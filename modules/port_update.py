#!/usr/bin/python

import re
import json
import shlex
import threading


class port_update:
    def __init__(self, ball):
        self.modparser = ball.parser.add_argument_group(
            'Port Update Arguments',
            description="""Port Update - \
Configure ports with certain criteria"""
            )
        self.modparser.add_argument(
                        '-P', "--port_config_file",
                        help="""JSON file with port configurations""",
                        metavar='PORT_CONFIG_FILE',
                        dest="port_config_file")
        self.modparser.add_argument(
                        '-C', "--cdp_filter",
                        help="""CDP attribute filter to use to find ports""",
                        metavar='FILTER_EXPRESSION',
                        dest="cdp_filter",
                        action="append")
        self.modparser.add_argument(
                        '-T', "--spark_token",
                        help="""Spark token string for updates""",
                        metavar='TOKEN',
                        dest="spark_token")
        self.modparser.add_argument(
                        '-R', "--spark_room_id",
                        help="""Spark room ID for updates""",
                        metavar='ROOM_ID',
                        dest="spark_room_id")

    def run(self, input_ball):
        global ball
        global log
        self._threads = []
        self._fixes = []
        ball = input_ball
        log = ball.modlog
        log.info("port_update.run: Starting port updates")
        f = open(ball.args.port_config_file, "r")
        port_configs = json.loads(f.read())
        f.close()
        for host in ball.hosts.hosts:
            thread = threading.Thread(target=self._update_ports, args=(
                host, port_configs))
            thread.daemon = True
            self._threads.append(thread)
            thread.start()
        for thread in self._threads:
            thread.join()
        log.info("port_update.run: Port updates done, checking for Spark!")
        self._update_spark(self._fixes)
        log.info("port_update.run: Port update complete!")

    def _update_spark(self, updates):
        if ball.args.spark_token and ball.args.spark_room_id:
            if updates:
                log.info("port_update._update_spark: \
Spark info present. Pushing report")
                from ciscosparkapi import CiscoSparkAPI
                message = "\n".join(updates)
                api = CiscoSparkAPI(access_token=ball.args.spark_token)
                api.messages.create(ball.args.spark_room_id, text=message)
                log.info("port_update._update_spark: \
Spark report sent!")
            else:
                log.info("port_update._update_spark: \
No updates exist to send to Spark.")
        else:
            log.info("port_update._update_spark: \
Spark info not present.")

    def _update_ports(self, host, port_configs):
        check_ports = []
        fix_ports = []
        if host.idle and host.connected:
            log.debug("inv._update_ports: Checking ports on (%s) (%s)"
                      % (host.host, host.hostname))
            for port in host.info["cdp"]:
                for filter in ball.args.cdp_filter:
                    attrib = filter.split(":")[0]
                    regex = filter.split(":")[1]
                    if attrib in port:
                        search = re.findall(regex, port[attrib])
                        if search:
                            check_ports.append(port["localif"])
            log.debug("inv._update_ports: \
Found Matching Ports on (%s) (%s):\n%s" %
                      (host.hostname, host.host, json.dumps(
                       check_ports, indent=4)))
            for port in check_ports:
                current_config = host.send_command(
                    "show run interface %s" % port)
                port_ok = False
                for template in port_configs:
                    if template in current_config:
                        port_ok = True
                if not port_ok:
                    fix_ports.append(port)
            for port in fix_ports:
                config = "default interface \
%s\ninterface %s\n%s\n shutdown\n no shutdown" % (
                          port, port, port_configs[1])
                log.info("inv._update_ports: \
Pushing config to (%s) (%s):\n%s" % (host.hostname, host.host,
                                     config))
                self._fixes.append("Reset %s:%s" % (host.hostname, port))
                host.device.config_mode()
                response = host.send_command(config)
                log.debug("inv._update_ports: \
Response from (%s) (%s):\n%s" % (host.hostname, host.host,
                                 response))
