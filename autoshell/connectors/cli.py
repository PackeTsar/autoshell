#!/usr/bin/python

"""
connectors.cli
"""


# Built-In Libraries
import re
import json
import logging

# Installed Libraries
import netmiko


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


def connect(parent, con_instance, credentials, returner):
    """
    connectors.cli.connect is the worker function used to connect to
    CLI-based devices using SSH or TELNET.
    """
    if not con_instance.host.type:
        log.warning("connectors.cli.connect:\
 Host (%s) has no device_type.\
 Will use credential or try autodetection" % con_instance.address)
    elif con_instance.host.type not in netmiko.platforms:
        log.info("connectors.cli.connect:\
 Host (%s) device_type (%s) not in Netmiko platforms list. Discarding.\
 Supported platforms are: \n%s" % (con_instance.address,
                                   con_instance.host.type,
                                   " ".join(netmiko.platforms)))
        return None
    log.info("connectors.cli.connect: Connecting to address (%s)"
             % con_instance.address)
    # Create ordered list of types so we can prefer credentials with
    #  matching types if they exist.
    pref_types = [con_instance.host.type] + netmiko.platforms
    # Try each credential once they have been ordered by preference
    for credential in _order_credentials(credentials, pref_types):
        # .address attributes which came from some modules may be a list
        if type(con_instance.address) == list:
            # Iterate a copy of the list since we will be changing the value
            #  of con_instance.address as we iterate through it.
            for address in list(con_instance.address):
                # Change value of .address so it is a string if we succeed
                con_instance.address = address
                # Build Netmiko-compatible address/credential dict
                assemb_cred = _assemble_credential(con_instance, credential)
                # _execute will return True if connection is successful
                if _execute(con_instance, assemb_cred):
                    # Update .info with the original credential we used
                    con_instance.host.info["cli"].update(
                        {"original_credential": credential})
                    # If another connector has not added the host_class
                    #  instance to the returner yet
                    if con_instance.host not in returner:
                        returner.append(con_instance.host)
                    # Return to prevent trying the next credential
                    return None
        else:
            # Build Netmiko-compatible address/credential dict
            assemb_cred = _assemble_credential(con_instance, credential)
            # _execute will return True if connection is successful
            if _execute(con_instance, assemb_cred):
                # Update .info with the original credential we used
                con_instance.host.info["cli"].update(
                    {"original_credential": credential})
                # If another connector has not added the host_class
                #  instance to the returner yet
                if con_instance.host not in returner:
                    returner.append(con_instance.host)
                # Return to prevent trying the next credential
                return None


def disconnect(parent, con_instance, returner):
    """
    connectors.cli.disconnect is the worker function used to gracefully
    disconnect from CLI-based devices, then return that connection instance
    to the returner list.
    """
    # Send disconnect command to Netmiko
    con_instance.connection.disconnect()
    log.info("connectors.cli.disconnect: Disconnected from (%s) (%s)"
             % (con_instance.host.hostname, con_instance.host.address))
    returner.append(con_instance)


def _assemble_credential(con_instance, credential):
    """
    connectors.cli._assemble_credential builds a Netmiko-compatible
    address/credential set which can be passed directly to the Netmiko
    library to make the connection. _assemble_credential also sorts out the
    device_type to put in the set preferring some sources over others.
    """
    log.debug("connectors.cli._assemble_credential: Assembling credential:\n%s"
              % json.dumps(credential, indent=4))
    device_type = None  # Start with no device_type
    if con_instance.host.type:
        if con_instance.host.type not in netmiko.platforms:
            # If credential type not in Netmiko supported platforms
            log.warning("connectors.cli._assemble_credential:\
 Address (%s) device_type (%s) not in Netmiko platforms.\
 Setting device_type to None.\
 Supported platforms are: \n%s" % (con_instance.host.address,
                                   con_instance.host.type,
                                   " ".join(netmiko.platforms)))
        else:
            # Prefer the type on the con_instance over anything
            device_type = con_instance.host.type
    # If there is a type in the credential, prefer it second
    if credential["type"] and not device_type:
        if credential["type"] in netmiko.platforms:
            device_type = credential["type"]
        else:
            # If credential type not in Netmiko supported platforms
            log.warning("connectors.cli._assemble_credential:\
 Credential device_type (%s) not in Netmiko platforms.\
 Setting device_type to None.\
 Supported platforms are: \n%s" % (credential["type"],
                                   " ".join(netmiko.platforms)))
    # Prefer to autodiscover as a last resort
    if not device_type:
        device_type = "autodetect"
    # Build final assembled Netmiko-compatible crrdential/address set
    assembled = {
        "ip": con_instance.address,
        "device_type": device_type,
        "username": credential["username"],
        "password": credential["password"],
        "secret": credential["secret"],
        "timeout": 10
    }
    log.debug("connectors.cli._assemble_credential: Returning:\n%s"
              % json.dumps(assembled, indent=4))
    return assembled


