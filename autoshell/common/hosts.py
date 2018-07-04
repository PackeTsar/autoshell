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
                "common.hosts.add_host: Host (%s) is a duplicate. Skipping" %
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
        log.info("common.hosts.disconnect_all: Disconnecting all hosts")
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
