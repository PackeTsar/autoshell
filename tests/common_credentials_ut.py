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
#from common_credentials import parse_credentials
from autoshell.common.credentials import parse_credentials

log = logging.getLogger("shared")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def test_parse_credentials(args):
    test = parse_credentials(args.creds)
    log.info("Result:\n%s" % json.dumps(test, indent=4))


def run_tests(args):
    test_parse_credentials(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
                        '-c', "--creds",
                        help="""Credentials (string or file)
    Examples:
        '-c admin:password123'
        '-c admin:password123:enablepass123'
        '-c admin:password123:enablepass@cisco_ios'
        '-c ;$--admin;password123;enablepass$cisco_ios'
        '-c credfile.json'
        '-c credfile.yml'""",
                        metavar='CRED_STRING/FILE',
                        dest="creds",
                        action='append')
    args = parser.parse_args()
    run_tests(args)