def _execute(con_instance, credential):
    """
    connectors.cli._execute performs the connection/autodiscovery attempts
    using the Netmiko library. It returns either a True or False value to the
    caller. True if the connection was successful, False if it was not.
    """
    # Add an empty dict in case we error out before connecting
    con_instance.host.info.update({"cli": {}})
    # Expect exceptions since we now executing the connection
    try:
        if credential["device_type"] == "autodetect":
            log.debug("connectors.cli._execute:\
 Connecting to address (%s) to detect device type..." %
                      (con_instance.address, ))
            # Trip idle flag since we are working on this connection now
            con_instance.idle = False
            # Connect to device to start type detection
            device = netmiko.SSHDetect(**credential)
            # Run detection function
            dtype = device.autodetect()
            # If None was returned by the function
            if not dtype:
                log.warning("connectors.cli._execute:\
 Authentication succeeded, but Auto Detection failed on address (%s).\
 Discarding host" % (con_instance.address, ))
                # Gracefully disconnect from the host, set the failed flag
                #  to prevent further connection attempts, and reset idle
                device.connection.disconnect()
                con_instance.failed = True
                con_instance.idle = True
                return False
            # If we got a successful returned type, set the credential set
            #  type, gracefully disconnect, and allow the connection
            #  process to continue
            credential["device_type"] = dtype
            con_instance.host.type = credential["device_type"]
            device.connection.disconnect()
            log.debug("connectors.cli._execute:\
 Detected device type (%s) on address (%s)" % (credential["device_type"],
                                               con_instance.address))
        log.debug("connectors.cli._execute:\
 Trying host (%s) with credential:\n%s"
                  % (con_instance.address, json.dumps(credential, indent=4)))
        con_instance.idle = False
        # Make Netmiko connection via SSH or TELNET
        device = netmiko.ConnectHandler(**credential)
        # Detect and clean the hostname
        hostname = device.find_prompt().replace("#", "")
        hostname = hostname.replace(">", "")
        log.info(
            "connectors.cli._execute: Connected to (%s) with address (%s)"
            % (hostname, con_instance.address))
        # Set all known values on the connection instance attributes
        con_instance.type = "cli"
        con_instance.connected = True
        con_instance.idle = True
        con_instance.connection = device
        con_instance.host.hostname = hostname
        # Add the final assembled credential to .info
        con_instance.host.info["cli"].update(
            {"assembled_credential": credential})
        # Set the type on the parent host_class instance
        con_instance.host.type = credential["device_type"]
        # Return True since we successfully connected
        return True
    except netmiko.ssh_exception.NetMikoTimeoutException:
        # Exception thrown when TCP connectivity cannot establish. Set failed
        #  and return since there is no use in trying to connect with a
        #  different credential.
        log.warning(
            "connectors.cli._execute: Device (%s) timed out. Discarding"
            % con_instance.address)
        con_instance.idle = True
        con_instance.failed = True
        return False
    except netmiko.ssh_exception.NetMikoAuthenticationException:
        # Exception thrown when authentication fails. Do not set as failed
        #  since we may have another credential to try
        log.warning(
            "connectors.cli._execute: Device (%s) authentication failed"
            % con_instance.address)
        con_instance.idle = True
        return False
    except Exception as e:
        # Unexpected exception thrown. Log it and continue with next cred
        log.exception(
            "connectors.cli._execute: Device (%s) connection exception raised:"
            % con_instance.address)
        con_instance.idle = True
        return False
    # Return False here in case we fell out of above code without a return
    return False


def _order_credentials(credentials, type_order):
    """
    connectors.cli._order_credentials builds a host-specific list of
    credentials to try to attempt to log into the host. The credentials are
    ordered based on whether or not they are typed, if that type is in the
    provided type order, and where in that order the type exists. This helps
    the cli connector more effeciently determine the appropriate credential
    to log in to the host.
    """
    ordered = {}  # Credentials with an ordered type: highest pref
    unordered_untyped = []  # Credentials with an ordered type: middle pref
    unordered_typed = []  # Credentials with an ordered type: lowest pref
    for credential in credentials:
        if credential["type"]:  # If there is a type in the credential
            # And that type is in the provided ordered types
            if credential["type"] in type_order:
                # And that credential has not been added to the ordered dict
                if credential["type"] not in ordered:
                    # Start a new dict with that credential in it
                    ordered.update({credential["type"]: [credential]})
                else:
                    # Add that credential to that keyed list
                    ordered[credential["type"]].append(credential)
            else:  # If the type was not in type_order
                unordered_typed.append(credential)
        else:  # If the credential had no type
            unordered_untyped.append(credential)
    # Build a deduplicated copy of the type_order list so we don't accidently
    #  add the same credential to the final result multiple times
    type_order_dedup = []
    for ctype in type_order:
        if ctype not in type_order_dedup:
            type_order_dedup.append(ctype)
    result = []
    # Add ordered and typed credentials to the result first, in the order of
    #  the type_order provided
    for ctype in type_order_dedup:
        # If we had any credentials with that type
        if ctype in ordered:
            result += ordered[ctype]
    # Middle preference is unordered and untype credentials
    result += unordered_untyped
    # Last preference is unordered credentials which are typed
    result += unordered_typed
    return result
