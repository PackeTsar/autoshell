#!/usr/bin/python

"""
common_neighbors_ut contains unit tests for functions in the
common_neighbors library
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
import autoshell.common.neighbors as neigh

log = logging.getLogger("shared")
mlog = logging.getLogger("modules")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)
mlog.addHandler(consoleHandler)
mlog.setLevel(logging.DEBUG)


test_neighbor = {
        "sysname": [
            "CORE_SWITCH"
        ],
        "remoteif": [
            "REthernet0"
        ],
        "addresses": [
            "192.168.1.1"
        ],
        "localif": [
            "LEthernet0"
        ],
        "remoteifdesc": [
            "Super Important Interface"
        ],
        "sysdesc": [
            "Manufacturer's Name: Network Systems Inc"
        ],
        "sysid": [
            "00:00:00:00:00:00"
        ],
        "platform": [
            "WS-BIG-ASS-SWITCH-V01"
        ],
        "ttl": [
            "120"
        ],
        "syscap": [
            "B,T"
        ]
    }


def test_neighbor_device():
    neighbor = neigh.neighbor_device(**test_neighbor)
    log.info("Result:\n%s" % json.dumps(neighbor(), indent=4))


def test_build_neighbor_filters():
    test = neigh.build_neighbor_filters([input("Enter Filter Expression: ")])
    log.info("Result:\n%s" % json.dumps(test, indent=4))


def test_filter_neighbor_device(args):
    neighbor = neigh.neighbor_device(**test_neighbor)
    log.info("common_neighbors.test_filter_neighbor_device:\
 Neighbor Info:\n%s" % json.dumps(neighbor(), indent=4))
    filters = neigh.build_neighbor_filters(args.filter)
    neigh.filter_neighbor_device(neighbor, filters)


def run_tests(args):
    if args.test_neighbor_device:
        test_neighbor_device()
    if args.test_build_neighbor_filters:
        test_build_neighbor_filters()
    if args.filter:
        test_filter_neighbor_device(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-n', "--test_neighbor_device",
                        help="Run test_neighbor_device",
                        dest="test_neighbor_device",
                        action='store_true')
    parser.add_argument(
                        '-b', "--test_build_neighbor_filters",
                        help="Run test_build_neighbor_filters",
                        dest="test_build_neighbor_filters",
                        action='store_true')
    parser.add_argument(
                        '-f', "--filter",
                        help="Run test_filter_neighbor_device",
                        metavar='FILTER_EXPRESSION',
                        dest="filter",
                        action='append')
    args = parser.parse_args()
    run_tests(args)
