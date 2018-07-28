#!/usr/bin/python

"""
common.neighbors contains common classes and functions useful for the
processing of host LLDP and CDP neighbors. The classes define standard
attribute sets which can be used for LLDP or CDP. The functions are useful
for building and processing filter expressions to filter unwanted neighbors
using instances of the standard neighbor_device class.
"""


# Built-In Libraries
import re
import json
import logging

# Autoshell Libraries
from . import expressions
from .. import cisco
from .. import hp


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


# common.neighbors.HANDLER_MAP is a mapping of host types to neighbor handlers.
#  Each handler is specific to a connection type (ie: "cli" or "netconf") and
#  is matched against the host type using a regular expression.
HANDLER_MAP = [
    {
        "handlers": {
           "cli": cisco.neighbors.handlers.cisco_ios_neighbor_handler
        },
        "types": [".*cisco.*"]
    },
    {
        "handlers": {
           "cli": hp.neighbors.handlers.hp_neighbor_handler
        },
        "types": [".*hp.*"]
    }
]


class neighbor_device:
    """
    common.neighbors.neighbor_device is used to contain all the attribute
    infomation for a device neighbor found on a host. The attribute
    information is normalized between CDP and LLDP.
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
        """
        common.neighbors.neighbor_device.__call__ returns a clean (JSON
        serializable) dict of values to make this object easier to use.
        """
        data = {}
        for attribute in self.__dict__:
            data.update({attribute: self.__dict__[attribute].Value})
        return data

    class neighbor_attribute:
        """
        common.neighbors.neighbor_device.neighbor_attribute is a simple
        namespace object which contains a consistent value set for each
        neighbor attribute. A copy of this object is instantiated for each
        attribute for each neighbor instantiated.
        """
        def __init__(self, Value=None, LLDP_TLV_Type=None, LLDP_TLV_Name=None,
                     CDP_TLV_Type=None, CDP_TLV_Name=None, Description=None):
            self.Value = Value
            self.LLDP_TLV_Type = LLDP_TLV_Type
            self.LLDP_TLV_Name = LLDP_TLV_Name
            self.CDP_TLV_Type = CDP_TLV_Type
            self.CDP_TLV_Name = CDP_TLV_Name
            self.Description = Description


# common.neighbors.allowed_attributes is a list of attributes existing
#  in a standard neighbor object. It is used to check filter expressions
#  and reject any with non-existent attributes defined.
allowed_attributes = list(neighbor_device().__dict__)


def build_neighbor_filters(inputs):
    """
    common.neighbors.build_neighbor_filters interprets and parsees user-input
    neighbor filter expressions. Filter expressions are a string in the format
    of ATTRIBUTE:REGEX. Expressions can be combined with AND logic using the
    delineator '%'. The colon and percent sign delineators can be changed
    using a double-dash:
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
 Parsing filter expressions: %s" % inputs)
    result = []
    if not inputs:  # If there were no input expressions
        return result
    else:
        # Use the common.expressions library to turn the expressions into a
        #  a list of lists so filter inputs can be found by positions
        #  relative to the provided delineators ("-", ":", "%").
        exp_data = expressions.parse_expression(inputs, ["-", ":", "%"])
        # Process each returned expression item as a file or string
        for response in exp_data:
            if response["type"] == "string":
                fltr = _process_string_exps(response["value"])
                # Discard filter if it is empty
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
    """
    common.neighbors._process_file_exps accepts pre-parsed file data from
    the common.expressions library and searches them for filter information.
    """
    def _normalize(flt_dict):
        """
        common.neighbors._process_file_exps._normalize checks through a
        expression-parsed filter dict for the required keys, checks that the
        filter value is a legitimate regular expression, and returns a
        normalized filter dict if it checks out.
        """
        attribute = None
        regex = None
        # If both required keys are in the filter dict
        if "attribute" in flt_dict and "regex" in flt_dict:
            attribute = flt_dict["attribute"]
            # Check the allowed attributes and discard if not allowed
            if attribute not in allowed_attributes:
                log.warning("common.neighbors._process_file_exps:\
 Illegal attribute (%s). Discarding expression. Allowed attributes are: %s" %
                            (attribute, " ".join(allowed_attributes)))
                return None
            else:
                regex = str(flt_dict["regex"])
                # Try to compile the filter value in case it is malformed
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
    # If an entry is a flat dictionary, then check for interesting values
    if type(file_data) == dict:
        norm_flt = _normalize(file_data)
        if norm_flt:
            result.append(norm_flt)
        else:
            return None
    # If an entry is a list, then check each entry for interesting values
    elif type(file_data) == list:
        for entry in file_data:
            norm_flt = _normalize(entry)
            if norm_flt:
                result.append(norm_flt)
            else:
                return None
    return result


def _process_string_exps(str_list):
    """
    common.neighbors._process_string_exps accepts pre-parsed string data
    from the common.expressions library and pulls attribute, and regex value
    information from the list of lists based on position.
    """
    result = []
    for entry in str_list:
        # Each filter expression must have an attribute and a regex value. If
        #  it does not contain both, then discard it.
        if len(entry) < 2:
            log.debug("common.neighbors._process_string_exps:\
 Discarding filter expression (%s). No regex found in entry (%s)" %
                      (str_list, entry))
            return None
        # Check the allowed attributes and discard if not allowed
        elif entry[0] not in allowed_attributes:
            log.warning("common.neighbors._process_string_exps:\
 Illegal attribute (%s). Discarding expression. Allowed attributes are: %s" %
                        (entry[0], " ".join(allowed_attributes)))
        else:
            regex = str(entry[1])
            # Try to compile the filter value in case it is malformed
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
    common.neighbors.filter_neighbor_device run a neighbor_device instance
    through neighbor filters (from build_neighbor_filters) and returns True
    if instance matches the filter criteria.
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
        return True  # Don't filter the device and let it through
    # Parse one filter set at a time since we use OR logic between filter-sets
    #  and use AND logic within a filter-set.
    for filter_set in filters:
        log.debug(
            "common.neighbors.filter_neighbor_device:\
 Processing Filter Set (%s)" % filter_set)
        set_results = []  # Used to store result from all filters in the set
        for flter in filter_set:
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Processing Filter (%s)" % flter)
            matched = False  # Initialize as False. Will trip if matched
            if neighbor()[flter["attribute"]]:  # If there is a value there
                # For each string in the list from
                #  common.neighbors.neighbor_device.neighbor_attribute.Value
                for value in neighbor()[flter["attribute"]]:
                    findings = re.findall(
                        flter["regex"],
                        value)
                    log.debug(
                        "common.neighbors.filter_neighbor_device:\
 Regex search returned: %s" %
                        str(findings))
                    # If anything at all came back from the regex search
                    if findings:
                        matched = True
            # Add to set_results so we can bulk check for a fail since we are
            #  using AND logic within a filter set
            set_results.append(matched)
        if False in set_results:
            # Then the neighbor failed this filter-set, but we don't return
            #  False yet because another filter set may fully pass
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Neighbor FAILED this filter")
        else:
            # If all set_results are True, then return True since this
            #  neighbor fully passed through this filter-set
            log.debug(
                "common.neighbors.filter_neighbor_device:\
 Neighbor PASSED this filter. Returning True")
            return True
    # If we haven't had a filter-set return True yet, then the neighbor didn't
    #  pass any filters and gets blocked
    log.debug(
        "common.neighbors.filter_neighbor_device:\
 All filters failed. Returning False")
    return False
