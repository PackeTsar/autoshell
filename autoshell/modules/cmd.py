#!/usr/bin/python

"""
cmd is a bundled AutoShell module which allows you to enter a command at a
prompt which will be executed on all connected hosts. The output from each
host will be printed to the screen after execution.
"""


# Built-In Libraries
import os
import json
import logging
import datetime
import readline
from builtins import input

# Autoshell Libraries
import autoshell

# Installed Libraries
from jinja2 import Template


# log (shared) is used for logging inside of user-written modules
log = logging.getLogger("modules")

# datalog is used only to output informatted data
datalog = logging.getLogger("data")


# <module_name>.add_parser_options is an *OPTIONAL* reserved name which is
#  called by the AutoShell core system when the module is initially loaded.
#  This allows external modules to add their own arguments to the core
#  arg parser.
def add_parser_options(parser):
    """
    cmd.add_parser_options adds all our cmd-specific arguments to our own
    argument group. It gets called immediately after the import of the module.
    """
    modparser = parser.add_argument_group(
        'Cmd Arguments',
        description="""\
Execute commands on all connected hosts. Shell will be prompted
   for commands by default"""
        )
    modparser.add_argument(
                    '-C', "--command",
                    help="Provide commands as an argument instead\
 of being prompted",
                    metavar='COMMAND',
                    dest="command",
                    action="append")
    modparser.add_argument(
                    '-O', "--output_file",
                    help="Write output from all hosts\
 to the same file",
                    metavar='PATH',
                    dest="output_file",
                    action="append")
    modparser.add_argument(
                    '-P', "--per_host_output_file",
                    help="Write output from each host\
 to a unique output file using Jinja2",
                    metavar='JINJA2_PATH',
                    dest="per_host_output_file",
                    action="append")


# <module_name>.run is a *REQUIRED* reserved name which is called by
#  the AutoShell core system once during its main run through the modules,
#  after it has finished connecting to all the hosts.
def run(ball):
    log.debug("cmd.run: Starting the CMD module")
    if not ball.hosts.ready_hosts():  # If there are no connected hosts
        log.warning("cmd.run: No connected hosts exist. Aborting CMD module")
        return None
    # Instantiate the output files
    out_files = output_files(
        ball.args.output_file,
        ball.args.per_host_output_file)
    # If command(s) were provided from the shell, we don't prompt the user
    if ball.args.command:
        log.info("cmd.run:\
 Command(s) provided from core. Skipping user interaction")
        for command in ball.args.command:
            execute(ball, command, out_files)
        out_files.close_all()
    # Otherwise we need to prompt the user repetitively for commands
    else:
        # Use try/except to allow user to break loop with CTRL+C
        try:
            # Use a while loop to keep asking until user is done
            while True:
                command = input("cmd> ")
                if command:
                    execute(ball, command, out_files)
        except KeyboardInterrupt:
            log.warning("cmd.run:\
 User interrupt detected. Returning control to the AutoShell core")
            out_files.close_all()


