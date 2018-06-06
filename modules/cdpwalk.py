#!/usr/bin/python

"""
cdpwalk is a bundled AutoShell module which uses output from the
"show cdp neighbors detail" command to walk a network, dynamically add CDP
neighbors into the hosts, log into those CDP devices, and recurse over them
until no more devices can be added. cdpwalk also adds each device's CDP data
into host.info so it can be dumped and parsed.

cdpwalk has some custom command-line arguments it adds into argparser which
can be used to control its behavior and limit the scope of what it recurses
back into itself. These arguments are CDP filter expressions (see
cisco_cdp.build_cdp_filters) and the switches of the filter logic from OR
logic to AND logic when faced with multiple filter expressions.
"""

# FIXME Make CDP device value fields lists instead of strings
# FIXME Get rid of ball.modlog

# Built-In Libraries
import re
import os
import sys
import json
import logging

# Autoshell Libraries
import commons
import cisco_cdp


class cdpwalk:
    def __init__(self, ball):
        # Instantiate logging facility for modules
        self.log = logging.getLogger("modules")
        # Add custom arguments into the argparser in our own group
        modparser = ball.parser.add_argument_group(
            'CDPWalk Arguments',
            description="""CDP Walk - \
Walk CDP neighbors and attempt to log in to each one"""
            )
        modparser.add_argument(
                        '-f', "--filter",
                        help="""Regex filters for walking devices (optional)
    Attributes: platform,ip,name,localif,
                remoteif,vtpdomain,nativevlan
    Examples:
        Only Switches:    '-f platform:WS'
        Only 192.168 IPs: '-f ip:192.168.*'
        Switches OR IPs:  '-f platform:WS -f ip:192.168.*'""",
                        metavar='ATTRIB:REGEX',
                        dest="filter",
                        action="append")
        modparser.add_argument(
                            '-a', "--and",
                            help="Change default filter OR logic to AND logic",
                            dest="and_logic",
                            action='store_true')

    def run(self, ball):
        # .run is the module entry point called by
        # the main program in the main thread
        self.ball = ball  # Data ball passed from main program
        # CDP filter dictionaries
        self.filters = cisco_cdp.build_cdp_filters(self.ball.args.filter)
        self.log.debug("cdpwalk.run: Starting walk of CDP neighbors")
        # Autoqueue instance from commons
        self._walkqueue = commons.autoqueue(10, self.walk, None)
        # Load all connected host_object instances into the _walkqueue
        # self.walk will filter and recurse hosts back into the _walkqueue
        for host in self.ball.hosts.hosts:
            if host.connected:
                self._walkqueue.put(host)
            else:
                self.log.debug(
                    "cdpwalk.run: Skipping host (%s) (%s) since not connected"
                    % (host.hostname, host.host))
        # Block until queue is empty and workers are idle
        self._walkqueue.block()

    def walk(self, parent, host):
        """
        worker function for cdpwalk. Process followed is:
            - Receives host_object instances from the queue
            - Runs the "show cdp neighbors detail" command
            - Parses the output through cisco_cdp.convert_cdp_output function
            - Filters the CDP neighbors using cisco_cdp.filter_cdp_device
            - Adds anything matching the filter back into
                the queue for recursion
            - Returns control to the supervisor function, awaiting a new
                host_object instances
        """
        # Host not be idle if it is running another command already
        if host.idle and host.connected:
            self.log.debug("cdpwalk.walk: Walking host (%s) (%s)"
                           % (host.hostname, host.host))
            # Add empty data to avoid future parsing issues in case
            # we error out
            host.info.update({"cdp": []})
            # Send command to device
            cdpdata = host.send_command("show cdp neighbors detail")
            # Convert data to list of dictionaries
            cdpdata = cisco_cdp.convert_cdp_output(cdpdata)
            self.log.debug("cdpwalk.walk:\
 CDP neighbors on (%s) (%s):\n%s"
                           % (host.hostname, host.host,
                              json.dumps(cdpdata, indent=4)))
            # Add CDP data to the host.info store
            host.info.update({"cdp": cdpdata})
            # Start recursion process
            for device in cdpdata:
                # Returns True if device matches the filter(s)
                if cisco_cdp.filter_cdp_device(device,
                                               self.filters,
                                               self.ball.args.and_logic):
                    # Add a host using the hosts_class instance
                    newhost = self.ball.hosts.add_host({
                        "host": device["ip"],
                        "device_type": cisco_cdp.guess_cdp_dev_type(device),
                    })
                    # May have returned None if host is a duplicate
                    if newhost:
                        self.log.info("cdpwalk.walk:\
 Added new host (%s) (%s) found on (%s) (%s). Queueing for CDP walk"
                                      % (device["name"],
                                         device["ip"],
                                         host.hostname, host.host))
                        # Add to queue to be walked if it connects OK
                        self._walkqueue.put(newhost)
        else:
            if host.failed:  # If it failed to connect
                # Do not requeue it
                self.log.warning("cdpwalk.walk:\
 Host (%s) failed. Discarding" % host.host)
            else:
                # Otherwise add it back to the end of the queue
                self._walkqueue.put(host)
