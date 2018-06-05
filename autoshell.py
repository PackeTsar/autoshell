#!/usr/bin/python


import re
import os
import sys
import time
import json
import queue
import logging
import argparse
import importlib
import threading
from builtins import input

# FIXME Remove native class dependencies on ball
# FIXME Write unit tests
# FIXME Comment Everything
# FIXME Modules: (config, cmd, cdp2desc)


class credentials_class:
    def __init__(self, credlist):
        import logging
        self.log = logging.getLogger("shared")
        self.log.debug("credentials_class.__init__: Starting")
        self._credlist = credlist
        self.creds = []
        self._override_delineator = "--"
        self._password_delineator = ":"
        self._device_type_delineator = "@"
        self.log.debug("""
            credentials_class.__init__: Default string credential delineators:
                Override Delineator: %s
                Password Delineator: %s
                Device Type Delineator: %s""" % (
                    self._override_delineator,
                    self._password_delineator,
                    self._device_type_delineator))
        if not self._credlist:
            self._add_cred_ui()
        else:
            for cred in self._credlist:
                self.log.debug("credentials_class.__init__: \
Checking credential (%s)" % cred)
                if os.path.isfile(cred):
                    self.log.debug(
                        "credentials_class.__init__: \
Credential (%s) is a file" % cred)
                    self._add_cred_file(cred)
                    self.log.debug(
                        "credentials_class.__init__: \
Credential file (%s) loaded" % cred)
                else:
                    self.log.debug(
                        "credentials_class.__init__: \
Credential (%s) is a string" % cred)
                    self._add_cred_str(cred)
                    self.log.debug(
                        "credentials_class.__init__: \
Credential string (%s) loaded" % cred)

    def _add_cred_ui(self):
        import getpass
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        secret = getpass.getpass("Secret [%s]: " % ("*"*len(password),))
        if not secret:
            secret = password
        device_type = input("Device Type [cisco_ios]: ")
        if not device_type:
            device_type = "cisco_ios"
        self.log.debug("""
            credentials_class._add_cred_str: Set Credentials To:\
                Username: %s
                Password: %s
                Enable Secret: %s
                Device Type: %s""" % (
                    username,
                    password,
                    secret,
                    device_type))
        cred = {
            "username": username,
            "password": password,
            "secret": secret,
            "device_type": device_type
        }
        self.creds.append(cred)

    def _add_cred_file(self, file):
        self.log.debug("credentials_class._add_cred_file: Opening file (%s)"
                       % file)
        f = open(file, "r")
        self.log.debug(
            "credentials_class._add_cred_file: File opened. Parsing JSON")
        raw = json.loads(f.read())
        self.log.debug(
            "credentials_class._add_cred_file: JSON Loaded. Closing file")
        f.close()
        if type(raw) == dict:
            self.log.debug(
             "credentials_class._add_cred_file: JSON is single credential")
            raw = [raw]
        else:
            self.log.debug(
             "credentials_class._add_cred_file: JSON has multiple credentials")
        # Parse
        for cred in raw:
            if "secret" not in cred:
                cred.update({"secret": cred["password"]})
            if "device_type" not in cred:
                cred.update({"device_type": "cisco_ios"})
            self.log.debug("""
            credentials_class._add_cred_file: Imported Credential:
                Username: %s
                Password: %s
                Enable Secret: %s
                Device Type: %s""" % (
                        cred["username"],
                        cred["password"],
                        cred["secret"],
                        cred["device_type"]))
            self.creds.append(cred)

    def _add_cred_str(self, string):
        self.log.debug(
            "credentials_class._add_cred_str:\
 Processing string credential (%s)" % string)
        pdel = self._password_delineator  # Set default delineator
        ddel = self._device_type_delineator  # Set default delineator
        if len(string) > 5:  # If the input is big enough
            # And we are switching delineators
            if string[2:4] == self._override_delineator:
                self.log.debug(
                    "credentials_class._add_cred_str:\
 Changing delineators for this credential")
                pdel = string[0]  # Set the new password delineator
                ddel = string[1]  # Set the new device delineator
                string = string[4:]  # Reset the input to remove the switch
                self.log.debug("""
            credentials_class._add_cred_str:\
 Set New In-String Credential Delineators:
                Password Delineator: %s
                Device Type Delineator: %s
                Stripped Credential String to Parse: %s""" % (
                            pdel,
                            ddel,
                            string))
        # Device Type
        if len(string.split(ddel)) > 1:
            device_type = string.split(ddel)[1]
            string = string.replace(ddel+device_type, "")
            self.log.debug(
                "credentials_class._add_cred_str:\
 Device type set to (%s), stripped string to (%s)" % (device_type, string))
        else:
            device_type = "cisco_ios"
            self.log.debug(
                "credentials_class._add_cred_str:\
 Device type set to default (%s)," % device_type)
        # Credentials
        cwords = string.split(pdel)
        username = cwords[0]
        if len(cwords) > 1:
            password = cwords[1]
        else:
            password = username
        if len(cwords) > 2:
            secret = cwords[2]
        else:
            secret = password
        self.log.debug("""
            credentials_class._add_cred_str:\
 Set Credentials To:
                Username: %s
                Password: %s
                Enable Secret: %s
                Device Type: %s""" % (
                    username,
                    password,
                    secret,
                    device_type))
        #########################
        self.creds.append({
            'device_type': device_type,
            'username': username,
            'password': password,
            'secret': secret
            })


