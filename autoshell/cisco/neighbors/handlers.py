#!/usr/bin/python

"""
cisco.neighbors.handlers contains functions used for interacting with Cisco
devices to obtain LLDP and CDP neighbor information
"""

# Neighbor Libraries
from . import cli


def cisco_ios_neighbor_handler(con_instance, lldp=True, cdp=True):
    """
    cisco.neighbors.handlers.cisco_ios_neighbor_handler is an externally
    called function which accepts a common.hosts.connection_class instance,
    runs the show commands, then parses the output through the neighbor data
    scrapers to get the normalized data.
    """
    lldp_data = []  # Storage of JSON serializable LLDP neighbor data
    cdp_data = []  # Storage of JSON serializable CDP neighbor data
    if lldp:  # If we are checking LLDP
        # Send the show command to the host and parse it through
        #  the proper scraper
        lldp_data = cli.scrapers.cisco_ios_lldp_combine(
            cli.scrapers.cisco_ios_lldp_de_scraper(
                con_instance.connection.send_command(
                    "show lldp neighbors detail")),
            cli.scrapers.cisco_ios_lldp_br_scraper(
                con_instance.connection.send_command(
                    "show lldp neighbors"))
        )
    if cdp:  # If we are checking CDP
        cdp_data = cli.scrapers.cisco_ios_cdp_scraper(
            con_instance.connection.send_command(
                "show cdp neighbors detail")
        )
    # Format the data into a dict and return it
    return {
        "lldp": lldp_data,
        "cdp": cdp_data,
    }
