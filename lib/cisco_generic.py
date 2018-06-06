#!/usr/bin/python

"""
cisco_generic contains useful functions for interacting with Cisco devices.
"""

import shlex
import logging


def convert_inventory_output(shinv):
    """
    Screen-scrape the CLI output from the 'show inventory' command on a Cisco
    device and format into a list of dicts
    """
    # Attributes to find and include in each device dict
    _invattribs = [
         {
             "attrib": "name",
             "clean": [],
             "match": "NAME:"
         },
         {
             "attrib": "description",
             "clean": [],
             "match": "DESCR:"
         },
         {
             "attrib": "part",
             "clean": [],
             "match": "PID:"
         },
         {
             "attrib": "version",
             "clean": [],
             "match": "VID:"
         },
         {
             "attrib": "serial",
             "clean": [],
             "match": "SN:"
         }]
    # List of match expressions
    _attrib_matches = [each["match"] for each in _invattribs]
    result = []
    # List of blocks, each with info for a single device
    # Assuming doule-spaces in-between device blocks
    blocks = shinv.split("\n\n")
    for block in blocks:
        # May get empty blocks at the end
        if block != "":
            item = {}
            # Replace commas and newlines to make matching easier
            block = block.replace("\n", " ")
            block = block.replace(",", " ")
            # Split on spaces, considering quote wraps, similar to
            # how BASH will consider "these words" to be one word
            words = shlex.split(block)
            for attrib in _invattribs:
                # Using an index because the value we want will be
                # the word after a match
                index = 0
                # Initialize the value so we will always have a result value,
                # keeping output consistent; always containing the same keys
                value = None
                for word in words:
                    if word == attrib["match"]:
                        # If this is the last word and there
                        # was no trailing value
                        if index+1 >= len(words):
                            item.update({attrib["attrib"]: None})
                        # If there was no value, then the next word
                        # will be in the _attrib_matches list
                        elif words[index+1] in _attrib_matches:
                            item.update({attrib["attrib"]: None})
                        # Otherwise, we assume the next word is the value
                        else:
                            item.update({attrib["attrib"]: words[index+1]})
                        # We found this attrib. On to the next one
                        break
                    index += 1
            result.append(item)
    return result
