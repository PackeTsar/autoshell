#!/usr/bin/python

"""
connector_cli
"""


# Built-In Libraries
import re
import json
import logging

# Installed Libraries
import netmiko


log = logging.getLogger("shared")


def connect(parent, con_instance, credentials, returner):
    import netmiko
    if not con_instance.host.type:
        log.warning("XXXXXXXXXXXX.cli:\
 Host (%s) has no device_type.\
 Will use credential or try autodetection" % con_instance.address)
    elif not con_instance.host.type not in netmiko.platforms:
        log.info("XXXXXXXXXXXX.cli:\
 Host (%s) device_type (%s) not in Netmiko platforms list. Discarding.\
 Supported platforms are: \n%s" % (con_instance.address,
                                   con_instance.host.type,
                                   " ".join(netmiko.platforms)))
        return None
    log.info("XXXXXXXXXXXX.cli: Connecting to address (%s)"
             % con_instance.address)
    pref_types = [con_instance.host.type] + netmiko.platforms
    for credential in _order_credentials(credentials, pref_types):
        if type(con_instance.address) == list:
            addresses = list(con_instance.address)
            for address in addresses:
                con_instance.address = address
                assemb_cred = _assemble_credential(con_instance, credential)
                if _execute(con_instance, assemb_cred):
                    con_instance.host.info["cli"].update(
                        {"original_credential": credential})
                    if con_instance.host not in returner:
                        returner.append(con_instance.host)
                    con_instance.host.address = address
                    return None
                else:
                    pass
        else:
            assemb_cred = _assemble_credential(con_instance, credential)
            if _execute(con_instance, assemb_cred):
                con_instance.host.info["cli"].update(
                    {"original_credential": credential})
                if con_instance.host not in returner:
                    returner.append(con_instance.host)
                return None
            else:
                pass


def disconnect(parent, con_instance, returner):
    con_instance.connection.disconnect()
    log.info("XXXXXXXXXXXX.cli: Disconnected from (%s) (%s)"
             % (con_instance.host.hostname, con_instance.host.address))
    returner.append(con_instance)


def _assemble_credential(con_instance, credential):
    log.debug("XXXXXXXXXXXX._assemble_credential: Assembling credential:\n%s"
              % json.dumps(credential, indent=4))
    device_type = None
    if con_instance.host.type:
        if con_instance.host.type not in netmiko.platforms:
            log.warning("XXXXXXXXXXXX.cli:\
 Address (%s) device_type (%s) not in Netmiko platforms.\
 Setting device_type to None.\
 Supported platforms are: \n%s" % (con_instance.host.address,
                                   con_instance.host.type,
                                   " ".join(netmiko.platforms)))
            device_type = None
        else:
            device_type = con_instance.host.type
    if credential["type"]:
        if credential["type"] in netmiko.platforms and not device_type:
            device_type = credential["type"]
        else:
            log.warning("XXXXXXXXXXXX.cli:\
 Credential device_type (%s) not in Netmiko platforms.\
 Setting device_type to None.\
 Supported platforms are: \n%s" % (credential["type"],
                                   " ".join(netmiko.platforms)))
            device_type = None
    else:
        device_type = None
    if not device_type:
        device_type = "autodetect"
    assembled = {
        "ip": con_instance.address,
        "device_type": device_type,
        "username": credential["username"],
        "password": credential["password"],
        "secret": credential["secret"],
        "timeout": 10
    }
    log.debug("XXXXXXXXXXXX._assemble_credential: Returning:\n%s"
              % json.dumps(assembled, indent=4))
    return assembled


def _execute(con_instance, credential):
    con_instance.host.info.update({"cli": {}})
    try:
        if credential["device_type"] == "autodetect":
            log.debug("XXXXXXXXXXXX._execute:\
 Connecting to address (%s) to detect device type..." %
                      (con_instance.address, ))
            con_instance.idle = False
            device = netmiko.SSHDetect(**credential)
            dtype = device.autodetect()
            if not dtype:
                log.warning("XXXXXXXXXXXX._execute:\
 Authentication succeeded, but Auto Detection failed on address (%s).\
 Discarding host" % (con_instance.address, ))
                device.connection.disconnect()
                con_instance.failed = True
                con_instance.idle = True
                return False
            credential["device_type"] = dtype
            con_instance.host.type = credential["device_type"]
            device.connection.disconnect()
            log.debug("XXXXXXXXXXXX._execute:\
 Detected device type (%s) on address (%s)" % (credential["device_type"],
                                               con_instance.address))
        log.debug("XXXXXXXXXXXX._execute:\
 Trying host (%s) with credential:\n%s"
                  % (con_instance.address, json.dumps(credential, indent=4)))
        con_instance.idle = False
        device = netmiko.ConnectHandler(**credential)
        hostname = device.find_prompt().replace("#", "")
        hostname = hostname.replace(">", "")
        log.info(
            "XXXXXXXXXXXX._execute: Connected to (%s) with address (%s)"
            % (hostname, con_instance.address))
        con_instance.type = "cli"
        con_instance.connected = True
        con_instance.idle = True
        con_instance.connection = device
        con_instance.host.hostname = hostname
        con_instance.host.info["cli"].update(
            {"assembled_credential": credential})
        con_instance.host.type = credential["device_type"]
        return True
    except netmiko.ssh_exception.NetMikoTimeoutException:
        log.warning(
            "XXXXXXXXXXXX._execute: Device (%s) timed out. Discarding"
            % con_instance.address)
        con_instance.idle = True
        con_instance.failed = True
        return False
    except netmiko.ssh_exception.NetMikoAuthenticationException:
        log.warning(
            "XXXXXXXXXXXX._execute: Device (%s) authentication failed"
            % con_instance.address)
        con_instance.idle = True
        return False
    except Exception as e:
        log.exception(
            "XXXXXXXXXXXX._execute: Device (%s) connection exception raised:"
            % con_instance.address)
        con_instance.idle = True
        return False
    return False


def _order_credentials(credentials, type_order):
    ordered = {}
    unordered_typed = []
    unordered_untyped = []
    for credential in credentials:
        if credential["type"]:
            if credential["type"] in type_order:
                if credential["type"] not in ordered:
                    ordered.update({credential["type"]: [credential]})
                else:
                    ordered[credential["type"]].append(credential)
            else:
                unordered_typed.append(credential)
        else:
            unordered_untyped.append(credential)
    type_order_dedup = []
    for ctype in type_order:
        if ctype not in type_order_dedup:
            type_order_dedup.append(ctype)
    result = []
    for ctype in type_order_dedup:
        if ctype in ordered:
            result += ordered[ctype]
    result += unordered_untyped
    result += unordered_typed
    return result
