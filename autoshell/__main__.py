#!/usr/bin/python


# Built-In Libraries
import os
import sys
import json
import logging
import argparse
import importlib

# Autoshell Libraries
from . import cisco
from . import common
from . import connectors
from . import __version__

# --- Start all three logging systems
# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")
# datalog is used only to output parsable JSON data
datalog = logging.getLogger("data")
# modlog is used for logging inside of user-written modules
modlog = logging.getLogger("modules")


def run_modules(modules, ball):
    """
    autoshell.run_modules takes control after the initial connections
    complete. It hands control of the MainThread to each module (in order)
    a waits for return of control from each module before moving on to the
    next one.
    """
    log.debug("autoshell.run_modules: Processing imported modules")
    for module in modules:
        log.info("autoshell.run_modules: Running module (%s)" % module["name"])
        # Call the module's run() function and hand it the ball
        module["module"].run(ball)


def load_modules(modules, ball):
    """
    autoshell.load_modules briefly hands control of the MainThread to each
    module to allow it to perform checks of user-input data. This is done
    before the module is run to allow errors and warnings to be thrown
    immediately after execution of autoshell instead of having to wait until
    all the hosts are connected and the run() function is called.
    """
    log.debug("autoshell.load_modules: Loading modules with user data")
    for module in modules:
        # Check if the module has a load() function
        if "load" in module["module"].__dict__:
            log.debug("autoshell.load_modules: Loading module (%s)" %
                      module["name"])
            module["module"].load(ball)
        else:
            log.debug("autoshell.load_modules:\
 Module (%s) has no 'load' function. Skipping loading." % module["name"])


def main(args, modules):
    """
    autoshell.main is the primary execution process for autoshell; calling
    all the different autoshell libraries to assemble credentials and
    connectors, connect to the hosts, pass control to the modules, then
    disconnect from the hosts.
    """
    log.debug("autoshell.main: Starting main process")
    # Pull credentials from expressions or direct UI
    credentials = common.credentials.parse_credentials(
        args.credential)
    connector_dict = {}  # Storage of host connectors (CLI, NetCONF, etc..)
    for name in connectors.__dict__:
        # Exclude anything in __dict__ with an underscore (like "__doc__")
        if name[0] != "_":
            connector_dict.update({name: connectors.__dict__[name]})
    # Instantiate hosts with credentials and connectors, no host addresses yet
    hosts_instance = common.hosts.hosts_class(credentials,
                                                        connector_dict)
    # ball is a namespace object used to store all the main data in the program
    #  to make passing those data to modules easier.
    # Here, ball is instantiated as a simple ad-hoc namespace object instance
    ball = type('ball_class', (), dict(
        hosts=hosts_instance,
        creds=credentials,
        args=args,
        modules=modules
    ))()
    # Load all the modules with user-provided data for error checking, etc..
    load_modules(modules, ball)
    # Load the host addresses into the hosts instance, starting the
    #  process of connecting to each user-provided host using connectors
    hosts_instance.load(args.host_address)
    # After control is returned from the host instance, pass control to
    #  each module in the order in which they were input in the args
    run_modules(modules, ball)
    # Once control is returned from run_modules, gracefully disconnect from
    #  all the hosts
    hosts_instance.disconnect_all()
    # If we are to dump all the host info
    if args.dump_hostinfo:
        data = []  # Compile all host info into this list
        for host in hosts_instance.hosts:
            # Have the host update its .info var from its other attributes
            host.update_info()
            # If there is any info in .info
            if host.info:
                data.append(host.info)
        # Dump host info to datalog formatted as JSON
        datalog.info(json.dumps(data, indent=4))
    # Graceful exit for compiled versions
    sys.exit()


def import_modules(startlogs, parser):
    """
    autoshell.import_modules finds the "modules" directory and adds it into
    sys.path, then finds each module argument imports it into the program,
    and allows the modules to insert parser options. autoshell.import_modules
    then hands back a list of dictionaries containing the imported modules
    """
    modules = []  # List of dictionaries containing modules
    startlogs.append({
        "level": "debug",
        "message": "autoshell.import_modules: Starting module imports"
        })
    # ##### Add Paths ######
    # Check if we have a directory in this file's working directory
    #  named "modules"
    modules_path = os.path.join(
        os.path.split(os.path.abspath(__file__))[0], "modules")
    if os.path.isdir(modules_path):
        # If so, then add that path to the beginning of sys.path so we can
        #  import from it
        sys.path = [modules_path] + sys.path
    # ######################
    # ##### Find modules from args and import them ######
    index = 0  # For keeping track of which arg word we are on
    for word in sys.argv:
        # If we see "-m" or "--module" as an arg and there is a word after it
        if (word == "-m" or word == "--module") and len(sys.argv) > index + 1:
            try:
                # Check if the module is a file path
                isfile = os.path.isfile(sys.argv[index + 1])
                # Check if the module is a directory path
                isdir = os.path.isdir(sys.argv[index + 1])
                # If the args was a file or directory path
                if isfile or isdir:
                    # Build the absolute path
                    fullpath = os.path.abspath(sys.argv[index + 1])
                    # Split it into the filename and directory path
                    path, filename = os.path.split(fullpath)
                    # Add the directory into sys.path
                    sys.path.append(path)
                    # And use the filename to create the module name
                    modname = filename.replace(".py", "")
                # If the args was not a file or directory path
                else:
                    # Just use the name for the import
                    modname = sys.argv[index + 1]
                # Import the module by its name
                module = importlib.import_module(modname)
                # If the module has a add_parser_options() function inside
                if "add_parser_options" in module.__dict__:
                    startlogs.append({
                        "level": "debug",
                        "message": """autoshell.import_modules:\
 Module (%s) is adding arguments to the parser""" %
                        modname
                        })
                    module.add_parser_options(parser)
                # Add the module into the modules list
                modules.append({
                    "name": modname,
                    "module": module})
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.import_modules:\
 Imported module (%s)" % modname
                    })
            except ImportError as e:
                startlogs.append({
                    "level": "error",
                    "message": "autoshell.import_modules:\
 Error importing module (%s): %s" % (modname, e)
                    })
            except TypeError as e:
                startlogs.append({
                    "level": "error",
                    "message": "autoshell.import_modules:\
 Error importing module (%s): %s" % (modname, e)
                    })
        index += 1
    startlogs.append({
        "level": "debug",
        "message": "autoshell.import_modules: Module imports complete"
        })
    return modules