class hosts_class:
    def __init__(self, hostargs):
        import commons
        log.debug(
            "hosts_class.__init__: Starting. Hosts Input:\n%s"
            % json.dumps(hostargs, indent=4))
        self._hostargs = hostargs
        self.init_hosts = self._parse_hosts(self._hostargs)
        self.connect_queue = commons.autoqueue(25, self.connect, None)
        self.hosts = []
        for host in self.init_hosts:
            self.add_host(host)
        self.connect_queue.block(kill=False)
        # for host in self.hosts:
        #     host.connect_thread.join()  # Wait for threads to term

    def _parse_hosts(self, hosts):
        result = []
        for entry in hosts:
            log.debug("hosts_class._parse_hosts: Parsing host (%s)" % entry)
            if os.path.isfile(entry):
                log.debug(
                    "hosts_class._parse_hosts: Host (%s) appears to be a file"
                    % entry)
                f = open(entry, "r")
                log.debug("hosts_class._parse_hosts: File opened")
                data = f.read()
                f.close
                if "," in data:
                    log.debug(
                        "hosts_class._parse_hosts: Splitting on commas")
                    data = data.split(",")
                else:
                    log.debug(
                        "hosts_class._parse_hosts: Splitting on newlines")
                    data = data.split("\n")
                for each in data:
                    if each != "":
                        if "@" in each:
                            words = each.split("@")
                            newhost = {"host": words[0],
                                       "device_type": words[1]}
                        else:
                            newhost = {"host": each,
                                       "device_type": None}
                        if newhost not in result:
                            log.debug(
                                "hosts_class._parse_hosts: Adding host (%s)"
                                % newhost["host"])
                            result.append(newhost)
                        else:
                            log.warning(
                                "hosts_class._parse_hosts: Duplicate host (%s)"
                                % newhost["host"])
            else:
                log.debug(
                    "hosts_class._parse_hosts: \
Host (%s) is not a file. Parsing as a string"
                    % entry)
                if "@" in entry:
                    words = entry.split("@")
                    newhost = {"host": words[0],
                               "device_type": words[1]}
                else:
                    newhost = {"host": entry,
                               "device_type": None}
                if newhost not in result:
                    result.append(newhost)
                else:
                    log.warning(
                        "hosts_class._parse_hosts: Duplicate host (%s)"
                        % newhost["host"])
        log.debug("hosts_class._parse_hosts: Completed host list:\n%s"
                  % json.dumps(result, indent=4))
        return result

    def add_host(self, hostdict):
        if not hostdict["host"]:
            log.debug(
                "hosts_class.add_host: Host is None. Skipping")
            return None
        for host in self.hosts:
            if hostdict["host"] == host.host:
                log.debug(
                    "hosts_class.add_host: Host is a duplicate. Skipping")
                return None
        log.debug("hosts_class.add_host: Adding host (%s)" % hostdict["host"])
        host = host_object(hostdict)
        self.connect_queue.put(host)
        # self.hosts.append(host)
        return host

    def disconnect_all(self):
        log.debug("hosts_class.disconnect_all: Disconnecting all hosts")
        threads = []
        for host in self.hosts:
            threads.append(host.disconnect())
        for thread in threads:
            thread.join()

    def connect(self, parent, hostobj):
        import netmiko
        log.info("hosts_class.connect: Connecting to IP (%s)"
                 % hostobj.host)
        for credential in ball.creds.creds:
            log.debug("hosts_class.connect: Assembling credential:\n%s"
                      % json.dumps(credential, indent=4))
            if hostobj.type:
                type = hostobj.type
            else:
                type = credential["device_type"]
            asmb_cred = {
                "ip": hostobj.host,
                "device_type": type,
                "username": credential["username"],
                "password": credential["password"],
                "secret": credential["secret"]
            }
            log.debug("hosts_class.connect: Trying assembled credential:\n%s"
                      % json.dumps(asmb_cred, indent=4))
            try:
                hostobj.device = netmiko.ConnectHandler(timeout=60,
                                                        **asmb_cred)
                hostobj.hostname = hostobj.device.find_prompt().replace("#",
                                                                        "")
                hostobj.hostname = hostobj.hostname.replace(">", "")
                log.info(
                    "host_object._connect: Connected to (%s) with IP (%s)"
                    % (hostobj.hostname, hostobj.host))
                hostobj.info.update({"credential": credential})
                hostobj.connected = True
                hostobj._update_info()
                hostobj.idle = True
                break
            except netmiko.ssh_exception.NetMikoTimeoutException:
                log.warning(
                    "host_object._connect: Device (%s) timed out. Discarding"
                    % hostobj.host)
                hostobj.idle = True
                hostobj.failed = True
                break
            except Exception as e:
                log.warning(
                    "host_object._connect: Device (%s) Connect Error: %s"
                    % (hostobj.host, str(e)))
                hostobj.idle = True
        if not hostobj.connected:
            hostobj.failed = True
        else:
            self.hosts.append(hostobj)


