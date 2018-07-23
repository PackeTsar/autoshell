#!/usr/bin/python

"""
cisco_neighbor_scrapers_ut contains unit tests for functions in the
cisco_neighbor_scrapers library
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
import autoshell.hp.neighbors.cli.scrapers as scrapers

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


def neighbor_test(func, message):
    log.info(message)
    data = multilineinput("^")
    result = func(data)
    log.info("Result:\n%s" % json.dumps(result, indent=4))



def run_tests(args):
    if args.test_cisco_ios_cdp_scraper:
        neighbor_test(scrapers.hp_cdp_scraper,
                      "test_cisco_ios_lldp_br_interpreter:\
 Input 'show cdp neighbors detail' output\
 ending with '^' on a line by itself")
    if args.test_cisco_ios_lldp_de_scraper:
        neighbor_test(scrapers.hp_lldp_de_scraper,
                      "test_cisco_ios_lldp_br_interpreter:\
 Input 'show lldp neighbors detail' output\
 ending with '^' on a line by itself")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-c', "--test_cisco_ios_cdp_scraper",
                        help="Run test_cisco_ios_cdp_scraper",
                        dest="test_cisco_ios_cdp_scraper",
                        action='store_true')
    parser.add_argument(
                        '-ld', "--test_cisco_ios_lldp_de_scraper",
                        help="Run test_cisco_ios_lldp_de_scraper",
                        dest="test_cisco_ios_lldp_de_scraper",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
