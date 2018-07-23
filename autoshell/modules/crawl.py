#!/usr/bin/python

"""
crawl is a bundled AutoShell module which uses LLDP and CDP neighbor
information to crawl a network, dynamically add neighbors as new hosts, log
into those new hosts, and recurse over them until no more hosts can be added.
crawl also adds each host's neighbor data into host.info so it can be dumped
and parsed.

crawl has some custom command-line arguments it adds into arg parser which
can be used to control its behavior and limit the scope of what it recurses
back into itself.
Crawl Arguments:
  Crawl LLDP/CDP neighbors and attempt to log in to each one
  -F ATTRIB:REGEX, --filter ATTRIB:REGEX
                Regex filters for crawling hosts (optional)
                Attributes: sysname,remoteif,addresses,localif,
                    remoteifdesc,sysdesc,sysid,platform,ttl,syscap
                Examples:
                    Only Switches:    '-f platform:WS'
                    Only 192.168 IPs: '-f addresses:192.168.*'
                    Switches OR IPs:  '-f platform:WS -f addresses:192.168.*'
  -M INTEGER, --max_hops INTEGER
                        Maximum hops from the seed host
  -CO, --crawl_cdp_only
                        Crawl CDP only and ignore LLDP
  -LO, --crawl_lldp_only
                        Crawl LLDP only and ignore CDP
"""


# Built-In Libraries
import re
import os
import sys
import json
import logging

# Autoshell Libraries
import autoshell


# log (shared) is used for logging inside of user-written modules
log = logging.getLogger("modules")


# <module_name>.add_parser_options is an *OPTIONAL* reserved name which is
#  called by the AutoShell core system when the module is initially loaded.
#  This allows external modules to add their own arguments to the core
#  arg parser.
def add_parser_options(parser):
    """
    crawl.add_parser_options adds all our crawl-specific arguments to our own
    argument group. It gets called immediately after the import of the module.
    """
    modparser = parser.add_argument_group(
        'Crawl Arguments',
        description="""\
Crawl LLDP/CDP neighbors and attempt to log in to each one"""
        )
    modparser.add_argument(
                    '-F', "--crawl_filter",
                    help="""Regex filters for crawling hosts (optional)
Attributes: %s
Examples:
    Only Switches:    '-f platform:WS'
    Only 192.168 IPs: '-f addresses:192.168.*'
    Switches OR IPs:  '-f platform:WS -f addresses:192.168.*'""" %
                    ",".join(autoshell.common.neighbors.allowed_attributes),
                    metavar='ATTRIB:REGEX',
                    dest="crawl_filter",
                    action="append")
    modparser.add_argument(
                    '-M', "--crawl_max_hops",
                    help="Maximum hops from the seed host",
                    metavar='INTEGER',
                    dest="crawl_max_hops")
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


# Instantiate an ad-hoc namespace object we will use to store state info
#  during load(). We then pick up that state info when we are run()
options = type('crawl_options', (), {})()


# <module_name>.load is an *OPTIONAL* reserved name which is called by
#  the AutoShell core system after all the command-line arguments have been
#  parsed by arg parser. This gives the module an opportunity to check all
#  user-inputs and throw errors before AutoShell continues on to connect to
#  the hosts.
def load(ball):
    """
    crawl.load processes all of the crawl-specific arguments from arg parser
    It uses the common.neighbors library to build the filters from standard
    expressions on the command-line.
    """
    log.debug("crawl.load: Processing user-inputs from the arg parser")
    options.filters = autoshell.common.neighbors.build_neighbor_filters(
        ball.args.crawl_filter)
    options.max_hops = ball.args.crawl_max_hops
    # Invert logic on user-input crawl switches
    options.crawl_lldp = not ball.args.crawl_cdp_only
    options.crawl_cdp = not ball.args.crawl_lldp_only
    if not (options.crawl_lldp and options.crawl_cdp):
        log.warning("crawl.load:\
 (crawl_cdp_only) and (crawl_lldp_only) are both enabled.\
 Crawling disabled. Neighbor data will still be collected")
    log.debug("crawl.load: Returning control back to main application")


# <module_name>.run is a *REQUIRED* reserved name which is called by
#  the AutoShell core system once during its main run through the modules,
#  after it has finished connecting to all the hosts.
def run(ball):
    log.debug("crawl.run: Starting crawl of LLDP/CDP neighbors")
    queue = autoshell.common.autoqueue.autoqueue(10, crawl, (ball, ))
    options.queue = queue
    for host in ball.hosts.hosts:
        queue.put(host)
    queue.block()
    log.debug("crawl.run: Complete. Returning control to the AutoShell core")


# crawl.HANDLER_MAPS is a mapping of host types to neighbor handlers. Each
#  handler is specific to a connection type (ie: "cli" or "netconf") and is
#  matched against the host type using a regular expression.
HANDLER_MAPS = [
    {
        "handlers": {
           "cli": autoshell.cisco.neighbors.handlers.cisco_ios_neighbor_handler
        },
        "types": [".*cisco.*"]
    },
    {
        "handlers": {
           "cli": autoshell.hp.neighbors.handlers.hp_neighbor_handler
        },
        "types": [".*hp.*"]
    }
]


