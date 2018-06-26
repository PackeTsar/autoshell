#!/usr/bin/python

"""
common_hosts
"""


# Built-In Libraries
import re
import json
import logging

# Autoshell Libraries
from . import autoqueue
from . import expressions


log = logging.getLogger("shared")


class connection_class:
    def __init__(self, address, host, port=None, con_type=None):
        self.address = address
        self.host = host
        self.port = port
        self.con_type = con_type
        self.connected = False
        self.failed = False
        self.idle = False
        self.connection = None


class host_class:
    def __init__(self, address, port=None, typ=None):
        self.address = address
        self.port = port
        self.type = typ
        self.connections = {}
        self.hostname = None
        self.info = {}

    def update_info(self):
        self.info.update({
            "address": self.address,
            "port": self.port,
            "type": self.type,
            "hostname": self.hostname
        })


class hosts_class:
    def __init__(self, credentials, connectors):
        self.credentials = credentials
        self.connectors = connectors
        self.attempts = []
        self.queues = {}
        self.disconnect_queues = {}
        self.hosts = []
        self.disconnected_hosts = []
        for con in self.connectors:
            self.queues.update({
                con: autoqueue.autoqueue(10,
                                         self.connectors[con].connect,
                                         (self.credentials, self.hosts))})

    def load(self, address_args):
        address_dicts = parse_addresses(address_args)
        for address_dict in address_dicts:
            self.add_host(address_dict)
        for con in self.connectors:
            self.queues[con].block(kill=False)

    def add_host(self, address_dict):
        if address_dict in self.attempts:
            log.debug(
                "hosts_class.add_host: Host (%s) is a duplicate. Skipping" %
                address_dict["address"])
            return None
        self.attempts.append(address_dict)
        new_host = host_class(
            address_dict["address"],
            port=address_dict["port"],
            typ=address_dict["type"]
        )
        for con in self.connectors:
            new_con = connection_class(
                address_dict["address"],
                host=new_host,
                port=address_dict["port"],
                con_type=con
            )
            new_host.connections.update({con: new_con})
            self.queues[con].put(new_con)
        return new_host

    def disconnect_all(self):
        log.info("hosts_class.disconnect_all: Disconnecting all hosts")
        for con in self.connectors:
            self.disconnect_queues.update({
                con: autoqueue.autoqueue(10,
                                         self.connectors[con].disconnect,
                                         (self.disconnected_hosts, ))})
        for queue in self.disconnect_queues:
            for host in self.hosts:
                self.disconnect_queues[queue].put(
                    host.connections[queue]
                )
        for queue in self.disconnect_queues:
            self.disconnect_queues[queue].block()


def parse_addresses(inputs):
    return _add_hosts_exp(inputs)


def _add_hosts_exp(inputs):
    result = []
    host_data = expressions.parse_expression(inputs, ["-", ":", "@"])
    for response in host_data:
        if response["type"] == "string":
            result.append(_process_string_exps(response["value"]))
        if response["type"] == "file":
            for cred in _process_file_exps(response["value"]):
                result.append(cred)
    return result


def _process_file_exps(file_data):
    def _normalize(host_dict):
        if "address" not in host_dict:
            return None
        else:
            address = host_dict["address"]
            port = None
            htype = None
        if "port" in host_dict:
            port = host_dict["port"]
        if "type" in host_dict:
            htype = host_dict["type"]
        return {
            "address": address,
            "port": port,
            "type": htype,
        }
    result = []
    if type(file_data) == dict:
        norm_host = _normalize(file_data)
        if norm_host:
            result.append(norm_host)
    elif type(file_data) == list:
        for entry in file_data:
            norm_host = _normalize(entry)
            if norm_host:
                result.append(norm_host)
    return result


def _process_string_exps(str_list):
    if len(str_list) == 1:
        htype = None
    else:
        htype = str_list[1][0]
    if len(str_list[0]) == 1:
        return {
            "address": str_list[0][0],
            "port": None,
            "type": htype,
        }
    elif len(str_list[0]) > 1:
        return {
            "address": str_list[0][0],
            "port": str_list[0][1],
            "type": htype,
        }


