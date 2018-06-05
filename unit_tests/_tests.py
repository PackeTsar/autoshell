#!/usr/bin/python

# Built-In Libraries
import os
import sys
import json
import logging
import argparse

# Autoshell Libraries
for each in os.walk(os.path.pardir):
    sys.path.append(each[0])
import cdp
import commons

log = logging.getLogger("modules")
consoleHandler = logging.StreamHandler()
fmt = """\
%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"""
format = logging.Formatter(fmt)
consoleHandler.setFormatter(format)
log.addHandler(consoleHandler)
log.setLevel(logging.DEBUG)


def test_build_cdp_filters():
    tests = [
        ["WS-"],
        ["ip:192.168"],
        ["platform:WS-"],
        ["broken:WS-"],
        ["platform:AIR-", "ip:*.192.168.*"],
        ["platform:AIR-", "ip:.*192.168.*"]
    ]
    device = {
        "platform": "WS-C2960XR-48FPD-I",
        "remoteif": "TenGigabitEthernet1/0/1",
        "nativevlan": "1",
        "name": "CORE_SWITCH.domain.com",
        "version": "Some IOS Version",
        "localif": "TenGigabitEthernet1/0/9",
        "ip": "10.1.1.1",
        "vtpdomain": None
    }
    result = []
    for test in tests:
        result.append(cdp.build_cdp_filters(test))
    result = json.dumps(result, indent=4)
    log.info("_tests.test_cdp_filters: Returned %s\n" % result)


def test_filter_cdp_device():
    test_filters = [
        [
            {
                "regex": "WS-",
                "attrib": "platform"
            }
        ],
        [
            {
                "regex": "XXX",
                "attrib": "platform"
            }
        ],
        [
            {
                "regex": "WS-",
                "attrib": "platform"
            },
            {
                "regex": "1.1.1$",
                "attrib": "ip"
            },
        ],
        [
            {
                "regex": "VMware",
                "attrib": "platform"
            }
        ]
    ]
    devices = [
        {
            "platform": "WS-C2960XR-48FPD-I",
            "remoteif": "TenGigabitEthernet1/0/1",
            "nativevlan": "1",
            "name": "CORE_SWITCH_1.domain.com",
            "version": "Some IOS Version 1.2.3",
            "localif": "TenGigabitEthernet1/0/9",
            "ip": "10.1.1.1",
            "vtpdomain": None
        },
        {
            "platform": "WS-C2960XR-48FPD-I",
            "remoteif": "TenGigabitEthernet1/0/1",
            "nativevlan": "1",
            "name": "CORE_SWITCH_2.domain.com",
            "version": "Some IOS Version 1.2.4",
            "localif": "TenGigabitEthernet1/0/10",
            "ip": "10.1.1.2",
            "vtpdomain": None
        },
        {
            "platform": "AIR-CT3504-K9",
            "remoteif": "GigabitEthernet0/0/2",
            "nativevlan": None,
            "name": "WLC-Standby",
            "version": "RTOS Version: 8.5.103.0  Bootloader Version:",
            "localif": "GigabitEthernet1/0/44",
            "ip": "10.1.1.51",
            "vtpdomain": None
        },
        {
            "platform": "VMware ESX",
            "remoteif": "vmnic1",
            "nativevlan": None,
            "name": "ESX1.domain.com",
            "version": "Releasebuild-7388607",
            "localif": "GigabitEthernet1/0/6",
            "ip": None,
            "vtpdomain": ""
        },
        {
            "platform": "AIR-AP2802I-B-K9",
            "remoteif": "GigabitEthernet0",
            "nativevlan": None,
            "name": "AP1000.1000.1000",
            "version": "Cisco AP Software, ap3g3-k9w8 Version: 8.5.103.0",
            "localif": "GigabitEthernet1/0/47",
            "ip": "10.1.1.52",
            "vtpdomain": None
        },
    ]
    for filter_set in test_filters:
        log.info("_tests.test_filter_cdp_device: Testing filter set %s" %
                 filter_set)
        result = []
        for device in devices:
            if cdp.filter_cdp_device(device, filter_set, False):
                result.append(device)
        log.info("_tests.test_filter_cdp_device: Matched devices\n%s" %
                 json.dumps(result, indent=4))


def test_cdp_conversion():
    def multilineinput(ending):
        result = ""
        for line in iter(raw_input, ending):
            result += line+"\n"
            return result[0:len(result)-1]
    log.info("_tests.test_cdp_conversion: Input CDP data ending with '^'")
    cdpnei = multilineinput("^")
    result = cdp.convert_cdp_output(cdpnei)
    result = json.dumps(result, indent=4)
    log.info("_tests.test_cdp_conversion: Returned:\n%s" % result)


def test_autoqueue():
    def worker(self, item):
        import time
        print(item["key1"])
        time.sleep(1)
    aq = commons.autoqueue(10, worker, None)
    for i in range(100):
        aq.put({"key1": str(i)})
        if not i % 10:  # if divisible by 10
            aq.put({"key2": str(i)})  # Insert some error data
    aq.block()


def run_tests(args):
    tests = [
        {
            "function": test_build_cdp_filters,
            "run": args.test_build_cdp_filters
        },
        {
            "function": test_filter_cdp_device,
            "run": args.test_filter_cdp_device
        },
        {
            "function": test_cdp_conversion,
            "run": args.test_cdp_conversion
        },
        {
            "function": test_autoqueue,
            "run": args.test_autoqueue
        },
    ]
    for test in tests:
        if test["run"]:
            test["function"]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='AutoShell - Module Library Test Suite')
    parser.add_argument(
                        '-b', "--test_build_cdp_filters",
                        help="Run test_build_cdp_filters",
                        dest="test_build_cdp_filters",
                        action='store_true')
    parser.add_argument(
                        '-f', "--test_filter_cdp_device",
                        help="Run test_filter_cdp_device",
                        dest="test_filter_cdp_device",
                        action='store_true')
    parser.add_argument(
                        '-c', "--test_cdp_conversion",
                        help="Run test_cdp_conversion",
                        dest="test_cdp_conversion",
                        action='store_true')
    parser.add_argument(
                        '-a', "--test_autoqueue",
                        help="Run test_autoqueue",
                        dest="test_autoqueue",
                        action='store_true')
    args = parser.parse_args()
    run_tests(args)
