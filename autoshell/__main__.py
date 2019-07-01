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
from . import modules
from . import __version__

# --- Start all three logging systems
# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")
# datalog is used only to output parsable JSON data
datalog = logging.getLogger("data")
# modlog is used for logging inside of user-written modules
modlog = logging.getLogger("modules")


# Logging initial setup. More setup is done in autoshell.start_logging
#  after arg processing
consoleHandler = logging.StreamHandler()
# Standard format for informational logging
format = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
# Standard format used for console (non-std.out) output
consoleHandler.setFormatter(format)
# Console output (non-std.out) handler used on log, modlog, and paramiko
log.addHandler(consoleHandler)


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
        args.credentials)
    connector_dict = {}  # Storage of host connectors (CLI, NetCONF, etc..)
    for name in connectors.__dict__:
        # Exclude anything in __dict__ with an underscore (like "__doc__")
        if name[0] != "_":
            connector_dict.update({name: connectors.__dict__[name]})
    # Check timeout argument to see if it was set
    if not args.timeout:
        args.timeout = 30
    # Instantiate hosts with credentials and connectors, no host addresses yet
    hosts_instance = common.hosts.hosts_class(credentials,
                                              connector_dict,
                                              args.timeout)
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
    hosts_instance.load(args.addresses)
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


def import_modules(startlogs, parser, config_file_data):
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
    module_names = []  # List of modules names
    # ##### Find modules from args and import them ######
    index = 0  # For keeping track of which arg word we are on
    for word in sys.argv:
        # If we see "-m" or "--module" as an arg and there is a word after it
        if (word == "-m" or word == "--module") and len(sys.argv) > index + 1:
            module_names.append(sys.argv[index + 1])
        index += 1
    if "modules" in config_file_data:
        if type(config_file_data["modules"]) == list:
            module_names = module_names + config_file_data["modules"]
        elif type(config_file_data["modules"]) == str:
            module_names.append(config_file_data["modules"])
        elif type(config_file_data["modules"]) == type(u""):
            # type(u"") is for Py2 unicode compatibility
            module_names.append(config_file_data["modules"])
    # ######################
    for name in module_names:
        try:
            # Check if the module is a file path
            isfile = os.path.isfile(name)
            # Check if the module is a directory path
            isdir = os.path.isdir(name)
            # If the arg was a file or directory path
            if isfile or isdir:
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.import_modules:\
 Module ({}) is a file".format(name)
                    })
                # Build the absolute path
                fullpath = os.path.abspath(name)
                # Split it into the filename and directory path
                path, filename = os.path.split(fullpath)
                # Add the directory into sys.path
                sys.path.append(path)
                # And use the filename to create the module name
                modname = filename.replace(".py", "")
            # If the args was not a file or directory path
            else:
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.import_modules:\
 Module ({}) is not a file".format(name)
                    })
                # Just use the name for the import
                modname = name
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
    # Standard format used for console (non-std.out) output
    consoleHandler.setFormatter(format)
    # Console output (non-std.out) handler used on log, modlog, and paramiko
    modlog.addHandler(consoleHandler)
    logging.getLogger("paramiko.transport").addHandler(consoleHandler)
    # std.out handler used on datalog
    datalog.addHandler(dataHandler)
    # If any logfiles were pased in the arguments
    if args.logfiles:
        if type(args.logfiles) == str or type(args.logfiles) == type(u""):
            # type(u"") is for Py2 unicode compatibility
            args.logfiles = [args.logfiles]
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


def merge_args(primary_value, secondary_value):
    if primary_value is None:
        return secondary_value
    elif type(primary_value) == list:
        if type(secondary_value) == list:
            return primary_value + secondary_value
        elif type(secondary_value) == str:
            primary_value.append(secondary_value)
            return primary_value
        elif type(secondary_value) == type(u""):
            # type(u"") is for Py2 unicode compatibility
            primary_value.append(secondary_value)
            return primary_value