class hosts_class2:
    def __init__(self, hostargs):
        import commons
        log.debug(
            "hosts_class.__init__: Starting. Hosts Input:\n%s"
            % json.dumps(hostargs, indent=4))
        self._hostargs = hostargs
        self.init_hosts = self._parse_hosts(self._hostargs)
        self.connect_queue = commons.autoqueue(25, self.connect, None)
        self.attempts = []
        self.hosts = []
        for host in self.init_hosts:
            self.add_host(host)
        self.connect_queue.block(kill=False)

    def _parse_hosts(self, hosts):
        result = []
        for entry in hosts:
            log.debug("hosts_class._parse_hosts: Parsing host (%s)" % entry)
            if os.path.isfile(entry):
                log.debug(
                    "hosts_class._parse_hosts: Host (%s) appears to be a file"
                    % entry)
                f = open(entry, "r")
                log.debug("hosts_class._parse_hosts: File opened")
                data = f.read()
                f.close
                if "," in data:
                    log.debug(
                        "hosts_class._parse_hosts: Splitting on commas")
                    data = data.split(",")
                else:
                    log.debug(
                        "hosts_class._parse_hosts: Splitting on newlines")
                    data = data.split("\n")
                for each in data:
                    if each != "":
                        if "@" in each:
                            words = each.split("@")
                            newhost = {"host": words[0],
                                       "device_type": words[1]}
                        else:
                            newhost = {"host": each,
                                       "device_type": None}
                        if newhost not in result:
                            log.debug(
                                "hosts_class._parse_hosts: Adding host (%s)"
                                % newhost["host"])
                            result.append(newhost)
                        else:
                            log.warning(
                                "hosts_class._parse_hosts: Duplicate host (%s)"
                                % newhost["host"])
            else:
                log.debug(
                    "hosts_class._parse_hosts: \
Host (%s) is not a file. Parsing as a string"
                    % entry)
                if "@" in entry:
                    words = entry.split("@")
                    newhost = {"host": words[0],
                               "device_type": words[1]}
                else:
                    newhost = {"host": entry,
                               "device_type": None}
                if newhost not in result:
                    result.append(newhost)
                else:
                    log.warning(
                        "hosts_class._parse_hosts: Duplicate host (%s)"
                        % newhost["host"])
        log.debug("hosts_class._parse_hosts: Completed host list:\n%s"
                  % json.dumps(result, indent=4))
        return result

    def add_host(self, hostdict):
        if not hostdict["host"]:
            log.debug(
                "hosts_class.add_host: Host is None. Skipping")
            return None
        if hostdict["host"] in self.attempts:
            log.debug(
                "hosts_class.add_host: Host is a duplicate. Skipping")
            return None
        log.debug("hosts_class.add_host: Adding host (%s)" % hostdict["host"])
        self.attempts.append(hostdict["host"])
        host = host_object(hostdict)
        self.connect_queue.put(host)
        return host

    def disconnect_all(self):
        log.debug("hosts_class.disconnect_all: Disconnecting all hosts")
        threads = []
        for host in self.hosts:
            threads.append(host.disconnect())
        for thread in threads:
            thread.join()

    def active_hosts(self):
        result = []
        for host in self.hosts:
            if host.idle and host.connected:
                result.append(host)
            else:
                self.log.debug(
                    "hosts_class.active_hosts:\
 Skipping host (%s) (%s) since not connected" % (host.hostname, host.host))
        return result

    def connect(self, parent, hostobj):
        import netmiko
        log.info("hosts_class.connect: Connecting to IP (%s)"
                 % hostobj.host)
        for credential in ball.creds.creds:
            log.debug("hosts_class.connect: Assembling credential:\n%s"
                      % json.dumps(credential, indent=4))
            if hostobj.type:
                type = hostobj.type
            else:
                type = credential["device_type"]
            asmb_cred = {
                "ip": hostobj.host,
                "device_type": type,
                "username": credential["username"],
                "password": credential["password"],
                "secret": credential["secret"]
            }
            log.debug("hosts_class.connect: Trying assembled credential:\n%s"
                      % json.dumps(asmb_cred, indent=4))
            try:
                hostobj.device = netmiko.ConnectHandler(timeout=10,
                                                        **asmb_cred)
                hostobj.hostname = hostobj.device.find_prompt().replace("#",
                                                                        "")
                hostobj.hostname = hostobj.hostname.replace(">", "")
                log.info(
                    "host_object._connect: Connected to (%s) with IP (%s)"
                    % (hostobj.hostname, hostobj.host))
                hostobj.info.update({"credential": credential})
                hostobj.connected = True
                hostobj._update_info()
                hostobj.idle = True
                break
            except netmiko.ssh_exception.NetMikoTimeoutException:
                log.warning(
                    "host_object._connect: Device (%s) timed out. Discarding"
                    % hostobj.host)
                hostobj.idle = True
                hostobj.failed = True
                break
            except Exception as e:
                log.warning(
                    "host_object._connect: Device (%s) Connect Error: %s"
                    % (hostobj.host, str(e)))
                hostobj.idle = True
        if not hostobj.connected:
            hostobj.failed = True
        else:
            self.hosts.append(hostobj)