class host_object:
    def __init__(self, host):
        log.debug("host_object.__init__: Starting with host (%s)"
                  % host["host"])
        self.connected = False
        self.failed = False
        self.idle = False
        self.host = host["host"]
        self.type = host["device_type"]
        self.device = None
        self.hostname = None
        self.commands = {}
        self.info = {}

    def _update_info(self):
        self.info.update({
            "host": self.host,
            "hostname": self.hostname,
            "device_type": self.type,
        })

    def send_command(self, cmd):
        if cmd in self.commands:
            return self.commands[cmd]
        else:
            data = self.device.send_command(cmd)
            self.commands.update({cmd: data})
            return data

    def disconnect(self, thread=False):
        if not thread:
            log.debug("host_object.disconnect: Starting disconnect thread")
            thread = threading.Thread(
                target=self.disconnect,
                args=(True,))
            thread.start()
            return thread
        if self.connected:
            self.connected = False
            self.device.disconnect()
            log.info(
             "host_object.disconnect: Host (%s) with IP (%s) disconnected"
             % (self.hostname, self.host))


class ball_class:  # Container class for all shared objects
    def __init__(self):
        self.hosts = None
        self.creds = None
        self.args = None
        self.parser = None
        self.modules = []
        self.log = None
        self.datalog = None
        self.modlog = None