def start_logging(startlogs, args):
    """
    autoshell.start_logging sets up the three logging facilities (shared,
    modules, and data) with the appropriate handlers and formats, creates
    the logfile handlers if any were requested, and sets the logging levels
    based on how verbose debugging was requested to be in the args.
    """
    startlogs.append({
        "level": "debug",
        "message": "autoshell.start_logging: Starting logger"
        })
    # datalog logging level is always info as it is not used for
    #  debugging or reporting warning and errors
    datalog.setLevel(logging.INFO)
    # consoleHandler is used for outputting to the console for log and modlog
    consoleHandler = logging.StreamHandler()
    # dataHandler is used to write to std.out so the output data can be piped
    #  into other applications without being mangled by informational logs
    dataHandler = logging.StreamHandler(sys.stdout)
    # Standard format for informational logging
    format = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
        )
    # Standard format used for console (non-std.out) output
    consoleHandler.setFormatter(format)
    # Console output (non-std.out) handler used on log, modlog, and paramiko
    log.addHandler(consoleHandler)
    modlog.addHandler(consoleHandler)
    logging.getLogger("paramiko.transport").addHandler(consoleHandler)
    # std.out handler used on datalog
    datalog.addHandler(dataHandler)
    # If any logfiles were pased in the arguments
    if args.logfiles:
        for file in args.logfiles:
            # Create a handler, set the format, and apply that handler to
            #  log and modlog
            fileHandler = logging.FileHandler(file)
            fileHandler.setFormatter(format)
            log.addHandler(fileHandler)
            modlog.addHandler(fileHandler)
    # Set debug levels based on how many "-d" args were parsed
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
        logging.getLogger("paramiko").setLevel(logging.INFO)
        logging.getLogger("paramiko.transport").setLevel(logging.INFO)
        logging.getLogger("netmiko").setLevel(logging.INFO)
    elif args.debug > 5:
        log.setLevel(logging.DEBUG)
        modlog.setLevel(logging.DEBUG)
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
        logging.getLogger("paramiko.transport").setLevel(logging.DEBUG)
        logging.getLogger("netmiko").setLevel(logging.DEBUG)
    # Mappings for startlog entries to be passed properly into the log facility
    maps = {
           "debug": logging.DEBUG,
           "info": logging.INFO,
           "warning": logging.WARNING,
           "error": logging.ERROR,
           "critical": logging.CRITICAL
    }
    # Pass the startlogs into the loggin facility under the proper level
    for msg in startlogs:
        log.log(maps[msg["level"]], msg["message"])


def start():
    """
    Start up the AutoShell program by creating the parsing system, importing
    user-provided modules, parsing the arguments, setting up the logging
    facilities, and finally calling the main() function.
    """
    startlogs = []  # Logs drop here until the logging facilities are ready
    startlogs.append({
        "level": "debug",
        "message": "autoshell.start: Starting Up"
        })
    # Main arg parser for autoshell
    #  Formatter is removed to prevent whitespace loss
    #  Auto help is removed so it can be added into an argument group
    parser = argparse.ArgumentParser(
        description='AutoShell - A Shell-Based Automation Utility',
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False)
    # Misc arguments are meant for informational help-based arguments
    misc = parser.add_argument_group('Misc Arguments')
    # Required arguments are needed to start the program
    required = parser.add_argument_group('Required Arguments')
    # Optional arguments are not required for the start of the program
    optional = parser.add_argument_group('Optional Arguments')
    # Pull a list of modules from user-provided arguments
    modules = import_modules(startlogs, parser)
    startlogs.append({
        "level": "debug",
        "message": "autoshell.start: Starting argument parsing"
        })
    misc.add_argument(
                        "-h", "--help",
                        help="show this help message and exit",
                        action="help")
    misc.add_argument(
                        "-v", "--version",
                        action="version",
                        version="AutoShell v{}".format(__version__.version))
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
    # Set up the logging facilities, which will dump in the startlogs
    start_logging(startlogs, args)
    # Output all the parsed arguments for debugging
    log.debug("autoshell.start: \n###### INPUT ARGUMENTS #######\n" +
              json.dumps(args.__dict__, indent=4) +
              "\n##############################\n")
    try:
        # Execute main() with ability to catch user interrupts for an exit
        main(args, modules)
    except KeyboardInterrupt:
        log.warning("autoshell.start:\
 Exiting AutoShell program due to user-intervention")
        sys.exit()


if __name__ == "__main__":
    start()
