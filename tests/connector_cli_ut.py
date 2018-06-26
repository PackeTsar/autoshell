#!/usr/bin/python

"""
connector_cli_ut
"""


# Built-In Libraries
import os
import sys
import json
import logging
import argparse
from builtins import input

# Autoshell Libraries
for each in os.walk(os.path.pardir):
    sys.path.append(each[0])
import autoshell.connectors.cli as cli
import autoshell.common as common

log = logging.getLogger("shared")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


creds = [
    {
        "username": "admin3",
        "secret": "password3",
        "password": "password3",
        "type": "unknown"
    },
    {
        "username": "admin2",
        "secret": "password2",
        "password": "password2",
        "type": None
    },
    {
        "username": "admin1",
        "secret": "password1",
        "password": "password1",
        "type": "cisco_ios"
    }
]


def test_order_credentials():
    import netmiko
    pref_types = ["cisco_ios"] + netmiko.platforms
    result = cli._order_credentials(creds, pref_types)
    log.info("Result:\n%s" % json.dumps(result, indent=4))


def test_assemble_credential():
    address = input("Enter address: ")
    credentials = common.credentials.parse_credentials(None)
    host_instance = common.hosts.host_class(address)
    con_instance = common.hosts.connection_class(address, host_instance)
    credential = cli._assemble_credential(con_instance,
                                          credentials[0])


def test_connect():
    address = input("Enter address: ")
    credentials = common.credentials.parse_credentials(None)
    host_instance = common.hosts.host_class(address)
    con_instance = common.hosts.connection_class(address, host_instance)
    credential = cli._assemble_credential(con_instance,
                                          credentials[0])
    cli._execute(con_instance, credential)


def test_cli():
    address = input("Enter address: ")
    credentials = common.credentials.parse_credentials(None)
    host_instance = common.hosts.host_class(address)
    con_instance = common.hosts.connection_class(address, host_instance)
    hostlist = []
    queue = common.autoqueue.autoqueue(
            thread_count=10,
            worker_func=cli.connect,
            worker_args=(credentials, hostlist))
    queue.put(con_instance)
    queue.block()
    log.info("Result: %s" % hostlist)


def run_tests(args):
    if args.test_order_credentials:
        test_order_credentials()
    if args.test_assemble_credential:
        test_assemble_credential()
    if args.test_connect:
        test_connect()
    if args.test_cli:
        test_cli()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
                        '-o', "--test_order_credentials",
                        help="Run test_order_credentials",
                        dest="test_order_credentials",
                        action='store_true')
    parser.add_argument(
                        '-s', "--test_assemble_credential",
                        help="Run test_assemble_credential",
                        dest="test_assemble_credential",
                        action='store_true')
    parser.add_argument(
                        '-n', "--test_connect",
                        help="Run test_connect",
                        dest="test_connect",
                        action='store_true')
    parser.add_argument(
                        '-x', "--test_cli",
                        help="Run test_cli",
                        dest="test_cli",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