def get_config_files(startlogs):
    """
    autoshell.get_config_files retrieves any defined configuration files
    and returns argument data for later processing.
    """
    config_files = []  # List of interpreted config files
    config_file_data = {}
    # Find modules from args and import them ######
    index = 0  # For keeping track of which arg word we are on
    for word in sys.argv:
        # If we see "-f" or "--config_file" as an arg and there
        #   is a word after it
        if (word == "-f" or word == "--config_file") and len(
                sys.argv) > index + 1:
            # Add the entry to the list of config files
            config_files.append(sys.argv[index + 1])
        index += 1
    if not config_files:
        startlogs.append({
            "level": "debug",
            "message": "autoshell.process_config_files:\
 No config files defined"
            })
        return config_file_data
    else:
        for filename in config_files:
            # Check to see if it is a legitimate file
            if not os.path.isfile(filename):
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.process_config_files:\
 Defined config file ({}) does not exist or is not a file".format(filename)
                    })
            # If it is a file
            else:
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.process_config_files:\
 Defined config file ({}) exists. Processing...".format(filename)
                    })
                # Process it through the expressions library
                exp_output = common.expressions.parse_expression(
                    [filename], ["-", ":", "@"])
                startlogs.append({
                    "level": "debug",
                    "message": "autoshell.process_config_files:\
 Config file ({}) interpreted by common.expressions:\
 \n{}".format(filename, json.dumps(exp_output, indent=4))
                    })
                # exp_output should be a list of results with one entry
                if exp_output:
                    if type(exp_output[0]["value"]) != dict:
                        startlogs.append({
                            "level": "error",
                            "message": "autoshell.process_config_files:\
 Config file ({}) must be a dictionary type! Discarding".format(filename)
                            })
                    else:
                        for key in exp_output[0]["value"]:
                            # If the key doesnt exist yet
                            if key not in config_file_data:
                                # Add it in with the value
                                config_file_data.update(
                                    {key: exp_output[0]["value"][key]})
                            else:  # If the key does exist
                                # Merge the values together
                                newval = merge_args(
                                    config_file_data[key],
                                    exp_output[0]["value"][key])
                                # If we got something from the merge
                                if newval:
                                    # Replace the value with it
                                    config_file_data[key] = newval
        return config_file_data


def process_config_files(startlogs, args, add_data):
    """
    autoshell.process_config_files takes key/value data and adds it to args
    from argparser using the merge_args function.
    """
    for key in add_data:
        # If the key does not exist as an argument at all
        if key not in list(args.__dict__):
            # Add it as a new attribute
            args.__dict__.update({key: add_data[key]})
        # If the key does exist as an argument
        else:
            newval = merge_args(
                args.__dict__[key],
                add_data[key])
            # If we got something from the merge
            if newval:
                # Replace the value with it
                args.__dict__[key] = newval


def check_args(parser, args):
    """
    autoshell.check_args checks for the existence of at least one argument
    from the command-line. If there are no arguments provided, we will print
    the help menu.
    """
    for key in args.__dict__:
        # If there is a value
        if args.__dict__[key]:
            # Then return back to start()
            return None
    # If we didn't return, then print help and quit
    parser.print_help()
    sys.exit()


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
    # Process any defined config files; prepare to add to args
    config_file_data = get_config_files(startlogs)
    # Pull a list of modules from user-provided arguments
    imp_modules = import_modules(startlogs, parser, config_file_data)
    # Generate a list of bundled modules to show in -v
    bundled_mods = []
    for mod in dir(modules):
        # If it is not private
        if mod[0] != "_":
            # Append it to the list
            bundled_mods.append(mod)
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
                        version="AutoShell {}\n\
    Bundled Modules: {}\n\
Python: {}\n\
Netmiko: {}\n\
    Netmiko Platforms:\n        {}".format(
                            __version__.version,
                            " ".join(bundled_mods),
                            sys.version.replace("\n", "\n    "),
                            connectors.cli.netmiko.__version__,
                            "\n        ".join(connectors.cli.netmiko.platforms)))
    required.add_argument(
                        'addresses',
                        help="""Target hosts (strings or files) (positional)'
    Examples:
        Use a file:       'myhosts.txt'
        Use IP w/ type:   '192.168.1.1@cisco_ios'
        Use IPs w/o type: '192.168.1.1 192.168.1.2'
        Use file and IP:  'myhosts.txt 192.168.1.1'""",
                        metavar='FILE/HOST_ADDRESS',
                        nargs='*')
    optional.add_argument(
                        '-f', "--config_file",
                        help="""JSON/YAML file containing\
 key/value pairs for Autoshell arguments""",
                        metavar='CONFIG_FILE',
                        dest="config_file",
                        action="append")
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
                        dest="credentials",
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
                        '-t', "--timeout",
                        help="Set timeout for SSH session (in seconds)",
                        metavar='TIMEOUT',
                        type=int,
                        dest="timeout")
#    optional.add_argument(
#                        '-dt', "--default_type",
#                        help="""Define default host type(s) (Experimental)
#    Examples:
#        '-t cisco_ios'
#            - Disables autodiscovery and uses 'cisco_ios'
#        '-t :cisco_ios'
#            - Uses 'cisco_ios' if autodiscovery fails""",
#                        metavar='TYPE',
#                        dest="default_type")
    args = parser.parse_args()
    # Add any arguments found in config files to args
    process_config_files(startlogs, args, config_file_data)
    # Set up the logging facilities, which will dump in the startlogs
    start_logging(startlogs, args)
    # Output all the parsed arguments for debugging
    log.debug("autoshell.start: \n###### INPUT ARGUMENTS #######\n" +
              json.dumps(args.__dict__, indent=4) +
              "\n##############################\n")
    # Check for arguments. If none were provided, print help and quit
    check_args(parser, args)
    try:
        # Execute main() with ability to catch user interrupts for an exit
        main(args, imp_modules)
    except KeyboardInterrupt:
        log.warning("autoshell.start:\
 Exiting AutoShell program due to user-intervention")
        sys.exit()


if __name__ == "__main__":
    start()
