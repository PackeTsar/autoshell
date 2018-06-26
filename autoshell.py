#!/usr/bin/python


import os
import sys
import json
import logging
import argparse
import importlib
import autoshell
try:
    import Queue as queue  # For Python2
except ModuleNotFoundError:
    import queue  # For Python3

# FIXME Remove native class dependencies on ball
# FIXME Write unit tests
# FIXME Go through and replace all % uses with .format
# FIXME Comment Everything
# FIXME -p to edit profile (timeout, threads, etc) '-p 10:25:60'
# FIXME Modules: (config, cmd, cdp2desc)


log = logging.getLogger("shared")
datalog = logging.getLogger("data")
modlog = logging.getLogger("modules")


def run_modules(modules, ball):
    log.debug("run_modules: Processing imported modules")
    for module in modules:
        log.info("run_modules: Running module (%s)" % module["name"])
        module["module"].run(ball)


def load_modules(modules, ball):
    log.debug("load_modules: Loading modules with user data")
    for module in modules:
        if "load" in module["module"].__dict__:
            log.debug("load_modules: Loading module (%s)" % module["name"])
            module["module"].load(ball)
        else:
            log.debug("load_modules:\
 Module (%s) has no 'load' function. Skipping loading." % module["name"])


def main(args, modules):
    log.debug("main: Starting main process")
    credentials = autoshell.common.credentials.parse_credentials(
        args.credential)
    connectors = {}
    for name in autoshell.connectors.__dict__:
        if name[0] != "_":
            connectors.update({name: autoshell.connectors.__dict__[name]})
    hosts_instance = autoshell.common.hosts.hosts_class(credentials,
                                                        connectors)
    ball = type('ball_class', (), dict(
        hosts=hosts_instance,
        creds=credentials,
        args=args,
        modules=modules
    ))()
    load_modules(modules, ball)
    hosts_instance.load(args.host_address)
    run_modules(modules, ball)
    hosts_instance.disconnect_all()
    if args.dump_hostinfo:
        data = []
        for host in hosts_instance.hosts:
            host.update_info()
            if host.info:
                data.append(host.info)
        datalog.info(json.dumps(data, indent=4))
    sys.exit()


def import_modules(startlogs, parser):
    # Add modules
    modules = []
    startlogs.put({
        "level": "debug",
        "message": "import_modules: Starting module imports"
        })
    if os.path.isdir("modules"):
        sys.path.append(os.path.abspath("modules"))
    else:
        parent_mod = os.path.join(os.path.abspath(os.path.pardir), "modules")
        if os.path.isdir(parent_mod):
            sys.path.append(parent_mod)
    index = 0
    for word in sys.argv:
        if word == "-m" and len(sys.argv) > index + 1:
            try:
                isfile = os.path.isfile(sys.argv[index + 1])
                isdir = os.path.isdir(sys.argv[index + 1])
                if isfile or isdir:
                    fullpath = os.path.abspath(sys.argv[index + 1])
                    path, filename = os.path.split(fullpath)
                    sys.path.append(path)
                    modname = filename.replace(".py", "")
                else:
                    modname = sys.argv[index + 1]
                module = importlib.import_module(modname)
                if "add_parser_options" in module.__dict__:
                    startlogs.put({
                        "level": "debug",
                        "message": """import_modules:\
 Module (%s) is adding arguments to the parser""" %
                        modname
                        })
                    module.add_parser_options(parser)
                modules.append({
                    "name": modname,
                    "module": module})
                startlogs.put({
                    "level": "debug",
                    "message": "import_modules: Imported module (%s)" %
                    modname
                    })
            except ImportError as e:
                startlogs.put({
                    "level": "error",
                    "message": "import_modules:\
 Error importing module (%s): %s" % (modname, e)
                    })
            except TypeError as e:
                startlogs.put({
                    "level": "error",
                    "message": "import_modules:\
 Error importing module (%s): %s" % (modname, e)
                    })
        index += 1
    startlogs.put({
        "level": "debug",
        "message": "import_modules: Module imports complete"
        })
    return modules


