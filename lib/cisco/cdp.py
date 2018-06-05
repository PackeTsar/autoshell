#!/usr/bin/python

import re
import json
import logging


def build_cdp_filters(expressions):
    log = logging.getLogger("modules")
    log.debug("cdp.build_cdp_filters:\
 Parsing filter expressions: %s" % expressions)
    result = []
    if not expressions:
        return result
    attribs = [
        "name",
        "ip",
        "platform",
        "localif",
        "remoteif",
        "vtpdomain",
        "nativevlan",
        "version"]
    for entry in expressions:
        if ":" not in entry:
            log.warning("cdp.build_cdp_filters:\
 Discarding filter expression (%s): No ':' found in expression" % entry)
        else:
            attrib = entry.split(":")[0]
            regex = entry.split(":")[1]
            if attrib not in attribs:
                log.warning("cdp.build_cdp_filters:\
 Discarding filter expression (%s):\
 Illegal attribute. Allowed attributes: (%s)"
                            % (entry, " ".join(attribs)))
            else:
                try:
                    re.compile(regex)
                    newfilter = {"attrib": attrib, "regex": regex}
                    log.debug("cdp.build_cdp_filters:\
 Adding filter element to filter list: %s" % newfilter)
                    result.append(newfilter)
                except Exception as e:
                    log.warning("cdp.build_cdp_filters:\
 Discarding filter expression (%s): REGEX Error: %s" % (entry, str(e)))
    log.debug("cdp.build_cdp_filters:\
Returning parsed filters:\n%s" % json.dumps(result, indent=4))
    return result


def filter_cdp_device(cdpdevice, filters, and_logic):
    log = logging.getLogger("modules")
    log.debug(
        "cdp.filter_cdp_device: Filtering device (%s) with IP (%s)"
        % (cdpdevice["name"], cdpdevice["ip"]))
    if not filters:  # If a filter is not set
        log.debug(
            "cdp.filter_cdp_device: No filter set. Returning True")
        return True  # Don't filter the device
    if and_logic:  # If logic is AND
        for flter in filters:
            log.debug(
                "cdp.filter_cdp_device: Processing Filter (%s)"
                % flter)
            if cdpdevice[flter["attrib"]]:  # If there is a value there
                findings = re.findall(
                    flter["regex"],
                    cdpdevice[flter["attrib"]])
                log.debug(
                    "cdp.filter_cdp_device: Regex search returned: %s" %
                    str(findings))
                if not findings:
                    log.debug("cdp.filter_cdp_device: Returning False")
                    return False
        log.debug("cdp.filter_cdp_device: Returning True")
        return True
    else:  # if logic is OR
        for flter in filters:
            log.debug(
                "cdp.filter_cdp_device: Processing Filter (%s)"
                % flter)
            if cdpdevice[flter["attrib"]]:  # If there is a value there
                findings = re.findall(
                    flter["regex"],
                    cdpdevice[flter["attrib"]])
                log.debug(
                    "cdp.filter_cdp_device: Regex search returned: %s"
                    % str(findings))
                if findings:
                    log.debug("cdp.filter_cdp_device: Returning True")
                    return True
        log.debug("cdp.filter_cdp_device: Returning False")
        return False


def convert_cdp_output(shcdpneidet):
    cdpattribs = [
        {
            "attrib": "name",
            "clean": [],
            "match": [
                "Device ID: ",
                "Device ID:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "ip",
            "clean": [],
            "match": [
                "IP address: ",
                "IP address:",
                "IPv4 Address: ",
                "IPv4 Address:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "platform",
            "clean": [
                "cisco ",
                "Cisco "
                ],
            "match": [
                "Platform: ",
                "Platform:"
                ],
            "delimiter": ",\n"
        },
        {
            "attrib": "localif",
            "clean": [],
            "match": [
                "Interface: ",
                "Interface:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "remoteif",
            "clean": [
                "Port ID (outgoing port): "
                ],
            "match": [
                "Port ID \\(outgoing port\\): "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "vtpdomain",
            "clean": [
                "'"
                ],
            "match": [
                "VTP Management Domain: ",
                "VTP Management Domain:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "nativevlan",
            "clean": [],
            "match": [
                "Native VLAN: ",
                "Native VLAN:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "version",
            "clean": [],
            "match": [
                "Version :\n",
                "Version:\n"
                ],
            "delimiter": "\n"
        }]

    def _pulldevattbs(devlines, cdpattribs):
        data = {}
        for attrib in cdpattribs:
            for match in attrib["match"]:
                regex = "%s[^%s]*" % (match, attrib["delimiter"])
                search = re.findall(regex, devlines)
                if len(search) > 0:
                    matched = search[0].replace(match, "")
                    for rm in attrib["clean"]:
                        matched = matched.replace(rm, "")
                    data.update({attrib["attrib"]: matched})
                    break
                if attrib["attrib"] not in data:  # No match was made
                    data.update({attrib["attrib"]: None})
        return data
    result = []
    delineator = shcdpneidet.split("\n")[0]  # Set delineator as the first line
    if not delineator:
        # Set delineator as the second line
        delineator = shcdpneidet.split("\n")[1]
    # Split on the delineator
    deviceblocks = shcdpneidet.split(delineator)
    devicelines = []  # List of lists of device lines
    # For each block of text describing a device
    for block in deviceblocks:
        if block != "":  # If the block is not empty
            result.append(_pulldevattbs(block, cdpattribs))
    return result


def guess_cdp_dev_type(cdpdevice):
    log = logging.getLogger("modules")
    _dev_types = [
        {
            "device_type": "cisco_ios",
            "match": {
                "attrib": "version",
                "regex": "Cisco IOS Software"
            }
        },
        {
            "device_type": "cisco_nxos",
            "match": {
                "attrib": "version",
                "regex": "NX-OS"
            }
        },
        {
            "device_type": "cisco_wlc",
            "match": {
                "attrib": "version",
                "regex": "RTOS"
            }
        }]
    log.debug("cdpwalk.worker_class._guess_dev_type:\
Guessing device type on CDP device:\n%s"
              % json.dumps(cdpdevice, indent=4))
    for criteria in _dev_types:
        if cdpdevice[criteria["match"]["attrib"]]:  # If not None
            if re.findall(criteria["match"]["regex"],
                          cdpdevice[criteria["match"]["attrib"]]):
                log.debug("cdpwalk.worker_class._guess_dev_type:\
Returning type (%s)" % criteria["device_type"])
                return criteria["device_type"]
    log.debug("cdpwalk.worker_class._guess_dev_type:\
Returning default type (cisco_ios)")
    return "cisco_ios"
