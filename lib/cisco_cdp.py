#!/usr/bin/python

"""
cisco_cdp contains functions used for reading, filtering, and parsing
screen-scraped Cisco CDP information
"""

import re
import json
import logging


def build_cdp_filters(expressions):
    """
    Interpret and parse user-input CDP filter expressions. Filter expressions
    are a string in the format of ATTRIBUTE:REGEX. This function simply parses
    these expressions and returns dictionary items:
    IE: 'platform:AIR' would return {"attrib": "platform", "regex": "AIR"}
    A list of expressions strings is input. A list of dictionary
    items is output
    """
    log = logging.getLogger("modules")
    log.debug("cisco_cdp.build_cdp_filters:\
 Parsing filter expressions: %s" % expressions)
    result = []
    if not expressions:  # If there were no input expressions
        return result
    # Allowed attributes
    attributes = [
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
            log.warning("cisco_cdp.build_cdp_filters:\
 Discarding filter expression (%s):\
 No ':' found in expression. Discarding" % entry)
        else:
            attrib = entry.split(":")[0]
            regex = entry.split(":")[1]
            if attrib not in attributes:
                log.warning("cisco_cdp.build_cdp_filters:\
 Discarding filter expression (%s):\
 Illegal attribute. Allowed attributes: (%s)"
                            % (entry, " ".join(attributes)))
            else:
                try:
                    # Try the regex to make sure its valid
                    # Will throw exception if invalid
                    re.compile(regex)
                    newfilter = {"attrib": attrib, "regex": regex}
                    log.debug("cisco_cdp.build_cdp_filters:\
 Adding filter element to filter list: %s" % newfilter)
                    result.append(newfilter)
                except Exception as e:
                    log.warning("cisco_cdp.build_cdp_filters:\
 Discarding filter expression (%s): REGEX Error: %s" % (entry, str(e)))
    log.debug("cisco_cdp.build_cdp_filters:\
 Returning parsed filters:\n%s" % json.dumps(result, indent=4))
    return result


def filter_cdp_device(cdpdevice, filters, and_logic):
    """
    Run a CDP dict item (cdpdevice) through CDP filters
    (from build_cdp_filters) and return True if CDP dict matches the filter
    criteria. CDP dict items are in the format of:
    {
        "platform": "<Part_Number>",
        "remoteif": "<Interface_Name>",
        "nativevlan": "<Native_VLAN_ID>",
        "name": "<Hostname>",
        "version": "<Software_Description>",
        "localif": "<Interface_Name>",
        "ip": "<Device_IP_Address>",
        "vtpdomain": "<VTP_Domain_Name>"
    }
    """
    log = logging.getLogger("modules")
    log.debug(
        "cisco_cdp.filter_cdp_device: Filtering device (%s) with IP (%s)"
        % (cdpdevice["name"], cdpdevice["ip"]))
    if not filters:  # If a filter is not set
        log.debug(
            "cisco_cdp.filter_cdp_device: No filter set. Returning True")
        return True  # Don't filter the device
    if and_logic:  # If filter logic is AND
        for flter in filters:
            log.debug(
                "cisco_cdp.filter_cdp_device: Processing Filter (%s)"
                % flter)
            if cdpdevice[flter["attrib"]]:  # If there is a value there
                findings = re.findall(
                    flter["regex"],
                    cdpdevice[flter["attrib"]])
                log.debug(
                    "cisco_cdp.filter_cdp_device: Regex search returned: %s" %
                    str(findings))
                if not findings:
                    log.debug("cisco_cdp.filter_cdp_device: Returning False")
                    return False
        log.debug("cisco_cdp.filter_cdp_device: Returning True")
        return True
    else:  # If filter logic is OR (default)
        for flter in filters:
            log.debug(
                "cisco_cdp.filter_cdp_device: Processing Filter (%s)"
                % flter)
            if cdpdevice[flter["attrib"]]:  # If there is a value there
                findings = re.findall(
                    flter["regex"],
                    cdpdevice[flter["attrib"]])
                log.debug(
                    "cisco_cdp.filter_cdp_device: Regex search returned: %s"
                    % str(findings))
                if findings:
                    log.debug("cisco_cdp.filter_cdp_device: Returning True")
                    return True
        log.debug("cisco_cdp.filter_cdp_device: Returning False")
        return False


def convert_cdp_output(shcdpneidet):
    """
    Screen-scrape the CLI output from the 'show cdp neighbors detail' command
    on a Cisco device and format into a list of dicts
    """
    #  Attributes to find and include in each CDP device dict
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
        """
        search a block of CDP data with each attribute set and return
        the cleaned up data
        """
        log = logging.getLogger("modules")
        data = {}
        for attrib in cdpattribs:
            # For each match statement
            for match in attrib["match"]:
                # Build a regex
                regex = "%s[^%s]*" % (match, attrib["delimiter"])
                search = re.findall(regex, devlines)
                if len(search) > 0:
                    # Match first result, replacing what was searched
                    matched = search[0].replace(match, "")
                    for rm in attrib["clean"]:
                        # Clean of any other useless info
                        matched = matched.replace(rm, "")
                    data.update({attrib["attrib"]: matched})
                    break
                if attrib["attrib"] not in data:  # No match was made
                    # Add an empty attribute
                    data.update({attrib["attrib"]: None})
        return data
    result = []
    # Set delineator as the first line
    # Usually looks like '-------------------------'
    delineator = shcdpneidet.split("\n")[0]
    # Some devices (like WLC) return an empty first line
    if not delineator:  # If empty first line
        # Set delineator as the second line
        delineator = shcdpneidet.split("\n")[1]
    # Split into list of strings. Each string having all data for a CDP device
    # Split on the delineator
    deviceblocks = shcdpneidet.split(delineator)
    # For each block of text describing a device
    for block in deviceblocks:
        if block != "":  # If the block is not empty
            # Run the block through _pulldevattbs
            result.append(_pulldevattbs(block, cdpattribs))
    return result


def guess_cdp_dev_type(cdpdevice):
    """
    guess a netmiko device_type based on data in the CDP device dict
    """
    log = logging.getLogger("modules")
    # List of possible device_types with criteria (attrib, regex pairs)
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
    log.debug("cisco_cdp.guess_cdp_dev_type:\
 Guessing device type on CDP device:\n%s"
              % json.dumps(cdpdevice, indent=4))
    for criterion in _dev_types:
        if cdpdevice[criterion["match"]["attrib"]]:  # If not None
            # If a regex search of the value in the CDP device dict
            # returns a match
            if re.findall(criterion["match"]["regex"],
                          cdpdevice[criterion["match"]["attrib"]]):
                log.debug("cisco_cdp.guess_cdp_dev_type:\
 Returning type (%s)" % criterion["device_type"])
                # Return its device_type
                return criterion["device_type"]
    log.debug("cisco_cdp.guess_cdp_dev_type:\
 Returning default type (cisco_ios)")
    # Otherwise return the default type
    return "cisco_ios"
