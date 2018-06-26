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
import common.autoqueue

log = logging.getLogger("shared")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def test_common_autoqueue():
    def test_worker(parent, input_data):
        import time
        log.info("common_autoqueue_ut.test_common_autoqueue:\
 Returning data: %s" % input_data)
        time.sleep(1)
    queue = common.autoqueue.autoqueue(
            thread_count=10,
            worker_func=test_worker,
            worker_args=None)
    for item in range(100):
        queue.put(item)
    queue.block()


def run_tests(args):
    if args.test_common_autoqueue:
        test_common_autoqueue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-a', "--test_common_autoqueue",
                        help="Run test_common_autoqueue",
                        dest="test_common_autoqueue",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
