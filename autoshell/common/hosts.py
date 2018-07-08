#!/usr/bin/python

"""
The common.hosts library contains classes and functions used for connecting
to remote hosts using connectors. The job of common.hosts is to manage the
use of credentials against hosts, oversee the autothreads used to connect
to the hosts, and gracefully disconnect from the hosts when instructed.
"""


# Built-In Libraries
import re
import json
import logging

# Autoshell Libraries
from . import autoqueue
from . import expressions


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


class connection_class:
    """
    common.hosts.connection_class is a simple namespace object used to hold
    values for an individual connection to a host using a specific connector.
    """
    def __init__(self, address, host, port=None, con_type=None):
        self.address = address  # DNS or IP Address string or list
        self.host = host  # Parent host_class object
        self.port = port  # TCP port number
        self.con_type = con_type  # Connector type (ie: "cli")
        self.connected = False  # Are we currently connected?
        self.failed = False  # Did the connection fail to establish?
        self.idle = False  # Flag used to indicate host is not ready for use
        self.connection = None  # ?????


class host_class:
    """
    common.hosts.host_class is used to store values for all connections to a
    specific host.
    """
    def __init__(self, address, port=None, typ=None):
        self.address = address  # DNS or IP Address string or list
        self.port = port  # TCP port number
        self.type = typ  # Device type string (ie: "linux")
        self.connections = {}  # Dict of connections keyed by connector name
        self.hostname = None  # Remote host discovered hostname
        self.info = {}  # Information dict which can be dumped to JSON

    def update_info(self):
        """
        common.hosts.host_class.update_info is used to update the .info
        dict using attributes before .info is used to dump info about the
        host.
        """
        self.info.update({
            "address": self.address,
            "port": self.port,
            "type": self.type,
            "hostname": self.hostname
        })


class hosts_class:
    """
    common.hosts.hosts_class is used as the single storage/management object
    for all the hosts in the runtime. The instantiation of hosts_class is
    passed to modules by AutoShell and can be used to find connected hosts
    and communicate with them.
    """
    def __init__(self, credentials, connectors):
        self.credentials = credentials  # List of credential dicts
        self.connectors = connectors  # List of connector libraries
        # List of DNS names or IP addresses which we have tried to connect
        #  to. Checked by add_host() to make sure we don't make duplicate
        #  connections.
        self.attempts = []
        # Dict of each connectors queue, keyed by the connector name
        self.queues = {}
        # Equivalent to self.queues, but for disconnecting from hosts
        self.disconnect_queues = {}
        self.hosts = []  # List of host_class instances
        # Storage for disconnect threads to drop completed items
        self.disconnected_hosts = []
        for con in self.connectors:
            # Fire up the autoqueue instance for each connector. Threads
            #  will remain idle until we load addresses into the queues
            #  using add_host() or load().
            self.queues.update({
                con: autoqueue.autoqueue(10,
                                         self.connectors[con].connect,
                                         (self.credentials, self.hosts))})

    def load(self, address_args):
        """
        common.hosts.load runs the user-provided address entries (from the
        arg parser) through the expression parser to pull out the defined
        hosts. It then loads all those hosts into the connector queues using
        add_host().
        """
        # Parse input addresses as expressions
        address_dicts = _add_hosts_exp(address_args)
        # Load each address into connector queues
        for address_dict in address_dicts:
            self.add_host(address_dict)
        # Call the autoqueue blocker for each of the connectors to hang the
        #  main thread until all connection attempts complete.
        for con in self.connectors:
            self.queues[con].block(kill=False)

    def add_host(self, address_dict):
        """
        common.hosts.add_host uses an address dict to instantiate a host_class
        instance, fills it with connection_class instanaces for each
        connector, and loads each connection_class instanace into the
        connector autoqueues so the connection attempts can be made by the
        threads using the connector's functions.
        """
        # If we have added a connection to this host already
        if address_dict in self.attempts:
            log.debug(
                "common.hosts.add_host: Host (%s) is a duplicate. Skipping" %
                address_dict["address"])
            # Don't add it again as it is a duplicate
            return None
        # Otherwise, record that we are adding it now
        self.attempts.append(address_dict)
        # Instantiate the host
        new_host = host_class(
            address_dict["address"],
            port=address_dict["port"],
            typ=address_dict["type"]
        )
        # And add a connection object for each connector
        for con in self.connectors:
            new_con = connection_class(
                address_dict["address"],
                host=new_host,
                port=address_dict["port"],
                con_type=con
            )
            # Add the connection to host's connections dict
            new_host.connections.update({con: new_con})
            # Add the connection_class instance to the proper connector queue
            self.queues[con].put(new_con)
        return new_host

    def disconnect_all(self):
        """
        common.hosts.disconnect_all gets called externally once all modules
        have completed their work and we are ready to gracefully disconnect
        from all the hosts and complete the program.
        """
        log.info("common.hosts.disconnect_all: Disconnecting all hosts")
        # Fire up the disconnect autoqueue instances and drop them into
        #  the self.disconnect_queues dict. The disconnect() functions should
        #  return disconnected hosts into the self.disconnected_hosts list.
        for con in self.connectors:
            self.disconnect_queues.update({
                con: autoqueue.autoqueue(10,
                                         self.connectors[con].disconnect,
                                         (self.disconnected_hosts, ))})
        # Drop each connector-specific connection_class instance into
        #  its appropriate disconnect_queues to be processed by the
        #  connector's disconnect() function.
        for queue in self.disconnect_queues:
            for host in self.hosts:
                self.disconnect_queues[queue].put(
                    host.connections[queue]
                )
        # Call each disconnect_queues (autoqueue) blocker to block the main
        #  thread until all connections for all hosts have gracefully
        #  disconnected.
        for queue in self.disconnect_queues:
            self.disconnect_queues[queue].block()


