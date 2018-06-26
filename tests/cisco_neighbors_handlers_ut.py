#!/usr/bin/python

"""
cisco_neighbor_handlers_ut contains unit tests for functions in the
cisco_neighbor_handlers library
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
import autoshell.cisco.neighbors.handlers as handlers

log = logging.getLogger("modules")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def multilineinput(ending):
    result = ""
    done = False
    while not done:
        data = input()
        if data == ending:
            done = True
        else:
            result += data+"\n"
    return result


class fake_host:
    def send_command(self, command):
        log.info("test_cisco_ios_neighbor_handler:\
 Input '%s' output\
 ending with '^' on a line by itself" % command)
        return multilineinput("^")


def test_cisco_ios_neighbor_handler():
    host = fake_host()
    data = handlers.cisco_ios_neighbor_handler(host)
    log.info("Result:\n%s" % json.dumps(data, indent=4))


def run_tests(args):
    if args.test_cisco_ios_neighbor_handler:
        test_cisco_ios_neighbor_handler()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-c', "--test_cisco_ios_neighbor_handler",
                        help="Run test_cisco_ios_neighbor_handler",
                        dest="test_cisco_ios_neighbor_handler",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