def run_modules():
    log.debug("run_modules: Processing imported modules")
    for module in ball.modules:
        log.debug("run_modules: Running module (%s)" % module["name"])
        module["object"].run(ball)


def main():
    log.debug("main: Starting main process")
    log.debug("main: Instantiating credentials_class")
    ball.creds = credentials_class(ball.args.creds)
    log.debug("main: Instantiating hosts_class")
    ball.hosts = hosts_class(ball.args.hostdata)
    log.info("main: Handing control to modules")
    run_modules()
    log.info("main: Modules complete. Disconnecting all hosts")
    ball.hosts.disconnect_all()
    if ball.args.dump_hostinfo:
        data = []
        for host in ball.hosts.hosts:
            if host.info:
                data.append(host.info)
        ball.datalog.info(json.dumps(data, indent=4))
    sys.exit()


def import_modules(startlogs):
    startlogs.put({
        "level": "debug",
        "message": "import_modules: Adding subdirs of (%s) to sys.path"
        % os.getcwd()
        })
    for each in os.walk(os.getcwd()):
        startlogs.put({
            "level": "debug",
            "message": "import_modules: Adding (%s) to sys.path"
            % each[0]
            })
        sys.path.append(each[0])
    startlogs.put({
        "level": "debug",
        "message": "import_modules: Starting module imports"
        })
    index = 0
    for word in sys.argv:
        if word == "-m" and len(sys.argv) > index + 1:
            try:
                module = importlib.import_module(sys.argv[index + 1])
                object = getattr(module, sys.argv[index + 1])(ball)
                ball.modules.append({
                    "name": sys.argv[index + 1],
                    "object": object})
                startlogs.put({
                    "level": "debug",
                    "message": "import_modules: Imported module (%s)" %
                    sys.argv[index + 1]
                    })
            except ImportError as e:
                startlogs.put({
                    "level": "error",
                    "message": "import_modules:\
 Error importing module (%s): %s" % (sys.argv[index + 1], e)
                    })
        index += 1
    startlogs.put({
        "level": "debug",
        "message": "import_modules: Module imports complete"
        })


def start_logging(startlogs):
    global log
    startlogs.put({
        "level": "debug",
        "message": "start_logging: Starting logger"
        })
    log = logging.getLogger("shared")
    ball.log = log
    ball.datalog = logging.getLogger("data")
    ball.datalog.setLevel(logging.INFO)
    ball.modlog = logging.getLogger("modules")
    consoleHandler = logging.StreamHandler()
    dataHandler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    format = logging.Formatter(fmt)
    consoleHandler.setFormatter(format)
    ball.log.addHandler(consoleHandler)
    ball.datalog.addHandler(dataHandler)
    ball.modlog.addHandler(consoleHandler)
    logging.getLogger("paramiko.transport").addHandler(consoleHandler)
    if ball.args.logfiles:
        for file in ball.args.logfiles:
            fileHandler = logging.FileHandler(file)
            fileHandler.setFormatter(log.handlers[0].formatter)
            log.addHandler(fileHandler)
    if not ball.args.debug:
        log.setLevel(logging.WARNING)
        ball.modlog.setLevel(logging.WARNING)
        logging.getLogger("paramiko").setLevel(logging.ERROR)
        logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
        logging.getLogger("netmiko").setLevel(logging.ERROR)
    elif ball.args.debug == 1:
        log.setLevel(logging.WARNING)
        ball.modlog.setLevel(logging.INFO)
        logging.getLogger("paramiko").setLevel(logging.ERROR)
        logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
        logging.getLogger("netmiko").setLevel(logging.ERROR)
    elif ball.args.debug == 2:
        log.setLevel(logging.INFO)
        ball.modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.ERROR)
        logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
        logging.getLogger("netmiko").setLevel(logging.ERROR)
    elif ball.args.debug == 3:
        log.setLevel(logging.DEBUG)
        ball.modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.INFO)
        logging.getLogger("paramiko.transport").setLevel(logging.INFO)
        logging.getLogger("netmiko").setLevel(logging.INFO)
    elif ball.args.debug > 3:
        log.setLevel(logging.DEBUG)
        ball.modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
        logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)
        logging.getLogger("netmiko").setLevel(logging.DEBUG)
    maps = {
           "debug": logging.DEBUG,
           "info": logging.INFO,
           "warning": logging.WARNING,
           "error": logging.ERROR,
           "critical": logging.CRITICAL
    }
    while not startlogs.empty():
        msg = startlogs.get()
        log.log(maps[msg["level"]], msg["message"])


