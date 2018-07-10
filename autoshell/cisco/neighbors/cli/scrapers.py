#!/usr/bin/python

"""
cisco.neighbors.cli.scrapers contains functions used for reading, filtering,
and parsing screen-scraped Cisco LLDP and CDP information. Output is a list
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


# cisco.neighbors.cli.scrapers.neighbor_template is used to normalize each
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
    cisco.neighbors.cli.scrapers._pulldevattbs searches a block of data with
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
    cisco.neighbors.cli.scrapers._pulldevattbs divides device data into blocks
    of text, with each block having info for one device. Then parses each
    block with a set of attribute matches (using _pulldevattbs).
    """
    result = []
    # Set delineator as the first line
    # Usually looks like '-------------------------'
    delineator = data.split("\n")[0]
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


def cisco_ios_cdp_scraper(shcdpneidet):
    """
    cisco.neighbors.cli.scrapers.cisco_ios_cdp_scraper screen-scrapes the CLI
    output from the 'show cdp neighbors detail' command on a Cisco device and
    formats into a list of dicts.
    """
    #  Attributes to find and include in each CDP device dict
    cdpattribs = [
        {
            "attrib": "sysname",
            "clean": [],
            "match": [
                "Device ID: ",
                "Device ID:"
                ],
            "delimiter": ",\\s"
        },
        {
            "attrib": "addresses",
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
            "attrib": "sysdesc",
            "clean": [],
            "match": [
                "Version :\n",
                "Version:\n"
                ],
            "delimiter": "\n"
        }]
    return _attrib_search(cdpattribs, shcdpneidet)


def cisco_ios_lldp_combine(lldp_primary, lldp_secondary):
    """
    cisco.neighbors.cli.scrapers.cisco_ios_lldp_combine combines LLDP-type
    data between two lists, preferring the primary data but adding in the
    secondary data when the primary is empty.
    """
    def _find_match(devpri, sec_list, attrib):
        """
        cisco.neighbors.cli.scrapers.cisco_ios_lldp_combine._find_match
        searches through a secondary list of devices to find an entry with a
        similar attribute to the primary device; returning the secondary
        device.
        """
        # For each attribute in the attribute list
        for priattrib in devpri[attrib]:
            # For each device in the seondary list
            for secdev in sec_list:
                # For each entry in the attribute list
                for secattrib in secdev[attrib]:
                    # If the secondary is in the primary
                    if secattrib in priattrib:
                        # Return the secondary device for merging
                        return secdev
    # Iter through lldp_primary as primary info source
    for pri_device in lldp_primary:
        # Find the second device
        sec_device = _find_match(pri_device, lldp_secondary, "sysname")
        # If we got a value returned
        if sec_device:
            # Check each attribute list in the primary device
            for attrib in pri_device:
                # If that attribute list is empty
                if not pri_device[attrib]:
                    # And the secondary has a value
                    if sec_device[attrib]:
                        # Overwrite with the secondary
                        pri_device[attrib] = sec_device[attrib]
    return lldp_primary


def cisco_ios_lldp_de_scraper(shlldpneidet):
    """
    cisco.neighbors.cli.scrapers.cisco_ios_lldp_de_scraper screen-scrapes
    the CLI output from the 'show lldp neighbors detail' command on a Cisco
    device and formats into a list of dicts.
    """
    #  Attributes to find and include in each LLDP device dict
    lldpattribs = [
        {
            "attrib": "sysid",
            "clean": [],
            "match": [
                "Chassis id: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "remoteif",
            "clean": [],
            "match": [
                "Port id: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "ttl",
            "clean": [],
            "match": [
                "Time remaining: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "remoteifdesc",
            "clean": [],
            "match": [
                "Port Description: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "sysname",
            "clean": [],
            "match": [
                "System Name: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "sysdesc",
            "clean": [],
            "match": [
                "System Description: \n"
                ],
            "delimiter": "\n\n"
        },
        {
            "attrib": "syscap",
            "clean": [],
            "match": [
                "System Capabilities: "
                ],
            "delimiter": "\n"
        },
        {
            "attrib": "addresses",
            "clean": [],
            "match": [
                "IP: "
                ],
            "delimiter": "\n"
        }]
    return _attrib_search(lldpattribs, shlldpneidet)


def cisco_ios_lldp_br_scraper(cdplldpnei):
    """
    cisco.neighbors.cli.scrapers.cisco_ios_lldp_br_scraper screen-scrapes the
    CLI output from the 'show lldp neighbors' command on a Cisco device and
    format into a list of dicts. This function is needed to get LLDP neighbors
    with their corresponding local interface as the output of
    'show lldp neighbors detail' does not contain that info.
    """
    def get_headers(cdplldpnei):
        """
        cisco.neighbors.cli.scrapers.cisco_ios_lldp_br_scraper.get_headers
        pulls the headers of the LLDP neighbors table and returns the header
        name along with it's starting column depth (needed because data from
        columns may run together). Will return [0] a list of dicts where each
        dict contains the column name and its starting depth, and [1] an
        integer which is the starting line of table data.
        """
        lines = cdplldpnei.split("\n")
        # List of dicts, each dict describes a column
        headers = []
        # Which line are we currently on
        line_index = 0
        for line in lines:
            if "Device ID" in line:
                # Split on a double space since some header names have spaces
                heads = line.split("  ")
                for each in heads:
                    # Skip empty entries
                    if each:
                        # Remove a leading space (since we split on doubles)
                        if each[0] == " ":
                            each = each[1:]
                        headers.append({
                            "name": each,
                            "start": line.find(each)
                        })
                # Return data since we found the line with the headers
                return (headers, line_index + 1)
            # If no 'Device ID' in this line, move to the next
            line_index += 1
    # Mapping the Table Headers to normalized attributes in neighbor template
    mappings = {
        "remoteif": ["Port ID"],
        "sysname": ["Device ID"],
        "syscap": ["Capability"],
        "localif": ["Local Intf"]
    }
    # Pull tuple with headers and start line
    headers = get_headers(cdplldpnei)
    # If no headers, return an empty result
    if not headers:
        return []
    # If not empty, pull out the headers and starting line
    headers, start = get_headers(cdplldpnei)
    result = []
    # Iterate through the table lines, starting at the correct line
    for entry in cdplldpnei.split("\n")[start:]:
        headindex = 0
        # Start with a copy of the neighbor template
        data = dict(neighbor_template)
        for header in headers:
            # If this is not the last column
            if len(headers) > headindex+1:
                # Set the end character for this column
                # to the start of the next column
                end = headers[headindex+1]["start"]
            # If this is the last column
            else:
                # Set a high number to the last character
                end = 1000
            # Set the value and remove spaces
            value = entry[header["start"]:end].replace(" ", "")
            # If this is the first column and the value is empty
            # then we are likely out of the table data
            if not value and headindex == 0:
                return result
            else:
                # Normalized attrib from mappings
                mapped_attrib = None
                for attrib in mappings:
                    # For each header we can match for that attribute
                    for mapped_header in mappings[attrib]:
                        # If we have a match
                        if mapped_header == header["name"]:
                            # Set the mapped attrib and stop looking
                            mapped_attrib = attrib
                            break
                    # If found, stop looking
                    if mapped_attrib:
                        break
                # If found, update the data with the value
                if mapped_attrib:
                    data.update({
                        mapped_attrib: [value]
                        })
            headindex += 1
        result.append(data)
    return result