def start_logging(startlogs, args):
    startlogs.put({
        "level": "debug",
        "message": "start_logging: Starting logger"
        })
    datalog.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    dataHandler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    format = logging.Formatter(fmt)
    consoleHandler.setFormatter(format)
    log.addHandler(consoleHandler)
    datalog.addHandler(dataHandler)
    modlog.addHandler(consoleHandler)
    logging.getLogger("paramiko.transport").addHandler(consoleHandler)
    if args.logfiles:
        for file in args.logfiles:
            fileHandler = logging.FileHandler(file)
            fileHandler.setFormatter(log.handlers[0].formatter)
            log.addHandler(fileHandler)
    if not args.debug:
        log.setLevel(logging.WARNING)
        modlog.setLevel(logging.WARNING)
        logging.getLogger("paramiko").setLevel(logging.ERROR)
        logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
        logging.getLogger("netmiko").setLevel(logging.ERROR)
    elif args.debug == 1:
        log.setLevel(logging.WARNING)
        modlog.setLevel(logging.INFO)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
    elif args.debug == 2:
        log.setLevel(logging.INFO)
        modlog.setLevel(logging.INFO)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
    elif args.debug == 3:
        log.setLevel(logging.INFO)
        modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
    elif args.debug == 4:
        log.setLevel(logging.DEBUG)
        modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
    elif args.debug == 5:
        log.setLevel(logging.DEBUG)
        modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
    elif args.debug > 5:
        log.setLevel(logging.DEBUG)
        modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("netmiko").setLevel(logging.WARNING)
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
    startlogs = queue.Queue(maxsize=0)
    startlogs.put({
        "level": "debug",
        "message": "Starting Up"
        })
    parser = argparse.ArgumentParser(
        description='AutoShell - A Shell-Based Automation Utility',
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False)
    misc = parser.add_argument_group('Misc Arguments')
    required = parser.add_argument_group('Required Arguments')
    optional = parser.add_argument_group('Optional Arguments')
    modules = import_modules(startlogs, parser)
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
                        'host_address',
                        help="""Target hosts (strings or files) (positional)'
    Examples:
        Use a file:       'myhosts.txt'
        Use IP w/ type:   '192.168.1.1@cisco_ios'
        Use IPs w/o type: '192.168.1.1 192.168.1.2'
        Use file and IP:  'myhosts.txt 192.168.1.1'""",
                        metavar='FILE/HOST_ADDRESS',
                        nargs='+')
    optional.add_argument(
                        '-c', "--credential",
                        help="""Credentials (string or file)
    Examples:
        '-c admin:password123'
        '-c admin:password123:enablepass123'
        '-c admin:password123:enablepass@cisco_ios'
        '-c ;$--admin;password123;enablepass$cisco_ios'
        '-c credfile.json'
        '-c credfile.yml'""",
                        metavar='CRED_STRING/FILE',
                        dest="credential",
                        action="append")
    optional.add_argument(
                        '-u', "--dump_hostinfo",
                        help="Dump all host data to stdout as JSON",
                        dest="dump_hostinfo",
                        action='store_true')
    optional.add_argument(
                        '-d', "--debug",
                        help="""Set debug level (off by default)
    Examples for debug levels in main,modules,netmiko:
        defaults are WARNING,WARNING,ERROR
            Debug levels WARNING,INFO,WARNING: '-d'
            Debug levels INFO,INFO,WARNING:    '-dd'
            Debug levels INFO,DEBUG,WARNING:   '-ddd'
            Debug levels DEBUG,DEBUG,WARNING:  '-dddd'
            Debug levels DEBUG,DEBUG,INFO:     '-ddddd'
            Debug levels DEBUG,DEBUG,DEBUG:    '-dddddd'""",
                        dest="debug",
                        action='count')
    optional.add_argument(
                        '-m', "--module",
                        help="""Import and use an external module
    Examples:
        '-m crawl'
        '-m /home/user/mymodule.py'""",
                        metavar='MODULE_NAME',
                        dest="modules",
                        action="append")
    optional.add_argument(
                        '-l', "--logfile",
                        help="""File for logging output
    Examples:
        '-l /home/user/logs/mylogfile.txt'""",
                        metavar='PATH',
                        dest="logfiles",
                        action="append")
    optional.add_argument(
                        '-t', "--default_type",
                        help="""Define default host type(s) (Experimental)
    Examples:
        '-t cisco_ios'
            - Disables autodiscovery and uses 'cisco_ios'
        '-t :cisco_ios'
            - Uses 'cisco_ios' if autodiscovery fails""",
                        metavar='TYPE',
                        dest="default_type")
    args = parser.parse_args()
    start_logging(startlogs, args)
    log.debug("\n###### INPUT ARGUMENTS #######\n" +
              json.dumps(args.__dict__, indent=4) +
              "\n##############################\n")
    try:
        main(args, modules)
    except KeyboardInterrupt:
        sys.exit()
