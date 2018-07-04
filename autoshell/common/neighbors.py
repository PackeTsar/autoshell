#!/usr/bin/python

"""
common_neighbors
"""


# Built-In Libraries
import re
import json
import logging

# Autoshell Libraries
from . import expressions as espsns


log = logging.getLogger("shared")


class neighbor_device:
    """
    neighbor_device is used to contain all the attribute infomation for a
    device neighbor found on a host.
    """
    def __init__(self, sysid=[], remoteif=[], ttl=[], remoteifdesc=[],
                 sysname=[], sysdesc=[], syscap=[], addresses=[],
                 localif=[], platform=[]):
        self.sysid = self.neighbor_attribute(
            Value=sysid,
            LLDP_TLV_Type=1,
            LLDP_TLV_Name="Chassis ID",
            Description="Chassis MAC Address")
        self.remoteif = self.neighbor_attribute(
            Value=remoteif,
            LLDP_TLV_Type=2,
            LLDP_TLV_Name="Port ID",
            CDP_TLV_Type=3,
            CDP_TLV_Name="Port ID",
            Description="Remote Interface Name")
        self.ttl = self.neighbor_attribute(
            Value=ttl,
            LLDP_TLV_Type=3,
            LLDP_TLV_Name="Time To Live",
            Description="LLDP Time To Live")
        self.remoteifdesc = self.neighbor_attribute(
            Value=remoteifdesc,
            LLDP_TLV_Type=4,
            LLDP_TLV_Name="Port Description",
            Description="LLDP Description on Remote Interface")
        self.sysname = self.neighbor_attribute(
            Value=sysname,
            LLDP_TLV_Type=5,
            LLDP_TLV_Name="System Name",
            CDP_TLV_Type=1,
            CDP_TLV_Name="Device ID",
            Description="System Hostname")
        self.sysdesc = self.neighbor_attribute(
            Value=sysdesc,
            LLDP_TLV_Type=6,
            LLDP_TLV_Name="System Description",
            CDP_TLV_Type=5,
            CDP_TLV_Name="Software Version",
            Description="System/Software Description")
        self.syscap = self.neighbor_attribute(
            Value=syscap,
            LLDP_TLV_Type=7,
            LLDP_TLV_Name="System Capabilities",
            CDP_TLV_Type=4,
            CDP_TLV_Name="Capabilities",
            Description="LLDP System Capability Codes")
        self.addresses = self.neighbor_attribute(
            Value=addresses,
            LLDP_TLV_Type=8,
            LLDP_TLV_Name="Management Address",
            CDP_TLV_Type=2,
            CDP_TLV_Name="Addresses",
            Description="Management Hostname/IP Address")
        self.localif = self.neighbor_attribute(
            Value=localif,
            Description="Local Interface Name")
        self.platform = self.neighbor_attribute(
            Value=platform,
            CDP_TLV_Type=6,
            CDP_TLV_Name="Platform",
            Description="CDP Specific System Part Number")

    def __call__(self):
        data = {}
        for attribute in self.__dict__:
            data.update({attribute: self.__dict__[attribute].Value})
        return data

    class neighbor_attribute:
        def __init__(self, Value=None, LLDP_TLV_Type=None, LLDP_TLV_Name=None,
                     CDP_TLV_Type=None, CDP_TLV_Name=None, Description=None):
            self.Value = Value
            self.LLDP_TLV_Type = LLDP_TLV_Type
            self.LLDP_TLV_Name = LLDP_TLV_Name
            self.CDP_TLV_Type = CDP_TLV_Type
            self.CDP_TLV_Name = CDP_TLV_Name
            self.Description = Description


allowed_attributes = list(neighbor_device().__dict__)


def build_neighbor_filters(expressions):
    """
    Interpret and parse user-input neighbor filter expressions. Filter
    expressions are a string in the format of ATTRIBUTE:REGEX.
    Expressions can be combined with AND logic using the delineator '%'.
    The colon and percent sign delineators can be changed using a double-dash:
    ':%--ATTRIBUTE:REGEX%ATTRIBUTE:REGEX' uses default delineators
    ';$--ATTRIBUTE;REGEX$ATTRIBUTE;REGEX' modifies the delineators
        to ';' and '$'
    This function parses these expressions and returns lists if dict items:
    IE: 'platform:AIR' would return [{"attribute": "platform", "regex": "AIR"}]
    A list of expression strings is input. A list of lists, each containing
    a dict item is output
    Valid Expressions:
        - platform:WS
        - platform:WS%addresses:192.168
        - sysid:1a:2b:3c.*
        - :%--platform:AIR%addresses:192
    """
    log.debug("common.neighbors.build_neighbor_filters:\
 Parsing filter expressions: %s" % expressions)
    result = []
    if not expressions:  # If there were no input expressions
        return result
    else:
        exp_data = espsns.parse_expression(expressions, ["-", ":", "%"])
        for response in exp_data:
            if response["type"] == "string":
                fltr = _process_string_exps(response["value"])
                if fltr:
                    result.append(fltr)
            if response["type"] == "file":
                fltr = _process_file_exps(response["value"])
                if fltr:
                    result.append(fltr)
        log.debug("common.neighbors.build_neighbor_filters:\
 Returning:\n%s" % json.dumps(result, indent=4))
        return result


