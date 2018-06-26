#!/usr/bin/python

"""
common_autoqueue_ut contains unit tests for functions in the
common_autoqueue library
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
import autoshell.common as common
import autoshell.connectors.cli as cli

log = logging.getLogger("shared")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def test_parse_hosts(args):
    test = common.parse_addresses(args.addresses)
    log.info("Result:\n%s" % json.dumps(test, indent=4))


def test_hosts_class():
    addresses = [input("Enter address expression: ")]
    credentials = common.credentials.parse_credentials(None)
    hosts_instance = common.hosts.hosts_class(credentials,
                                              {"cli": cli})
    hosts_instance.load(addresses)
    hosts_instance.disconnect_all()



def run_tests(args):
    if args.addresses:
        test_parse_hosts(args)
    if args.test_hosts_class:
        test_hosts_class()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
                        '-a', "--address",
                        help="""Address Expressions""",
                        metavar='ADDRESS_EXPRESSION',
                        dest="addresses",
                        action='append')
    parser.add_argument(
                        '-t', "--test_hosts_class",
                        help="Run test_hosts_class",
                        dest="test_hosts_class",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
