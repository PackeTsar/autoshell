#!/usr/bin/python

"""
cmd is a bundled AutoShell module which allows you to enter a command at a
prompt which will be executed on all connected hosts. The output from each
host will be printed to the screen after execution.
"""


# Built-In Libraries
import logging
from builtins import input

# Autoshell Libraries
import autoshell


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
Execute commands on all connected devices"""
        )
    modparser.add_argument(
                    '-C', "--command",
                    help="Provide commands as an argument instead of being\
 prompted",
                    metavar='COMMAND',
                    dest="command",
                    action="append")


# <module_name>.run is a *REQUIRED* reserved name which is called by
#  the AutoShell core system once during its main run through the modules,
#  after it has finished connecting to all the hosts.
def run(ball):
    log.debug("cmd.run: Starting the CMD module")
    # If command(s) were provided from the shell, we don't prompt the user
    if ball.args.command:
        log.info("cmd.run:\
 Command(s) provided from core. Skipping user interaction")
        for command in ball.args.command:
            execute(ball, command)
    # Otherwise we need to prompt the user repetitively for commands
    else:
        # Use try/except to allow user to break loop with CTRL+C
        try:
            # Use a while loop to keep asking until user is done
            while True:
                command = input("cmd> ")
                execute(ball, command)
        except KeyboardInterrupt:
            log.warning("cmd.run:\
 User interrupt detected. Returning control to the AutoShell core")


def execute(ball, command):
    log.info("cmd.execute: Executing command ()")
    queue = autoshell.common.autoqueue.autoqueue(10,
                                                 cmd,
                                                 (command, ))
    for host in ball.hosts.ready_hosts():
        queue.put(host)
    queue.block()


def wrap_output(host, output):
    header = "############ {} ({}) ############".format(host.hostname,
                                                        host.get_address())
    liner = "#"*len(header)
    trailer = liner + "\n" + liner
    return "\n".join(["\n\n", header, liner, output, liner, liner, "\n\n"])


def cmd(parent, host, command):
    """
    cmd.cmd is the worker function for cmd.
    """
    connection = host.connections["cli"].connection
    output = connection.send_command(command)
    datalog.info(wrap_output(host, output))
