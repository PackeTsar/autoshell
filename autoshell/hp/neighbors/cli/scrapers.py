#!/usr/bin/python

"""
hp.neighbors.cli.scrapers contains functions used for reading, filtering,
and parsing screen-scraped LLDP and CDP information. Output is a list
of dicts with keys:
    - sysid
    - remoteif
    - ttl
    - remoteifdesc
    - sysname
    - sysdesc
    - syscap
    - addresses
    - localif
    - platform
  Each value will be a list of strings
"""

# Built-In Libraries
import re
import json


# hp.neighbors.cli.scrapers.neighbor_template is used to normalize each
#  neighbor built by the methods
neighbor_template = {
    "sysid": [],
    "remoteif": [],
    "ttl": [],
    "remoteifdesc": [],
    "sysname": [],
    "sysdesc": [],
    "syscap": [],
    "addresses": [],
    "localif": [],
    "platform": []
}


def _pulldevattbs(datablock, attribs):
    """
    hp.neighbors.cli.scrapers._pulldevattbs searches a block of data with
    each attribute set and returns the cleaned up data.
    """
    # Make a copy of the neighbor template
    data = dict(neighbor_template)
    for attrib in attribs:
        # For each match statement
        for match in attrib["match"]:
            # Build a regex
            regex = "%s[^%s]*" % (match, attrib["delimiter"])
            search = re.findall(regex, datablock)
            if len(search) > 0:
                # Match first result, replacing what was searched
                # matched = search[0].replace(match, "")
                matched = []
                for item in search:
                    item = item.replace(match, "")
                    for rm in attrib["clean"]:
                        # Clean of any other useless info
                        item = item.replace(rm, "")
                    matched.append(item)
                data.update({attrib["attrib"]: matched})
                break
            if attrib["attrib"] not in data:  # No match was made
                # Add an empty attribute
                data.update({attrib["attrib"]: None})
    return data


def _attrib_search(attribs, data):
    """
    hp.neighbors.cli.scrapers._pulldevattbs divides device data into blocks
    of text, with each block having info for one device. Then parses each
    block with a set of attribute matches (using _pulldevattbs).
    """
    result = []
    # Set delineator as the first line
    # Usually looks like '-------------------------'
    delineator = "------------------------------------------------------------------------------"
    # Some devices (like WLC) return an empty first line
    if not delineator:  # If empty first line
        # Set delineator as the second line
        delineator = data.split("\n")[1]
    # Split into list of strings. Each string having all data for a CDP device
    # Split on the delineator
    deviceblocks = data.split(delineator)
    # For each block of text describing a device
    for block in deviceblocks:
        if block != "":  # If the block is not empty
            # Run the block through _pulldevattbs
            result.append(_pulldevattbs(block, attribs))
    return result


def hp_cdp_scraper(shcdpneidet):
    """
    hp.neighbors.cli.scrapers.hp_cdp_scraper screen-scrapes the CLI
    output from the 'show cdp neighbors detail' command on a HP device and
    formats into a list of dicts.
    """
    #  Attributes to find and include in each CDP device dict
    cdpattribs = [
        {
            "attrib": "sysname",
            "clean": [],
            "match": [
                "Device ID : "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "addresses",
            "clean": [],
            "match": [
                "Address      : "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "platform",
            "clean": [],
            "match": [
                "Platform     : "
                ],
            "delimiter": ",\n"
        },
        {
            "attrib": "localif",
            "clean": [],
            "match": [
                "Port : "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "remoteif",
            "clean": [],
            "match": [
                "Device Port  : "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "syscap",
            "clean": [],
            "match": [
                "Capability   : "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "sysdesc",
            "clean": [],
            "match": [
                "Version      : "
                ],
            "delimiter": "\n"
        }]
    return _attrib_search(cdpattribs, shcdpneidet)


def hp_lldp_de_scraper(shlldpneidet):
    """
    hp.neighbors.cli.scrapers.hp_lldp_de_scraper screen-scrapes
    the CLI output from the 'show lldp info remote-device all' command on
    a HP device and formats into a list of dicts.
    """
    #  Attributes to find and include in each LLDP device dict
    lldpattribs = [
        {
            "attrib": "sysid",
            "clean": [],
            "match": [
                "ChassisId    : "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "remoteif",
            "clean": [],
            "match": [
                "PortId       : "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "localif",
            "clean": [],
            "match": [
                "Local Port   : "
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "ttl",
            "clean": [],
            "match": [],
            "delimiter": "\n"
        },
        {
            "attrib": "remoteifdesc",
            "clean": [],
            "match": [
                "PortDescr    : "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "sysname",
            "clean": [],
            "match": [
                "SysName      : "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "sysdesc",
            "clean": [],
            "match": [
                "System Descr : "
                ],
            "delimiter": "\n\n"
        },
        {
            "attrib": "syscap",
            "clean": [],
            "match": [
                "System Capabilities"
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "addresses",
            "clean": [],
            "match": [
                "Address : "
                ],
            "delimiter": "\n"
        }]
    return _attrib_search(lldpattribs, shlldpneidet)