if __name__ == "__main__":
    global ball
    ball = ball_class()
    startlogs = queue.Queue(maxsize=0)
    startlogs.put({
        "level": "debug",
        "message": "Starting Up"
        })
    ball.parser = argparse.ArgumentParser(
        description='AutoShell - A Shell-Based Automation Utility',
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False)
    misc = ball.parser.add_argument_group('Misc Arguments')
    required = ball.parser.add_argument_group('Required Arguments')
    optional = ball.parser.add_argument_group('Optional Arguments')
    import_modules(startlogs)
    startlogs.put({
        "level": "debug",
        "message": "Starting argument parsing"
        })
    misc.add_argument(
                        "-h", "--help",
                        help="show this help message and exit",
                        action="help")
    misc.add_argument(
                        "-v", "--version",
                        action="version",
                        version='%(prog)s v0.0.1')
    required.add_argument(
                        '-c', "--creds",
                        help="""Credentials (string or file)
    Examples:
        '-c admin:password123'
        '-c admin:password123:enablepass123'
        '-c admin:password123:enablepass@cisco_ios'
        '-c ;$--admin;password123;enablepass$cisco_ios'
        '-c credfile.json'""",
                        metavar='CRED_STRING/FILE',
                        dest="creds",
                        action="append")
    required.add_argument(
                        'hostdata',
                        help="""Target hosts (strings or files) (positional)'
    Examples:
        Use a file:       'myhosts.txt'
        Use IP w/ type:   '192.168.1.1@cisco_ios'
        Use IPs w/o type: '192.168.1.1 192.168.1.2'
        Use file and IP:  'myhosts.txt 192.168.1.1'""",
                        metavar='FILES/STRINGS',
                        nargs='+')
    optional.add_argument(
                        '-d', "--debug",
                        help="""Set debug level (off by default)
    Examples for debug levesl in main,modules,netmiko:
        defaults are WARNING,WARNING,ERROR
            Debug levels WARNING,INFO,ERROR:  '-d'
            Debug levels INFO,DEBUG,ERROR:  '-dd'
            Debug levels DEBUG,DEBUG,INFO:  '-ddd'
            Debug levels DEBUG,DEBUG,DEBUG: '-dddd'""",
                        dest="debug",
                        action='count')
    optional.add_argument(
                        '-m', "--module",
                        help="""Import and use an external module
    Examples:
        '-m cdpwalk'""",
                        metavar='MODULE_NAME',
                        dest="modules",
                        action="append")
    optional.add_argument(
                        '-l', "--logfile",
                        help="""File for logging output
    Examples:
        '-l /home/user/logs/mylogfile.txt'""",
                        metavar='LOGFILE_PATH',
                        dest="logfiles",
                        action="append")
    optional.add_argument(
                        '-u', "--dump_hostinfo",
                        help="Dump all host data as JSON",
                        dest="dump_hostinfo",
                        action='store_true')
    ball.args = ball.parser.parse_args()
    start_logging(startlogs)
    log.debug("\n###### INPUT ARGUMENTS #######\n" +
              json.dumps(ball.args.__dict__, indent=4) +
              "\n##############################\n")
    main()