class output_files:
    """
    cmd.output_files handles writing the shell output from hosts into
    statically or dynamically (Jinja2) named file paths.
    """
    def __init__(self, output_file_list, per_host_output_file_list):
        self._output_file_list = output_file_list  # Static filepath list
        # Dynamic (Jinja2) filepath list
        self._per_host_output_file_list = per_host_output_file_list
        # Maps host objects to a list of file objects
        # Used to list the output files assigned to a particular host
        self._host_map = {}
        # Maps file paths to a list of file objects
        # Used to keep track of all opened files and not open one twice
        self._file_map = {}

    def _build_host_files(self, host):
        """
        cmd.output_files._build_host_files uses the user-input output file
        paths combined with information from a connected host (and host.info
        when generating per-host files) to generate a list of file objects
        which should be assigned to a particular host, returning that list
        """
        file_list = []  # List of file objects to be assigned to this host
        if self._output_file_list:  # If there are static filepaths
            for filepath in self._output_file_list:  # Iterate them
                # Use _get_file to look up the correct existing file or
                #    to create a new one
                newfile = self._get_file(filepath)
                if newfile:  # Just in case _get_file could not create the file
                    file_list.append(newfile)  # Add to the list
        if self._per_host_output_file_list:  # If there are dynamic filepaths
            # Then iterate them
            for filepath in self._per_host_output_file_list:
                # Render the Jinja2 path from available info
                #     with _build_j2_path
                filepath = self._build_j2_path(host, filepath)
                newfile = self._get_file(filepath)
                if newfile:
                    file_list.append(newfile)
        return file_list

    def _get_file(self, filepath):
        """
        cmd.output_files._get_file checks for the existence of the
        user-provided filepath, creates directories for it if necessary, and
        creates the file, returning the object. If the file already exists, it
        will simply open the file and return the file object.
        """
        # If we didn't create this file already
        if filepath not in self._file_map:
            log.info('cmd.output_files._get_file:\
 File ({}) not in the file map yet'.format(filepath))
            try:  # Use try-except in case we have a permissions issue
                # Grab the directory path if it exists
                directory = os.path.dirname(filepath)
                if directory:  # If it does exist
                    # And the fill filepath does no already exist
                    if not os.path.exists(os.path.dirname(filepath)):
                        # Build all necessary directories
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                log.info('cmd.output_files._get_file:\
 Creating new output file ({})'.format(filepath))
                file_obj = open(filepath, "a")  # Create the file object
                # Add the file object and path to the map so we can
                #    find it later
                self._file_map.update({filepath: file_obj})
                return file_obj
            except Exception as e:
                log.exception('cmd.output_files._get_file:\
 Exception when creating file ({}):'.format(filepath))
                return None
        else:  # If we already created this file, then return the object for it
            log.debug('cmd.output_files._get_file:\
 File ({}) found in the file map. Returning it'.format(filepath))
            return self._file_map[filepath]

    def _build_j2_path(self, host, j2path):
        """
        cmd.output_files._build_j2_path uses the user-input Jinja2 string
        along with all available attributes of the host.info and the current
        datetime to generate an output file path for the individual host
        """
        log.debug('cmd.output_files._build_j2_path:\
 Processing dynamic filepath ({}) for host ({})'.format(j2path, host.hostname))
        # Initialize the Jinja2 template wit the user-input string
        template = Template(j2path)
        # Add the current date and time in case that is desired for file naming
        template.globals['now'] = datetime.datetime.now()
        # Have the host object update its .info attribute
        host.update_info()
        log.debug('cmd.output_files._build_j2_path:\
 Attributes availabe to Jinja2 for host ({}): \n{}'.format(
            host.hostname,
            json.dumps(host.info, indent=4)
                ))
        # Render and return the final file path
        filepath = template.render(host.info)
        log.debug('cmd.output_files._build_j2_path:\
 Returning ({})'.format(filepath))
        return filepath

    def write(self, host, output):
        """
        cmd.output_files.write is an external facing function used to write
        host output data to all output files assigned to a particular host
        """
        # If we have not generated the output files for this host yet
        if host not in self._host_map:
            # Add the hosts list of output files to the host map
            hostfiles = self._build_host_files(host)
            if hostfiles:
                log.debug('cmd.output_files.write:\
     Mapping host ({}) to files ({})'.format(host.hostname, hostfiles))
            self._host_map.update({host: hostfiles})
        for file in self._host_map[host]:  # For each file mapped to the host
            file.write(output)  # Write (append) the output to the file
            file.flush()  # Flush the object state to write the changes

    def close_all(self):
        """
        cmd.output_files.close_all is an external facing function used to close
        out all of the currently open files. It should be called before
        terminating the CMD module.
        """
        for filename in self._file_map:  # For each filename in the map
            log.debug('cmd.output_files.close_all:\
 Closing out file ({})'.format(filename))
            self._file_map[filename].close()  # Close out the file object


def execute(ball, command, out_files):
    log.info("cmd.execute: Executing command ({})".format(command))
    queue = autoshell.common.autoqueue.autoqueue(10,
                                                 cmd,
                                                 (command, out_files))
    for host in ball.hosts.ready_hosts():
        queue.put(host)
    queue.block()


def wrap_output(host, output, command):
    headercore = " {} ({}) ".format(host.hostname, host.get_address())
    cmdlinecore = " {} ".format(command)
    sourcelen = len(cmdlinecore)
    if len(headercore) > len(cmdlinecore):
        sourcelen = len(headercore)
    sourcelen += 10
    headside = (sourcelen-len(headercore))/2
    headside = "#"*int(headside)
    cmdside = (sourcelen-len(cmdlinecore))/2
    cmdside = "#"*int(cmdside)
    header = headside+headercore+headside
    commandline = cmdside+cmdlinecore+cmdside
    if len(commandline) < sourcelen:
        commandline += "#"*(sourcelen-len(commandline))
    if len(header) < sourcelen:
        header += "#"*(sourcelen-len(header))
    liner = "#"*sourcelen
    trailer = liner + "\n" + liner
    return "\n".join(["\n\n", header, commandline, liner, output, liner, liner, "\n\n"])


def cmd(parent, host, command, out_files):
    """
    cmd.cmd is the worker function for cmd.
    """
    connection = host.connections["cli"].connection
    output = ""
    config = False
    if command[:7] == "config:":
        config = True
        command = command[7:]
    if config:
        output += connection.config_mode()
    output += connection.send_command(command)
    if config:
        output += connection.exit_config_mode()
    wrapped_output = wrap_output(host, output, command)
    datalog.info(wrapped_output)
    out_files.write(host, wrapped_output)
