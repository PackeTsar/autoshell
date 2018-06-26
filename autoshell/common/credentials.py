#!/usr/bin/python

"""
The common_credentials library contains classes and functions used for finding
and storing credentials for logging into hosts
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


log = logging.getLogger("shared")


def parse_credentials(inputs):
    log.debug("common.credentials.parse_credentials:\
 Parsing inputs:\n%s" % json.dumps(inputs, indent=4))
    if not inputs:
        result = [_add_cred_ui()]
        log.debug("common.credentials.parse_credentials:\
 Returning:\n%s" % json.dumps(result, indent=4))
        return result
    else:
        result = _add_cred_exp(inputs)
        log.debug("common.credentials.parse_credentials:\
 Returning:\n%s" % json.dumps(result, indent=4))
        return result


def _add_cred_exp(inputs):
    result = []
    cred_data = expressions.parse_expression(inputs, ["-", ":", "@"])
    for response in cred_data:
        if response["type"] == "string":
            result.append(_process_string_exps(response["value"]))
        if response["type"] == "file":
            for cred in _process_file_exps(response["value"]):
                result.append(cred)
    return result


def _process_file_exps(file_data):
    def _normalize(cred_dict):
        ctype = None
        if "username" not in cred_dict:
            return None
        else:
            username = cred_dict["username"]
            password = cred_dict["username"]
            secret = cred_dict["username"]
        if "password" in cred_dict:
            password = cred_dict["password"]
            secret = cred_dict["password"]
        if "secret" in cred_dict:
            secret = cred_dict["secret"]
        if "type" in cred_dict:
            ctype = cred_dict["type"]
        return {
            "username": username,
            "password": password,
            "secret": secret,
            "type": ctype,
        }
    result = []
    if type(file_data) == dict:
        norm_cred = _normalize(file_data)
        if norm_cred:
            result.append(norm_cred)
    elif type(file_data) == list:
        for entry in file_data:
            norm_cred = _normalize(entry)
            if norm_cred:
                result.append(norm_cred)
    return result


def _process_string_exps(str_list):
    if len(str_list) == 1:
        ctype = None
    else:
        ctype = str_list[1][0]
    if len(str_list[0]) == 1:
        return {
            "username": str_list[0][0],
            "password": str_list[0][0],
            "secret": str_list[0][0],
            "type": ctype,
        }
    elif len(str_list[0]) == 2:
        return {
            "username": str_list[0][0],
            "password": str_list[0][1],
            "secret": str_list[0][1],
            "type": ctype,
        }
    elif len(str_list[0]) > 2:
        return {
            "username": str_list[0][0],
            "password": str_list[0][1],
            "secret": str_list[0][2],
            "type": ctype,
        }


def _add_cred_ui():
    log.warning("credentials_class._add_cred_file:\
 No credentials input. Getting interactively")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    secret = getpass.getpass("Secret [%s]: " % ("*"*len(password),))
    if not secret:
        secret = password
    ctype = input("Credential Type [None]: ")
    if not ctype:
        ctype = None
    log.debug(""" credentials_class._add_cred_str: Set Credentials To:
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
