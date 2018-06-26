#!/usr/bin/python

"""
cisco_neighbor_handlers contains functions used for interacting with Cisco
devices to obtain LLDP and CDP neighbor information
"""

# Neighbor Libraries
from . import cli


def cisco_ios_neighbor_handler(con_instance, lldp=True, cdp=True):
    lldp_data = []
    cdp_data = []
    if lldp:
        lldp_data = cli.scrapers.cisco_ios_lldp_combine(
            cli.scrapers.cisco_ios_lldp_de_scraper(
                con_instance.connection.send_command("show lldp neighbors detail")),
            cli.scrapers.cisco_ios_lldp_br_scraper(
                con_instance.connection.send_command("show lldp neighbors"))
        )
    if cdp:
        cdp_data = cli.scrapers.cisco_ios_cdp_scraper(
            con_instance.connection.send_command("show cdp neighbors detail")
        )
    return {
        "lldp": lldp_data,
        "cdp": cdp_data,
    }
