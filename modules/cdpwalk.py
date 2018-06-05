#!/usr/bin/python

# Built-In Libraries
import re
import os
import sys
import time
import json

# Autoshell Libraries
import cdp
import commons


class cdpwalk:
    def __init__(self, ball):
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

    def run(self, data_ball):
        global log
        global ball
        ball = data_ball
        log = ball.modlog
        self.filters = cdp.build_cdp_filters(ball.args.filter)
        log.debug("cdpwalk.run: Starting walk of CDP neighbors")
        self._walkqueue = commons.autoqueue(10, self.walk, None)
        for host in ball.hosts.hosts:
            if host.connected:
                self._walkqueue.put(host)
            else:
                log.debug(
                    "cdpwalk.run: Skipping host (%s) (%s) since not connected"
                    % (host.hostname, host.host))
        # Block until queue is empty and workers are idle
        self._walkqueue.block()

    def walk(self, parent, host):
        if host.idle and host.connected:
            log.debug("cdpwalk.walk: Walking host (%s) (%s)"
                      % (host.hostname, host.host))
            host.info.update({"cdp": []})
            cdpdata = host.send_command("show cdp neighbors detail")
            cdpdata = cdp.convert_cdp_output(cdpdata)
            log.debug("cdpwalk.walk:\
 CDP neighbors on (%s) (%s):\n%s"
                      % (host.hostname, host.host,
                         json.dumps(cdpdata, indent=4)))
            host.info.update({"cdp": cdpdata})
            for device in cdpdata:
                if cdp.filter_cdp_device(device,
                                         self.filters,
                                         ball.args.and_logic):
                    newhost = ball.hosts.add_host({
                        "host": device["ip"],
                        "device_type": cdp.guess_cdp_dev_type(device),
                    })
                    if newhost:
                        log.info("cdpwalk.walk:\
 Added new host (%s) (%s) found on (%s) (%s). Queueing for CDP walk"
                                 % (device["name"],
                                    device["ip"],
                                    host.hostname, host.host))
                        self._walkqueue.put(newhost)
        else:
            if host.failed:
                log.warning("cdpwalk.walk:\
 Host (%s) failed. Discarding" % host.host)
            else:
                self._walkqueue.put(host)
                time.sleep(0.1)
