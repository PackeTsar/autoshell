#!/usr/bin/python

import re
import os
import sys
import json
import logging
import argparse


def make_table(columnorder, tabledata):
    ##### Check and fix input type #####
    if type(tabledata) != type([]): # If tabledata is not a list
        tabledata = [tabledata] # Nest it in a list
    ##### Set seperators and spacers #####
    tablewrap = "#" # The character used to wrap the table
    headsep = "=" # The character used to seperate the headers from the table values
    columnsep = "|" # The character used to seperate each value in the table
    columnspace = "  " # The amount of space between the largest value and its column seperator
    ##### Generate a dictionary which contains the length of the longest value or head in each column #####
    datalengthdict = {} # Create the dictionary for storing the longest values
    for columnhead in columnorder: # For each column in the columnorder input
        datalengthdict.update({columnhead: len(columnhead)}) # Create a key in the length dict with a value which is the length of the header
    for row in tabledata: # For each row entry in the tabledata list of dicts
        for item in columnorder: # For column entry in that row
            if len(re.sub(r'\x1b[^m]*m', "",  str(row[item]))) > datalengthdict[item]: # If the length of this column entry is longer than the current longest entry
                datalengthdict[item] = len(row[item]) # Then change the value of entry
    ##### Calculate total table width #####
    totalwidth = 0 # Initialize at 0
    for columnwidth in datalengthdict: # For each of the longest column values
        totalwidth += datalengthdict[columnwidth] # Add them all up into the totalwidth variable
    totalwidth += len(columnorder) * len(columnspace) * 2 # Account for double spaces on each side of each column value
    totalwidth += len(columnorder) - 1 # Account for seperators for each row entry minus 1
    totalwidth += 2 # Account for start and end characters for each row
    ##### Build Header #####
    result = tablewrap * totalwidth + "\n" + tablewrap # Initialize the result with the top header, line break, and beginning of header line
    columnqty = len(columnorder) # Count number of columns
    for columnhead in columnorder: # For each column header value
        spacing = {"before": 0, "after": 0} # Initialize the before and after spacing for that header value before the columnsep
        spacing["before"] = int((datalengthdict[columnhead] - len(columnhead)) / 2) # Calculate the before spacing
        spacing["after"] = int((datalengthdict[columnhead] - len(columnhead)) - spacing["before"]) # Calculate the after spacing
        result += columnspace + spacing["before"] * " " + columnhead + spacing["after"] * " " + columnspace # Add the header entry with spacing
        if columnqty > 1: # If this is not the last entry
            result += columnsep # Append a column seperator
        del spacing # Remove the spacing variable so it can be used again
        columnqty -= 1 # Remove 1 from the counter to keep track of when we hit the last column
    del columnqty # Remove the column spacing variable so it can be used again
    result += tablewrap + "\n" + tablewrap + headsep * (totalwidth - 2) + tablewrap + "\n" # Add bottom wrapper to header
    ##### Build table contents #####
    result += tablewrap # Add the first wrapper of the value table
    for row in tabledata: # For each row (dict) in the tabledata input
        columnqty = len(columnorder) # Set a column counter so we can detect the last entry in this row
        for column in columnorder: # For each value in this row, but using the correct order from column order
            spacing = {"before": 0, "after": 0} # Initialize the before and after spacing for that header value before the columnsep
            spacing["before"] = int((datalengthdict[column] - len(re.sub(r'\x1b[^m]*m', "",  str(row[column])))) / 2) # Calculate the before spacing
            spacing["after"] = int((datalengthdict[column] - len(re.sub(r'\x1b[^m]*m', "",  str(row[column])))) - spacing["before"]) # Calculate the after spacing
            result += columnspace + spacing["before"] * " " + str(row[column]) + spacing["after"] * " " + columnspace # Add the entry to the row with spacing
            if columnqty == 1: # If this is the last entry in this row
                result += tablewrap + "\n" + tablewrap # Add the wrapper, a line break, and start the next row
            else: # If this is not the last entry in the row
                result += columnsep # Add a column seperator
            del spacing # Remove the spacing settings for this entry 
            columnqty -= 1 # Keep count of how many row values are left so we know when we hit the last one
    result += tablewrap * (totalwidth - 1) # When all rows are complete, wrap the table with a trailer
    return result


def make_csv(columnorder, tabledata):
    result = ",".join(columnorder)
    for entry in tabledata:
        entrylist = []
        for column in columnorder:
            if column in entry:
                if not entry[column]:
                    entrylist.append("")
                else:
                    entrylist.append(entry[column])
        result += "\n" + ",".join(entrylist)
    return result


def build_inv_table(raw_data_list):
    table_data = []
    for json_entry in raw_data_list:
        data = json.loads(json_entry)
        for host in data:
            hostname = host["hostname"]
            for device in host["inv"]:
                if device != {}:
                    table_data.append({
                        "Hostname": hostname,
                        "Name": device["name"],
                        "Part Number": device["part"],
                        "Serial Number": device["serial"],
                        "Version": device["version"],
                        "Description": device["description"]
                    })
    return table_data


def main(args):
    file_data = []
    if not args.filenames:
        log.info("show_inv.main: Reading STDIN for JSON data")
        file_data.append(sys.stdin.read())
    else:
        for each_file in args.filenames:
            if os.path.isfile(each_file):
                f = open(each_file, "r")
                data = f.read()
                f.close
                file_data.append(data)
            else:
                log.ERROR("show_inv.main: Cannot open file (%s)" % each_file)
    table_data = build_inv_table(file_data)
    columns = ["Hostname", "Name", "Part Number", "Serial Number", "Version"]
    if args.dump_csv:
        datalog.info(make_csv(columns, table_data))
    else:
        datalog.info(make_table(columns, table_data))


if __name__ == "__main__":
    # Logging Setup
    global log
    global datalog
    log = logging.getLogger("debugs")
    datalog = logging.getLogger("data")
    logHandler = logging.StreamHandler()
    dataHandler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    format = logging.Formatter(fmt)
    logHandler.setFormatter(format)
    log.addHandler(logHandler)
    datalog.addHandler(dataHandler)
    log.setLevel(logging.INFO)
    datalog.setLevel(logging.INFO)
    # Parser Setup
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False)
    misc = parser.add_argument_group('misc arguments')
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    misc.add_argument(
                        "-h", "--help",
                        help="show this help message and exit",
                        action="help")
    misc.add_argument(
                        "-v", "--version",
                        action="version",
                        version='%(prog)s v0.0.1')
    required.add_argument(
                        'filenames',
                        help="File containing host info data in JSON format",
                        metavar='JSON_FILE',
                        nargs='*')
    optional.add_argument(
                        '-c', "--csv",
                        help="Dump all host data as CSV",
                        dest="dump_csv",
                        action='store_true')
    args = parser.parse_args()
    main(args)
