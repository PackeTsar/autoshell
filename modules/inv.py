#!/usr/bin/python

import re
import json
import shlex
import threading


class inv:
    def __init__(self, parser):
        self._threads = []
        self._invattribs = [
             {
                 "attrib": "name",
                 "clean": [],
                 "match": "NAME:"
             },
             {
                 "attrib": "description",
                 "clean": [],
                 "match": "DESCR:"
             },
             {
                 "attrib": "part",
                 "clean": [],
                 "match": "PID:"
             },
             {
                 "attrib": "version",
                 "clean": [],
                 "match": "VID:"
             },
             {
                 "attrib": "serial",
                 "clean": [],
                 "match": "SN:"
             }]
        self._attrib_matches = [each["match"] for each in self._invattribs]

    def run(self, input_ball):
        global ball
        global log
        ball = input_ball
        log = ball.modlog
        log.info("inv.run: Starting inventory of hosts")
        for host in ball.hosts.hosts:
            thread = threading.Thread(target=self._get_inv, args=(host,))
            thread.daemon = True
            self._threads.append(thread)
            thread.start()
        for thread in self._threads:
            thread.join()
        log.info("inv.run: Host inventory complete!")

    def _get_inv(self, host):
        if host.idle and host.connected:
            log.debug("inv._get_inv: Getting inventory of (%s) (%s)"
                      % (host.host, host.hostname))
            invdata = host.send_command("show inventory")
            invdata = self._convertinv(invdata)
            log.debug("inv._get_inv: Host (%s) (%s) inventory:\n%s"
                      % (host.host, host.hostname,
                         json.dumps(invdata, indent=4)))
            host.info.update({"inv": invdata})

    def _convertinv(self, showinv):
        result = []
        lines = showinv.split("\n\n")
        for line in lines:
            if line != "":
                item = {}
                line = line.replace("\n", " ")
                line = line.replace(",", " ")
                words = shlex.split(line)
                for attrib in self._invattribs:
                    index = 0
                    value = None
                    for word in words:
                        if word == attrib["match"]:
                            if index+1 >= len(words):  # Last item empty
                                item.update({attrib["attrib"]: None})
                            elif words[index+1] in self._attrib_matches:
                                item.update({attrib["attrib"]: None})
                            else:
                                item.update({attrib["attrib"]: words[index+1]})
                            break
                        index += 1
                result.append(item)
        return result