def _process_file_exps(file_data):
    def _normalize(flt_dict):
        attribute = None
        regex = None
        if "attribute" in flt_dict and "regex" in flt_dict:
            attribute = flt_dict["attribute"]
            if attribute not in allowed_attributes:
                log.warning("common.neighbors._process_file_exps:\
 Illegal attribute (%s). Discarding expression. Allowed attributes are: %s" %
                            (attribute, " ".join(allowed_attributes)))
                return None
            else:
                regex = str(flt_dict["regex"])
                try:
                    re.compile(regex)
                except Exception as e:
                    log.debug("common.neighbors._process_file_exps:\
 Malformed regex (%s). Discarding expression" % regex)
                    return None
                result = {
                    "attribute": attribute,
                    "regex": regex
                }
                log.debug("common.neighbors._process_file_exps:\
 Adding new filter from file:\n%s" % json.dumps(result, indent=4))
                return result
        else:
            log.warning("common.neighbors._process_file_exps:\
 Cannot find the 'attribute' and 'regex' keys. Discarding filter")
            return None
    result = []
    if type(file_data) == dict:
        norm_flt = _normalize(file_data)
        if norm_flt:
            result.append(norm_flt)
        else:
            return None
    elif type(file_data) == list:
        for entry in file_data:
            norm_flt = _normalize(entry)
            if norm_flt:
                result.append(norm_flt)
            else:
                return None
    return result


def _process_string_exps(str_list):
    result = []
    for entry in str_list:
        if len(entry) < 2:
            log.debug("common.neighbors._process_string_exps:\
 Discarding filter expression (%s). No regex found in entry (%s)" %
                      (str_list, entry))
            return None
        elif entry[0] not in allowed_attributes:
            log.warning("common.neighbors._process_string_exps:\
 Illegal attribute (%s). Discarding expression. Allowed attributes are: %s" %
                        (entry[0], " ".join(allowed_attributes)))
        else:
            regex = str(entry[1])
            try:
                re.compile(regex)
            except Exception as e:
                log.debug("common.neighbors._process_string_exps:\
 Malformed regex (%s). Discarding expression" % regex)
                return None
            fltr = {
                "attribute": entry[0],
                "regex": regex
            }
            result.append(fltr)
    if result:
        log.debug("common.neighbors._process_string_exps:\
 Adding Filter:\n%s" % json.dumps(result, indent=4))
        return result
    else:
        log.debug("common.neighbors._process_string_exps:\
 No filters to add")
        return result


def filter_neighbor_device(neighbor, filters):
    """
    Run a neighbor_device instance through neighbor filters
    (from build_neighbor_filters) and return True if instance matches the
    filter criteria.
    """
    log.debug(
        "common.neighbors.filter_neighbor_device:\
 Filtering device (%s) with IP (%s) using filter:\n%s"
        % (neighbor.sysname.Value,
           neighbor.addresses.Value,
           json.dumps(filters, indent=4)))
    if not filters:  # If a filter is not set
        log.debug(
            "common.neighbors.filter_neighbor_device:\
 No filter set. Returning True")
        return True  # Don't filter the device
    total_results = []
    for filter_set in filters:
        log.debug(
            "common.neighbors.filter_neighbor_device:\
 Processing Filter Set (%s)" % filter_set)
        set_results = []
        for flter in filter_set:
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Processing Filter (%s)" % flter)
            matched = False
            if neighbor()[flter["attribute"]]:  # If there is a value there
                for value in neighbor()[flter["attribute"]]:
                    findings = re.findall(
                        flter["regex"],
                        value)
                    log.debug(
                        "common.neighbors.filter_neighbor_device:\
 Regex search returned: %s" %
                        str(findings))
                    if findings:
                        matched = True
            set_results.append(matched)
        if False in set_results:
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Neighbor FAILED this filter")
        else:
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Neighbor PASSED this filter. Returning True")
            return True
        total_results.append(set_results)
    log.debug(
        "common.neighbors.filter_neighbor_device:\
 All filters failed. Returning False")
    return False