def _add_hosts_exp(inputs):
    """
    common.hosts._add_hosts_exp runs the address inputs through
    common.expressions and directs each response through the appropriate
    processing function
    """
    result = []
    # Process address entries using common.expressions
    host_data = expressions.parse_expression(inputs, ["-", ":", "@"])
    # Process each returned expression item as a file or string
    for response in host_data:
        if response["type"] == "string":
            result.append(_process_string_exps(response["value"]))
        if response["type"] == "file":
            for cred in _process_file_exps(response["value"]):
                result.append(cred)
    return result


def _process_file_exps(file_data):
    """
    common.hosts._process_file_exps accepts pre-parsed file data from
    the common.expressions library and searches them for host information.
    """
    def _normalize(host_dict):
        """
        common.hosts._process_file_exps._normalize normalizes every processed
        file entry to make sure each returned address dict has the same keys
        """
        # Entries without an address key are invalid
        if "address" not in host_dict:
            return None
        # If it has an address key, then set the key/vals and search for the
        #  other interesting keys, seting them if possible.
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
    # If an entry is a flat dictionary, then check for interesting values
    if type(file_data) == dict:
        norm_host = _normalize(file_data)
        if norm_host:
            result.append(norm_host)
    # If an entry is a list, then check each entry for interesting values
    elif type(file_data) == list:
        for entry in file_data:
            norm_host = _normalize(entry)
            if norm_host:
                result.append(norm_host)
    return result


def _process_string_exps(str_list):
    """
    common.hosts._process_string_exps accepts pre-parsed string data
    from the common.expressions library and pulls address, tcp port, and type
    information from the list of lists based on position.
    """
    if len(str_list) == 1:
        # If there is only one entry in the expression parsed by
        #  common.expressions, then there was no type defined.
        htype = None
    else:
        # Otherwise, the type will be the first entry in the second list
        htype = str_list[1][0]
    # If the first list has only one entry
    if len(str_list[0]) == 1:
        # Then assume it contains the address and no port was defined
        return {
            "address": str_list[0][0],
            "port": None,
            "type": htype,
        }
    # If the first list has more than one entry
    elif len(str_list[0]) > 1:
        # Then assume the first entry is the address and the second entry
        #  is the tcp port.
        return {
            "address": str_list[0][0],
            "port": str_list[0][1],
            "type": htype,
        }
