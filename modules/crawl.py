#!/usr/bin/python

"""
crawl is a bundled AutoShell module which uses LLDP and CDP neighbor
information to walk a network, dynamically add neighbors as new hosts, log
into those new hosts, and recurse over them until no more devices can be added.
crawl also adds each device's neighbor data into host.info so it can be dumped
and parsed.

crawl has some custom command-line arguments it adds into argparser which
can be used to control its behavior and limit the scope of what it recurses
back into itself
"""


# Built-In Libraries
import re
import os
import sys
import json
import logging

# Autoshell Libraries
import autoshell


log = logging.getLogger("modules")


def add_parser_options(parser):
    modparser = parser.add_argument_group(
        'Crawl Arguments',
        description="""\
Crawl LLDP/CDP neighbors and attempt to log in to each one"""
        )
    modparser.add_argument(
                    '-F', "--filter",
                    help="""Regex filters for crawling devices (optional)
Attributes: %s
Examples:
    Only Switches:    '-f platform:WS'
    Only 192.168 IPs: '-f addresses:192.168.*'
    Switches OR IPs:  '-f platform:WS -f addresses:192.168.*'""" %
                    ",".join(autoshell.common.neighbors.allowed_attributes),
                    metavar='ATTRIB:REGEX',
                    dest="filter",
                    action="append")
    modparser.add_argument(
                    '-M', "--max_hops",
                    help="Maximum hops from the seed device",
                    metavar='INTEGER',
                    dest="max_hops")
    modparser.add_argument(
                    '-CO', "--crawl_cdp_only",
                    help="Crawl CDP only and ignore LLDP",
                    dest="crawl_cdp_only",
                    action='store_true')
    modparser.add_argument(
                    '-LO', "--crawl_lldp_only",
                    help="Crawl LLDP only and ignore CDP",
                    dest="crawl_lldp_only",
                    action='store_true')


options = type('crawl_options', (), {})()


def load(ball):
    options.filters = autoshell.common.neighbors.build_neighbor_filters(
        ball.args.filter)
    options.max_hops = ball.args.max_hops
    options.crawl_cdp_only = ball.args.crawl_cdp_only
    options.crawl_lldp_only = ball.args.crawl_lldp_only
    if options.crawl_cdp_only and options.crawl_lldp_only:
        log.warning("crawl.load:\
 (crawl_cdp_only) and (crawl_lldp_only) are both enabled.\
 Crawling disabled. Neighbor data will still be collected")
    log.debug("crawl.load: Returning control back to main application")


def run(ball):
    log.debug("crawl.run: Starting crawl of LLDP/CDP neighbors")
    queue = autoshell.common.autoqueue.autoqueue(10, crawl, (ball, ))
    options.queue = queue
    for host in ball.hosts.hosts:
        queue.put(host)
    queue.block()


HANDLER_MAPS = [
    {
        "handlers": {
           "cli": autoshell.cisco.neighbors.handlers.cisco_ios_neighbor_handler
        },
        "types": [".*cisco.*"]
    }
]


def crawl(parent, host, ball):
    """
    worker function for crawl. Process followed is:
        - Receives connection_class instances from the queue
        - Look up the device crawl handler from XXXXXXXXXXX
        - Uses the crawl handler to pull LLDP/CDP neighbor data
        - Filters the neighbors using the crawl filters
        - Adds anything matching the filter back into
            the queue for recursion
        - Returns control to the supervisor function, awaiting a new
            host_object instances
    """
    ############################################################

    ############################################################
    for connection in host.connections:
        if not host.connections[connection].idle:
            options.queue.put(host)  # Host still trying to connect
            return None
    if not host.type:
        log.warning("crawl.crawl:\
 Host (%s) has no type. Discarding" % host.address)
        return None
    handler_dict = None
    for each in HANDLER_MAPS:
        for typ in each["types"]:
            if re.findall(typ, host.type):
                handler_dict = each
                log.debug("crawl.crawl:\
 Found handler for host (%s) matching type (%s)" % (host.hostname, typ))
                break
    if not handler_dict:
        log.warning("crawl.crawl:\
 Could not find neighbor handler for host (%s)" % (host.hostname, ))
        return None
    ############################################################
    for handler_type in handler_dict["handlers"]:
        if not (host.connections[handler_type].idle
                and host.connections[handler_type].connected):
            if host.connections[handler_type].failed:
                log.warning("crawl.crawl:\
 Host (%s) failed. Discarding" % host.address)
                return None
            else:
                options.queue.put(host)
                return None
        ############################################################
        if handler_type not in host.connections:
            log.warning("crawl.crawl:\
 Host (%s) has no connection for handler type (%s). Discarding" %
                        (host.address, handler_type))
            return None
        ############################################################
        log.debug("crawl.crawl:\
 Found connection on host (%s) for (%s) neighbor handler"
                  % (host.hostname, handler_type))
        handler = handler_dict["handlers"][handler_type]
        if not host.type:
            log.warning("crawl.crawl:\
 Host (%s) has no type. Cancelling crawl of this host" % (host.hostname, ))
            return None
        log.debug("crawl.crawl:\
 Crawling host (%s) (%s) with (%s) neighbor handler"
                  % (host.hostname, host.address, handler_type))
        host.info.update({"neighbors": []})
        crawl_lldp = not options.crawl_cdp_only
        crawl_cdp = not options.crawl_lldp_only
        neighbor_dict = handler(host.connections[handler_type],
                                crawl_lldp, crawl_cdp)
        log.debug("crawl.crawl: Neighbors on (%s) (%s):\n%s"
                  % (host.hostname, host.address,
                     json.dumps(neighbor_dict, indent=4)))
        neighbors = {}
        for proto in neighbor_dict:
                neighbors.update({proto: []})
                for neighbor in neighbor_dict[proto]:
                    neighbors[proto].append(
                        autoshell.common.neighbors.neighbor_device(**neighbor)
                    )
        host.info.update({"neighbors": neighbor_dict})
        newhost_dicts = []
        for proto in neighbors:
            for neighbor_instance in neighbors[proto]:
                if autoshell.common.neighbors.filter_neighbor_device(
                        neighbor_instance, options.filters):
                    if neighbor_instance.addresses.Value:
                        newhost_dict = {
                            "address": neighbor_instance.addresses.Value,
                            "port": None,
                            "type": None
                        }
                        newhost = ball.hosts.add_host(newhost_dict)
                        if newhost:
                            log.info("crawl.crawl:\
 Added new host (%s) (%s) found on (%s) (%s). Queueing for neighbor walk"
                                     % (neighbor_instance.sysname.Value,
                                        neighbor_instance.addresses.Value,
                                        host.hostname, host.address))
                            options.queue.put(newhost)
