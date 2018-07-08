#!/usr/bin/python

"""
The common.credentials library contains classes and functions used for parsing
user-provided expressions into credentials using direct-string-input, files,
or even retrieving information directly from the CLI.
"""


# Built-In Libraries
import os
import json
import yaml
import getpass
import logging
from builtins import input

# Autoshell Libraries
from . import expressions


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


def parse_credentials(inputs):
    """
    common.credentials.parse_credentials is the externally called function
    which accepts a list of input expressions and parses those expressions
    to either find a file being referenced (and parse credentials from it),
    or parse the expression itself as a credential. If the input is empty,
    parse_credentials will query the CLI directly for credentials.
    """
    log.debug("common.credentials.parse_credentials:\
 Parsing inputs:\n%s" % json.dumps(inputs, indent=4))
    if not inputs:
        # If an empty input exists, prompt the CLI for credentials
        result = [_add_cred_ui()]
        log.debug("common.credentials.parse_credentials:\
 Returning:\n%s" % json.dumps(result, indent=4))
        return result
    else:
        # If the input has data, parse those data as expressions
        result = _add_cred_exp(inputs)
        log.debug("common.credentials.parse_credentials:\
 Returning:\n%s" % json.dumps(result, indent=4))
        return result


def _add_cred_exp(inputs):
    """
    common.credentials._add_cred_exp parses inputs as expressions using the
    common.expressions library, then it processes each response as a string
    or as a file to find credentials.
    """
    result = []
    # Use the common.expressions library to turn the expressions into a
    #  a list of lists so credential inputs can be found by positions
    #  relative to the provided delineators ("-", ":", "@").
    for response in expressions.parse_expression(inputs, ["-", ":", "@"]):
        if response["type"] == "string":
            result.append(_process_string_exps(response["value"]))
        if response["type"] == "file":
            for cred in _process_file_exps(response["value"]):
                result.append(cred)
    return result


def _process_file_exps(file_data):
    """
    common.credentials._process_file_exps accepts pre-parsed file data from
    the common.expressions library and searches them for credential
    information.
    """
    def _normalize(cred_dict):
        """
        common.credentials._process_file_exps._normalize checks through a
        dictionary for credential keys and normalizes the output so all
        interesting keys and always provided and values can be predictably
        shared between keys (like password and secret).
        """
        ctype = None  # Initialize as none in case not found in entry
        # If no username, then entry is invalid
        if "username" not in cred_dict:
            return None
        else:
            # Share username with password and secret
            username = cred_dict["username"]
            password = cred_dict["username"]
            secret = cred_dict["username"]
        if "password" in cred_dict:
            # Share password with secret
            password = cred_dict["password"]
            secret = cred_dict["password"]
        if "secret" in cred_dict:
            secret = cred_dict["secret"]
        # Set type if it is found in entry
        if "type" in cred_dict:
            ctype = cred_dict["type"]
        return {
            "username": username,
            "password": password,
            "secret": secret,
            "type": ctype,
        }
    result = []
    # If an entry is a flat dictionary, then check for interesting values
    if type(file_data) == dict:
        norm_cred = _normalize(file_data)
        if norm_cred:
            result.append(norm_cred)
    # If an entry is a list, then check each entry for interesting values
    elif type(file_data) == list:
        for entry in file_data:
            norm_cred = _normalize(entry)
            if norm_cred:
                result.append(norm_cred)
    return result


def _process_string_exps(str_list):
    """
    common.credentials._process_string_exps accepts pre-parsed string data
    from the common.expressions library and pulls username, password, secret,
    and type information from the list of lists based on position.
    """
    if len(str_list) == 1:
        # If there is only one entry in the expression parsed by
        #  common.expressions, then there was no type defined.
        ctype = None
    else:
        # Otherwise, the type will be the first entry in the second list
        ctype = str_list[1][0]
    # If the first list has only one entry
    if len(str_list[0]) == 1:
        # Then assume it is the username and share the username with
        #  password and secret.
        return {
            "username": str_list[0][0],
            "password": str_list[0][0],
            "secret": str_list[0][0],
            "type": ctype,
        }
    # If the first list has two entries
    elif len(str_list[0]) == 2:
        # Then assume the first entry is the username and the second entry
        #  is the password. Share the password with secret.
        return {
            "username": str_list[0][0],
            "password": str_list[0][1],
            "secret": str_list[0][1],
            "type": ctype,
        }
    # If the first list has more than two entries
    elif len(str_list[0]) > 2:
        # Then assume the first entry is the username, the second entry
        #  is the password, and the third entry is the secret.
        return {
            "username": str_list[0][0],
            "password": str_list[0][1],
            "secret": str_list[0][2],
            "type": ctype,
        }


def _add_cred_ui():
    """
    common.credentials._add_cred_ui prompts the CLI for username, password,
    secret, and device type to create a credential. It follows the same logic
    as _process_file_exps and _process_string_exps for sharing values between
    credential attributes.
    """
    log.warning("common.credentials._add_cred_ui:\
 No credentials input. Getting interactively")
    # Prompt CLI for username
    username = input("Username: ")
    # Prompt CLI for password, hiding input with getpass
    password = getpass.getpass("Password: ")
    # Prompt CLI for secret (defaulting to the password), hiding input
    #  with getpass
    secret = getpass.getpass("Secret [%s]: " % ("*"*len(password),))
    # Default secret to password if nothing was entered
    if not secret:
        secret = password
    # Prompt CLI for device type (defaulting to None)
    ctype = input("Credential Type [None]: ")
    # Default type to None if nothing was entered
    if not ctype:
        ctype = None
    log.debug("""common.credentials._add_cred_ui: Set Credentials To:
            Username: %s
            Password: %s
            Enable Secret: %s
            Type: %s""" % (
                username,
                password,
                secret,
                ctype))
    cred = {
        "username": username,
        "password": password,
        "secret": secret,
        "type": ctype
    }
    return cred
