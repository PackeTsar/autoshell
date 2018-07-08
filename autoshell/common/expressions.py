#!/usr/bin/python

"""
common.expressions contains functions used to parse entries from the
command-line which may contain file names (JSON or YAML) or a structured
expression which outputs two-leveled list data. Each input is checked as a file
first, if it is a file, we try to parse it as YAML and JSON. If it is not a
file then we parse it as a string with first and second order delineators.
String Examples:
 - 'one:two' will output [["one", "two"]]
 - 'one:two%three' will output as [["one", "two"], ["three"]]
Each output will be contained in a dictionary with a "type" descriptor being
"string", or "file".
"""


# Built-In Libraries
import os
import json
import yaml
import logging


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


def parse_expression(inputs, delineators):
    """
    common.expressions.parse_expression is called by the originating function
    to parse the inputs. It checks if each entry is a file or a string and
    processes accordingly.
    """
    results = []
    if not inputs:  # Return an empty result if input is empty
        return results
    for expression in inputs:
        log.debug("common.expressions.parse_expression:\
 Checking expression (%s)" % expression)
        # Check if it is a file
        if os.path.isfile(expression):
            log.debug(
                "common.expressions.parse_expression:\
 Expression (%s) is a file" % expression)
            data = _add_file(expression)
            # If empty data is returned, then don't add it to the results
            if data:
                results.append(data)
        else:
            log.debug(
                "common.expressions.parse_expression:\
 Expression (%s) is a string" % expression)
            # Parse as a string with the passed delineators
            data = _add_str(expression, delineators)
            if data:
                results.append(data)
    return results


def _add_file(file):
    """
    common.expressions._add_file will read in the file data and attempt to
    parse it as YAML. If it fails, then it will be parsed as JSON. If that
    fails, then None will be returned.
    """
    entries = []
    log.debug("common.expressions._add_file: Checking file (%s)"
              % file)
    # Pull raw file data
    f = open(file, "r")
    raw_data = f.read()
    f.close()
    # Try YAML
    if not entries:
        try:
            for each in yaml.load_all(raw_data):
                entries = each
                break
            log.debug(
                "common.expressions._add_file:\
 File (%s) contains YAML data" % file)
        except Exception as e:
            pass
    # If YAML failed, then attempt JSON
    if not entries:
        try:
            entries = json.loads(raw_data)
            log.debug(
                "common.expressions._add_file:\
 File (%s) contains JSON data" % file)
        except Exception as e:
            pass
    if entries:
        # Nest in a dict with a type descriptor
        result = {
            "type": "file",
            "value": entries
        }
        log.debug(
            "common.expressions._add_file:\
 Processing of (%s) complete. Adding to data:\n%s" %
            (file, json.dumps(result, indent=4)))
        return result
    else:
        log.debug(
            "common.expressions._add_file:\
 Processing of (%s) failed. Returning None." % file)
        return None


def _get_delineators(string, delineators):
    """
    common.expressions._get_delineators checks the expression for cues to
    change the default first and second order delineators.
    --- Example Cue: ";$--"
    --- Usage: ";$--list00;list01$list10;list11"
    If it finds that cue, it changes the delineators and strips the cue from
    the string, returning the delineators.
    """
    _override_delineator = delineators[0]
    _value_delineator = delineators[1]
    _entry_delineator = delineators[2]
    # If the input is not big enough to have a cue, then return the default
    if not len(string) > 5:
        log.debug("""common.expressions._get_delineators:\
 Using default delineators:
                Override Delineator:  %s
                Value Delineator:     %s
                Entry Delineator:     %s""" % (
                    _override_delineator,
                    _value_delineator,
                    _entry_delineator))
        return (_value_delineator, _entry_delineator, string)
    # If the override is not set, then return the default
    if string[2:4] != _override_delineator*2:
        return (_value_delineator, _entry_delineator, string)
    else:
        log.debug(
            "common.expressions._get_delineators:\
 Changing delineators for this credential")
        vdel = string[0]  # Set the new password delineator
        edel = string[1]  # Set the new device delineator
        string = string[4:]  # Reset the input to remove the switch
        log.debug("""common.expressions._get_delineators:\
 Set New In-String Expression Delineators:
                Value Delineator: %s
                Entry Delineator: %s
                Stripped Expression String to Parse: %s""" % (
                    vdel,
                    edel,
                    string))
        return (vdel, edel, string)


def _add_str(string, delineators):
    """
    common.expressions._add_str processes a string expression into a
    multi-layered list using the first and second order delineator.
    """
    log.debug(
        "common.expressions._add_str:\
 Processing string expression (%s)" % string)
    # Set delineators for this string
    valuedel, entrydel, string = _get_delineators(string, delineators)
    entries = []
    for entry in string.split(entrydel):
        values = []
        for value in entry.split(valuedel):
            values.append(value)
        entries.append(values)
    if entries:
        result = {
            "type": "string",
            "value": entries
        }
        log.debug(
            "common.expressions._add_str:\
 Processing of (%s) complete. Adding to data:\n%s" %
            (string, json.dumps(result, indent=4)))
        return result
    else:
        log.debug(
            "common.expressions._add_str:\
 Processing of (%s) failed. Returning None." % string)
        return None
