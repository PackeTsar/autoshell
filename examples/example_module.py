#!/usr/bin/python

"""
Welcome to the Autoshell Example Module! The code already in here is minimal
and has only the one required module function [run()]. There are other
reserved functions which expand the API integration with Autoshell;
"""


# Import the Built-in Logging library so we can log to the screen
import logging

# Import the Autoshell library since we will use Autoqueue
import autoshell


# log (modules) is used for logging inside of user-written modules. The
#  formatting and logging levels are controlled by the main Autoshell
#  program. We just have to instantiate the logger and start using it.
log = logging.getLogger("modules")


# add_parser_options() is an *OPTIONAL* function which is called by the
#  AutoShell core system when the module is initially loaded. This allows
#  external modules to add their own arguments to the core arg parser.

# add_parser_options() accepts one parameter (parser). parser is an argparse
#  object which holds all of the core and module command argument options. We
#  will want to use it to create our own argument group (so our options appear
#  seperate from core and other module arguments) and put argument options into
#  that group.
def add_parser_options(parser):
    # Create an argument group so we can distinguish this modules options from
    #  core system options or options from other modules when looking at help
    modparser = parser.add_argument_group(
        'Example Module Arguments',
        description="""\
Do something super fancy with the hosts and all these options""")
    # The -T or --text option can be used to pass in a single string value. If
    #  this option is used multiple times in the command, only the last use
    #  actually pass in a value. The default value (when not triggered) will
    #  be NULL
    modparser.add_argument(
                    # This sets the name and abbreviation which triggers this
                    #  this option. Make it something easy to remember
                    # It is good practice to always use capitalized characters
                    #  (ie: -T instead of -t) in modules for your
                    #  single-character options. The core options are all lower
                    #  case so this makes it easy to distinguish between the
                    #  two and keeps the namespace seperated.
                    '-T', "--text",
                    # Add a brief description of what this option is for and
                    #  how to use it.
                    help="A text/string option to pass in some text",
                    # The metavar helps indicate to the user what type of value
                    #  should be used after the option is triggered. This can
                    #  be anything you want but should be used to help the user
                    #  determine what to input
                    metavar='STRING',
                    # Your passed in item(s) land on the 'dest' name once the
                    #  arguments are parsed. You will be able to pull up this
                    #  value in your code later with "ball.args.text".
                    dest="text",
                    # The action setting tells the argparser how to handle
                    #  items passed in using this option. It also tells the
                    #  argparser how to validate the passed in value.
                    action='store')
    # The -S or --switch option is a simple TRUE/FALSE switch. It is set as
    #  FALSE by default and becomes TRUE when used.
    modparser.add_argument(
                    '-S', "--switch",
                    help="A simple TRUE/FALSE boolean switch",
                    dest="switch",
                    action='store_true')
    # The -L or --list option appends each item to a list. You can use this
    #  option to insert multiple items like '-L itemone -L itemtwo'. If not
    #  used/triggered, its value will be NULL by default.
    modparser.add_argument(
                    '-L', "--list",
                    help="A list option to allow multiple\
 entries to be added",
                    metavar='ITEM',
                    dest="list",
                    action="append")


# load() is an *OPTIONAL* reserved name which is called by the AutoShell core
#  system after all the command-line arguments have been parsed by arg parser.
#  This gives the module an opportunity to check all user-inputs and throw
#  errors before AutoShell continues on to connect to the hosts.

# load() accepts one parameter (ball). ball is a namespace (container) object
#  passed into the modules to give them access to all data collected and
#  organized by Autoshell before the module is called. We will use ball here
#  to access the parsed arguments and print them out using the logging system
def load(ball):
    # Insert a logging message here to let the user know (when debugging) that
    #  the load() function in this module has been called
    log.debug("example_module.load: Processing user-inputs from the argparser")
    # Logging as a warnings here so you don't have to be debugging to see
    #  the message come up.
    log.warning("example_module.load:\
 Value of 'text' argument: {}".format(ball.args.text))
    log.warning("example_module.load:\
 Value of 'switch' argument: {}".format(ball.args.switch))
    log.warning("example_module.load:\
 Value of 'list' argument: {}".format(ball.args.list))
    # If we don't like that the user didn't use -T to input some text value
    if not ball.args.text:
        # Throw a big ass error at them
        log.critical("example_module.load:\
 You forgot to use the -T option. REMEMBER NEXT TIME!!!")


# run() is the only *REQUIRED* function. It is called by the AutoShell core
#  system once (during its main run through the modules), after it has finished
#  connecting to all the hosts.

# run() accepts one parameter (ball). ball is a namespace (container) object
#  passed into the modules to give them access to all data collected and
#  organized by Autoshell before the module is called. We will use ball to
#  access all the connected SSH sessions.

# All code in the run() function is boiler-plate and does not need to be
#  modified unless you want to get fancy
def run(ball):
    # Add a debug here so we can see when our code starts being executed
    log.debug("example.run: Starting the example module")
    # Instantiate an instance of Autoqueue. Autoqueue will give us a
    #  "queue-like" object containing a pool of threads (10 in this case).
    # Each thread will pull items out of a shared queue (the items in this
    #  case will be host objects with connected SSH sessions) and feed those
    #  items to the my_function() function (which contains our code).
    # Since our code will get multi-threaded by Autoqueue, it will be greatly
    #  accelerated when being run against large numbers of hosts.
    queue = autoshell.common.autoqueue.autoqueue(10, my_function, None)
    # Loop through all the currently connected (and ready) host objects and
    #  add each one into the Autoqueue instance
    for host in ball.hosts.ready_hosts():
        queue.put(host)
    # Have Autoqueue block (pause) the main thread and wait for our code to
    #  finish processing all the hosts before continuing on with the main
    #  program.
    # You are also able to hit CRTL-C while Autoqueue is blocking to have it
    #  dump the queue and force return of control to the main thread.
    queue.block()
    # Once we finish blocking the main thread, let the user know that we are
    #  all done in this module.
    log.debug("example.run: Done! Returning control to the AutoShell core")


# my_function() is the function where you can write your code to do your
#  specific tasks. my_function() will end up getting executed in a thread by
#  the Autoqueue supervisor so any exceptions (errors) thrown in here will not
#  cause the main program to fail but will be logged to the screen.
# my_function() accepts one parameter. The object passed into that parameter
#  will be the same objects which were loaded into the queue up above.
def my_function(parent, host):
    # Log that we are starting work on this host
    log.debug("example.my_function: Starting on {}".format(host.hostname))
    # Grab the actual SSH connection object out of the passed in host
    connection = host.connections["cli"].connection
    # Do something cool...
