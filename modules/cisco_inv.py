#!/usr/bin/python

"""
cisco_inv is a bundled AutoShell module which parses the output of the
"show inventory" command and adds inventory data to host.info
"""

# Built-In Libraries
import json
import logging

# Autoshell Libraries
import commons
from cisco_generic import convert_inventory_output


class cisco_inv:
    def __init__(self, parser):
        # Instantiate logging facility for modules
        self.log = logging.getLogger("modules")

    def run(self, ball):
        # .run is the module entry point called by
        # the main program in the main thread
        self.ball = ball  # Data ball passed from main program
        self.log.info("cisco_inv.run: Starting inventory of hosts")
        # Autoqueue instance from commons
        self._queue = commons.autoqueue(10, self._get_inv, None)
        # Load all connected host_object instances into the _queue
        # self._get_inv will be fed hosts from the queue until empty
        for host in ball.hosts.active_hosts():
            self._queue.put(host)
        # Block until queue is empty and workers are idle
        self._queue.block()

    def _get_inv(self, parent, host):
        """
        worker function for cisco_inv.
        Runs the "show inventory" command on a host and parses the output
        through convert_inventory_output to get a list of dictionaries. It
        then adds the inventory data to host.info
        """
        self.log.info("cisco_inv._get_inv: Getting inventory of (%s) (%s)"
                      % (host.host, host.hostname))
        # Add empty data to avoid future parsing issues in case
        # we error out
        host.info.update({"inv": []})
        # Run command on device
        invdata = host.send_command("show inventory")
        # Parse output to get list of dictionaries
        invdata = convert_inventory_output(invdata)
        self.log.debug("cisco_inv._get_inv: Host (%s) (%s) inventory:\n%s"
                       % (host.host, host.hostname,
                          json.dumps(invdata, indent=4)))
        # Overwrite that entry with the real data
        host.info.update({"inv": invdata})
