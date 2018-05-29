#!/usr/bin/python

import re
import time
import json
import queue
import threading


class cdpwalk:
    def __init__(self, ball):
        self._walkqueue = queue.Queue(maxsize=0)
        self._thread_count = 10
        self._workers = []
        self.filters = []
        ball.modparser.add_argument(
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
        ball.modparser.add_argument(
                            '-a', "--and",
                            help="Change default filter OR logic to AND logic",
                            dest="and_logic",
                            action='store_true')

    def _block(self):  # Block until queue is empty and workers are idle
        log.debug("cdpwalk._block: Blocking until cdpwalk is finished")
        busy = True
        try:
            while busy:
                if self._walkqueue.empty():
                    busy = False
                    for worker in self._workers:
                        if not worker.idle:
                            busy = True
            log.info("cdpwalk._block: cdpwalk done. Killing threads...")
            for worker in self._workers:
                worker.terminate = True
        except KeyboardInterrupt:
            log.warning("cdpwalk._block: Interrupted. Killing threads...")

    def _build_filters(self, entries):
        log.debug("cdpwalk._build_filters:\
 Parsing filter expressions: %s" % entries)
        result = []
        if not entries:
            return result
        attribs = [
            "name",
            "ip",
            "platform",
            "localif",
            "remoteif",
            "vtpdomain",
            "nativevlan",
            "version"]
        for entry in entries:
            if ":" not in entry:
                log.warning("cdpwalk._build_filters:\
 Discarding filter expression (%s): No ':' found in expression" % entry)
            else:
                attrib = entry.split(":")[0]
                regex = entry.split(":")[1]
                if attrib not in attribs:
                    log.warning("cdpwalk._build_filters:\
 Discarding filter expression (%s): Illegal attribute. Allowed: (%s)"
                                % " ".join(attribs))
                else:
                    try:
                        re.compile(regex)
                        newfilter = {"attrib": attrib, "regex": regex}
                        log.debug("cdpwalk._build_filters:\
 Adding filter element to filter list: %s" % newfilter)
                        result.append(newfilter)
                    except Exception as e:
                        log.warning("cdpwalk._build_filters:\
 Discarding filter expression (%s): REGEX Error: %s"
                                    % str(e))
        return result

    def run(self, data_ball):
        global log
        global ball
        ball = data_ball
        log = ball.modlog
        filters = self._build_filters(ball.args.filter)
        log.debug("cdpwalk.run: Starting walk of CDP neighbors")
        for i in range(self._thread_count):
            self._workers.append(self.worker_class(self._walkqueue, filters))
        for host in ball.hosts.hosts:
            if host.connected:
                self._walkqueue.put(host)
            else:
                log.debug(
                    "cdpwalk.run: Skipping host (%s) (%s) since not connected"
                    % (host.hostname, host.host))
        self._block()  # Block until queue is empty and workers are idle

    class worker_class:
        def __init__(self, walkqueue, filters):
            self.idle = True
            self.terminate = False
            self._walkqueue = walkqueue
            self._filters = filters
            self._cdpattribs = [
                {
                    "attrib": "name",
                    "clean": [],
                    "match": [
                        "Device ID: ",
                        "Device ID:"
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "ip",
                    "clean": [],
                    "match": [
                        "IP address: ",
                        "IP address:",
                        "IPv4 Address: ",
                        "IPv4 Address:"
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "platform",
                    "clean": [
                        "cisco ",
                        "Cisco "
                        ],
                    "match": [
                        "Platform: ",
                        "Platform:"
                        ],
                    "delimiter": ",\n"
                },
                {
                    "attrib": "localif",
                    "clean": [],
                    "match": [
                        "Interface: ",
                        "Interface:"
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "remoteif",
                    "clean": [
                        "Port ID (outgoing port): "
                        ],
                    "match": [
                        "Port ID \\(outgoing port\\): "
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "vtpdomain",
                    "clean": [
                        "'"
                        ],
                    "match": [
                        "VTP Management Domain: ",
                        "VTP Management Domain:"
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "nativevlan",
                    "clean": [],
                    "match": [
                        "Native VLAN: ",
                        "Native VLAN:"
                        ],
                    "delimiter": ",\\s"
                },
                {
                    "attrib": "version",
                    "clean": [],
                    "match": [
                        "Version :\n",
                        "Version:\n"
                        ],
                    "delimiter": "\n"
                }]
            self._dev_types = [
                {
                    "device_type": "cisco_ios",
                    "match": {
                        "attrib": "version",
                        "regex": "Cisco IOS Software"
                    }
                },
                {
                    "device_type": "cisco_nxos",
                    "match": {
                        "attrib": "version",
                        "regex": "NX-OS"
                    }
                },
                {
                    "device_type": "cisco_wlc",
                    "match": {
                        "attrib": "version",
                        "regex": "RTOS"
                    }
                }]
            self.thread = threading.Thread(target=self._check_queue)
            self.thread.daemon = True
            self.thread.start()

        def _guess_dev_type(self, cdp_device):
            log.debug("cdpwalk.worker_class._guess_dev_type:\
 Guessing device type on CDP device:\n%s"
                      % json.dumps(cdp_device, indent=4))
            for criteria in self._dev_types:
                if cdp_device[criteria["match"]["attrib"]]:  # If not None
                    if re.findall(criteria["match"]["regex"],
                                  cdp_device[criteria["match"]["attrib"]]):
                        log.debug("cdpwalk.worker_class._guess_dev_type:\
    Returning type (%s)" % criteria["device_type"])
                        return criteria["device_type"]
            log.debug("cdpwalk.worker_class._guess_dev_type:\
 Returning default type (cisco_ios)")
            return "cisco_ios"

        def _check_queue(self):
            log.debug(
                "cdpwalk.worker_class._check_queue: cdpwalk worker started")
            while not self.terminate:
                try:
                    host = self._walkqueue.get_nowait()
                    self.idle = False
                    self._walk(host)
                    self._walkqueue.task_done()
                    self.idle = True
                except queue.Empty:
                    time.sleep(0.01)

        def _walk(self, host):
            if host.idle and host.connected:
                log.debug("cdpwalk.worker_class._walk: Walking host (%s) (%s)"
                          % (host.hostname, host.host))
                host.info.update({"cdp": []})
                cdpdata = host.send_command("show cdp neighbors detail")
                cdpdata = self._convertcdp(cdpdata)
                log.debug("cdpwalk.worker_class._walk:\
 CDP neighbors on (%s) (%s):\n%s"
                          % (host.hostname, host.host,
                             json.dumps(cdpdata, indent=4)))
                host.info.update({"cdp": cdpdata})
                for device in cdpdata:
                    if self._filter_device(device):
                        newhost = ball.hosts.add_host({
                            "host": device["ip"],
                            "device_type": self._guess_dev_type(device),
                        })
                        if newhost:
                            log.info("cdpwalk.worker_class._walk:\
 Added new host (%s) (%s) found on (%s) (%s). Waiting for it to connect"
                                     % (device["name"],
                                        device["ip"],
                                        host.hostname, host.host))
                            # while not newhost.idle:
                            #     # time.sleep(0.01)
                            #     print("Waiting: %s" % newhost.host)
                            #     time.sleep(5)
                            log.info("cdpwalk.worker_class._walk:\
 (%s) (%s) Connected. Queueing host for CDP walk"
                                     % (newhost.hostname, device["ip"]))
                            self._walkqueue.put(newhost)
            else:
                if host.failed:
                    log.warning("cdpwalk.worker_class._walk:\
 Host (%s) failed. Discarding" % host.host)
                else:
                    self._walkqueue.put(host)
                    # print("Putting: %s idle:%s connected:%s"
                    #      % (host.host, host.idle, host.connected))
                    time.sleep(0.1)

        def _convertcdp(self, shcdpneidet):
            ###############
            ###############
            result = []
            delineator = shcdpneidet.split(
                "\n")[0]  # Set delineator as the first line
            if not delineator:
                delineator = shcdpneidet.split(
                    "\n")[1]  # Set delineator as the first line
            deviceblocks = shcdpneidet.split(
                delineator)  # Split on the delineator
            devicelines = []  # List of lists of device lines
            # For each block of text descrbng a device
            for block in deviceblocks:
                if block != "":
                    devlines = block.split("\n")
                    result.append(self._pulldevattbs(block))
            return result

        def _pulldevattbs(self, devlines):
            data = {}
            for attrib in self._cdpattribs:
                # for line in devlines:
                for match in attrib["match"]:
                    regex = "%s[^%s]*" % (match, attrib["delimiter"])
                    search = re.findall(regex, devlines)
                    if len(search) > 0:
                        matched = search[0].replace(match, "")
                        for rm in attrib["clean"]:
                            matched = matched.replace(rm, "")
                        data.update({attrib["attrib"]: matched})
                        break
                    if attrib["attrib"] not in data:  # No match was made
                        data.update({attrib["attrib"]: None})
            return data

        def _filter_device(self, cdpdevice):
            log.debug(
                "cdpwalk._filter_device: Filtering device (%s) with IP (%s)"
                % (cdpdevice["name"], cdpdevice["ip"]))
            if not self._filters:  # If a filter is not set
                log.debug(
                    "cdpwalk._filter_device: No filter set. Returning True")
                return True  # Don't filter the device
            if ball.args.and_logic:  # If logic is AND
                for flter in self._filters:
                    log.debug(
                        "cdpwalk._filter_device: Processing Filter (%s)"
                        % flter)
                    if cdpdevice[flter["attrib"]]:  # If there is a value there
                        findings = re.findall(
                            flter["regex"],
                            cdpdevice[flter["attrib"]])
                        log.debug(
                            "cdpwalk._filter_device:\
 Regex search returned: %s" % str(findings))
                        if not findings:
                            log.debug("cdpwalk._filter_device:\
 Returning False")
                            return False
                log.debug("cdpwalk._filter_device: Returning True")
                return True
            else:  # if logic is OR
                for flter in self._filters:
                    log.debug(
                        "cdpwalk._filter_device: Processing Filter (%s)"
                        % flter)
                    if cdpdevice[flter["attrib"]]:  # If there is a value there
                        findings = re.findall(
                            flter["regex"],
                            cdpdevice[flter["attrib"]])
                        log.debug(
                            "cdpwalk._filter_device: Regex search returned: %s"
                            % str(findings))
                        if findings:
                            log.debug("cdpwalk._filter_device: Returning True")
                            return True
                log.debug("cdpwalk._filter_device: Returning False")
                return False
