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
from autoshell.common.expressions import parse_expression

log = logging.getLogger("shared")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def test_expressions_class(args):
    test = parse_expression(args.expression, ["-", ":", "%"])
    log.info("Result:\n%s" % json.dumps(test, indent=4))


def run_tests(args):
    if args.expression:
        test_expressions_class(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-e', "--expression",
                        help="Run test_expressions_class",
                        metavar='EXPRESSION',
                        dest="expression",
                        action='append')
    args = parser.parse_args()
    run_tests(args)
