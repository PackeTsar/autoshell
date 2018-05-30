
import os
import sys
import json
import time
import logging
sys.path.append(os.pardir)  # Add parent directory to path
print("\nAdded (%s) to path" % os.pardir)
from autoshell import credentials_class
print("Imported credentials_class\n\n")


#######################################

# Logging Setup
global log
global datalog
log = logging.getLogger("shared")
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

#######################################


def run_tests(input_data):
    for each in input_data:
        if each["type"] == "string":
            print("Instantiating with '%s'" % each["input_data"])
            creds = credentials_class(each["input_data"])
            if creds.creds == each["expect"]:
                print("     - creds.creds: Pass\n")
            else:
                print("     - creds.creds: Fail")
                print("          - Expected: %s\n" % each["expect"])
                print("          - Recieved: %s\n" % creds.creds)
        else:
            filename = "test_cred_file.json"
            f = open(filename, "w")
            f.write(json.dumps(each["input_data"], indent=4))
            f.close


def run_tests(input_data):
    for test in input_data:
        cred_input = []
        del_files = []
        for cred_entry in test["input_data"]:
            if "string" in cred_entry:
                cred_input.append(cred_entry["string"])
            else:
                filename = cred_entry["file"]
                f = open(filename, "w")
                f.write(json.dumps(cred_entry["data"], indent=4))
                f.close
                del f
                cred_input.append(filename)
                del_files.append(filename)
        print("Instantiating with '%s'" % cred_input)
        creds = credentials_class(cred_input)
        if creds.creds == test["expect"]:
            print("     - creds.creds: Pass\n")
        else:
            print("     - creds.creds: Fail")
            print("          - Expected: %s\n" % each["expect"])
            print("          - Recieved: %s\n" % creds.creds)
        for filename in del_files:
            os.remove(filename)


#######################################


log = logging.getLogger("shared")
log.setLevel(logging.DEBUG)
# log.addHandler(logging.StreamHandler())  # Enable logging

#######################################


tests = [
    {
        "comment": "File and complex string entry",
        "input_data": [
            {
                "file": "test1.json",
                "data": {
                    "username": "admin1",
                    "password": "1password123"
                }
            },
            {
                "string": ";$--admin2;2password123;enablepass$cisco_test"
            },
        ],
        "expect": [
            {
                "username": "admin1",
                "password": "1password123",
                "secret": "1password123",
                "device_type": "cisco_ios",
            },
            {
                "username": "admin2",
                "password": "2password123",
                "secret": "enablepass",
                "device_type": "cisco_test",
            }
        ]
    }
]


run_tests(tests)
