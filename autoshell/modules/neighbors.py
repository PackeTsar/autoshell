#!/usr/bin/python

"""
neighbors is a bundled AutoShell module which parses LLDP and CDP neighbor
information from hosts and adds that normalized information into .info.
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


# Instantiate an ad-hoc namespace object we will use to store state info
#  during load(). We then pick up that state info when we are run()
options = type('crawl_options', (), {})()


# <module_name>.run is a *REQUIRED* reserved name which is called by
#  the AutoShell core system once during its main run through the modules,
#  after it has finished connecting to all the hosts.
def run(ball):
    log.debug("neighbors.run: Pulling LLDP/CDP neighbors")
    queue = autoshell.common.autoqueue.autoqueue(10, worker, (ball, ))
    options.queue = queue
    for host in ball.hosts.hosts:
        queue.put(host)
    queue.block()
    log.debug("neighbors.run:\
 Complete. Returning control to the AutoShell core")


def worker(parent, host, ball):
    """
    neighbors.worker is the worker function for for the neighbors module.
    The process followed is:
        - Receives common.hosts.host_class instances from the queue
        - Look up the host neighbor handler from common.neighbors.HANDLER_MAP
        - Uses the crawl handler to pull LLDP/CDP neighbor data
        - Filters the neighbors using the crawl filters
        - Adds anything matching the filter back into
            the queue for recursion
        - Returns control to the supervisor function, awaiting a new
            host_object instances
    """
    ############################################################
    # Check host validity
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
        #  to use. Discard and do not pull neighbor data from it.
        log.warning("neighbors.worker:\
 Host (%s) has no type. Discarding" % host.address)
        return None
    ############################################################
    # Find handler set for hosts type
    ############################################################
    # Initialize as None. Will get replaced if we find a matching handler set
    handler_dict = None
    for handler_set in autoshell.common.neighbors.HANDLER_MAP:
        # Search through all of the handler sets and try to match its regular
        #  expressions against the host type. If we get a match, overwrite
        #  the handler_dict and break the for loop.
        for typ in handler_set["types"]:
            if re.findall(typ, host.type):
                handler_dict = handler_set
                log.debug("neighbors.worker:\
 Found handler for host (%s) matching type (%s)" % (host.hostname, typ))
                break
        if handler_dict:
            break
    # If we didn't find a matching handler set
    if not handler_dict:
        log.warning("neighbors.worker:\
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
                log.warning("neighbors.worker:\
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
            log.warning("neighbors.worker:\
 Host (%s) has no connection for handler type (%s). Discarding" %
                        (host.address, handler_type))
            return None
        ############################################################
        # Core neighbors functionality
        ############################################################
        log.debug("neighbors.worker:\
 Found connection on host (%s) for (%s) neighbor handler"
                  % (host.hostname, handler_type))
        # Pull the specific handler for this connection type
        handler = handler_dict["handlers"][handler_type]
        log.debug("neighbors.worker:\
 Pulling neighbors from host (%s) (%s) with (%s) neighbor handler"
                  % (host.hostname, host.address, handler_type))
        # Initialize .info with empty neighbor data to prep for real data
        host.info.update({"neighbors": []})
        # Pass connection and options to handler to get neighbor data
        neighbor_dict = handler(host.connections[handler_type],
                                True, True)
        log.debug("neighbors.worker: Neighbors on (%s) (%s):\n%s"
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