def crawl(parent, host, ball):
    """
    crawl.crawl is the worker function for crawl. Process followed is:
        - Receives connection_class instances from the queue
        - Look up the host crawl handler from XXXXXXXXXXX
        - Uses the crawl handler to pull LLDP/CDP neighbor data
        - Filters the neighbors using the crawl filters
        - Adds anything matching the filter back into
            the queue for recursion
        - Returns control to the supervisor function, awaiting a new
            host_object instances
    """
    ############################################################
    # Check host validity and find its handler set
    ############################################################
    for connection in host.connections:
        # If any of the connections in the host are not idle
        if not host.connections[connection].idle:
            # Then the connections are still trying to be made. Drop them in
            #  the back of the queue and try them later.
            options.queue.put(host)
            return None
    if not host.type:
        # If the host does not have a type, then we don't know which handler
        #  to use. Discard and do not crawl it.
        log.warning("crawl.crawl:\
 Host (%s) has no type. Discarding" % host.address)
        return None
    # Initialize as None. Will get replaced if we find a matching handler set
    handler_dict = None
    for each in HANDLER_MAPS:
        # Search through all of the handler sets and try to match its regular
        #  expressions against the host type. If we get a match, overwrite
        #  the handler_dict and break the for loop.
        for typ in each["types"]:
            if re.findall(typ, host.type):
                handler_dict = each
                log.debug("crawl.crawl:\
 Found handler for host (%s) matching type (%s)" % (host.hostname, typ))
                break
    # If we didn't find a matching handler set
    if not handler_dict:
        log.warning("crawl.crawl:\
 Could not find neighbor handler for host (%s)" % (host.hostname, ))
        return None
    ############################################################
    # Find a connection for each handler and check connection validity
    ############################################################
    # BUG (multi-con): Any failed connection will fail the whole host. Need
    #  to allow some connections to be failed, since not all connection types
    #  will succeed
    # Iterate through each of the types and try to match against keyed
    #  connections in host.connections.
    for handler_type in handler_dict["handlers"]:
        # If the connection (which is a hosts.connection_class instance) is
        #  not connected and idle.
        if not (host.connections[handler_type].idle
                and host.connections[handler_type].connected):
            if host.connections[handler_type].failed:
                # And if it is also flagged as failed. Then discard it
                log.warning("crawl.crawl:\
 Host (%s) failed. Discarding" % host.address)
                return None
            else:
                # If it is not failed, then requeue it and return
                options.queue.put(host)
                return None
        ############################################################
        # BUG: Why are we checking if the host has the type here?????
        #  It would have already thrown an error above.
        if handler_type not in host.connections:
            log.warning("crawl.crawl:\
 Host (%s) has no connection for handler type (%s). Discarding" %
                        (host.address, handler_type))
            return None
        ############################################################
        # Core crawl functionality
        ############################################################
        log.debug("crawl.crawl:\
 Found connection on host (%s) for (%s) neighbor handler"
                  % (host.hostname, handler_type))
        # Pull the specific handler for this connection type
        handler = handler_dict["handlers"][handler_type]
        log.debug("crawl.crawl:\
 Crawling host (%s) (%s) with (%s) neighbor handler"
                  % (host.hostname, host.address, handler_type))
        # Initialize .info with empty neighbor data to prep for real data
        host.info.update({"neighbors": []})
        # Pass connection and options to handler to get neighbor data
        neighbor_dict = handler(host.connections[handler_type],
                                options.crawl_lldp, options.crawl_cdp)
        log.debug("crawl.crawl: Neighbors on (%s) (%s):\n%s"
                  % (host.hostname, host.address,
                     json.dumps(neighbor_dict, indent=4)))
        # Drop neighbor data into .info so it can be dumped to JSON
        host.info.update({"neighbors": neighbor_dict})
        # Format the returned neighbor_dict into a parsable dict which
        #  contains neighbor_device instances for each neighbor.
        neighbors = {}
        for proto in neighbor_dict:
                neighbors.update({proto: []})
                for neighbor in neighbor_dict[proto]:
                    # Append an instance of neighbor_device which gets used
                    #  by the filtering mechanism
                    neighbors[proto].append(
                        autoshell.common.neighbors.neighbor_device(**neighbor)
                    )
        # asdfasdfasdf
        for proto in neighbors:
            for neighbor_instance in neighbors[proto]:
                # Run neighbor_instance through the filter function (along)
                #  the filters we built during load() to see if we should
                #  crawl to this neighbor.
                if autoshell.common.neighbors.filter_neighbor_device(
                        neighbor_instance, options.filters):
                    # If the neighbor has address data for us to use to
                    #  connect.
                    if neighbor_instance.addresses.Value:
                        # Build a new host dict and hand it to hosts.add_host
                        #  which will attempt to connect to the host with
                        #  proper credentials and connectors.
                        newhost_dict = {
                            "address": neighbor_instance.addresses.Value,
                            "port": None,
                            "type": None
                        }
                        newhost = ball.hosts.add_host(newhost_dict)
                        # If add_host returned a host_class instance, then
                        #  queue it up to be walked after all connections are
                        #  made.
                        if newhost:
                            log.info("crawl.crawl:\
 Added new host (%s) (%s) found on (%s) (%s). Queueing for neighbor crawl"
                                     % (neighbor_instance.sysname.Value,
                                        neighbor_instance.addresses.Value,
                                        host.hostname, host.address))
                            options.queue.put(newhost)
