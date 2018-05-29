
import os
import sys
import json
import logging
sys.path.append(os.pardir)  # Add parent directory to path
print("\nAdded (%s) to path" % os.pardir)
from shell_tools import credentials_class
print("Imported credentials_class\n\n")


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


#######################################


log = logging.getLogger("shared")
log.setLevel(logging.DEBUG)
# log.addHandler(logging.StreamHandler())  # Enable logging

#######################################


tests = [
    {
        "input_data": [
            "admin:password123"
            ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "password123",
                "device_type": "cisco_ios",
            }
        ],
        "type": "string"
    },
    {
        "input_data": [
            "admin:password123:enablepass123"
        ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "enablepass123",
                "device_type": "cisco_ios",
            }
        ],
        "type": "string"
    },
    {
        "input_data": [
            "admin:password123:enablepass@cisco_test"
            ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "enablepass",
                "device_type": "cisco_test",
            }
        ],
        "type": "string"
    },
    {
        "input_data": [
            ";$--admin;password123;enablepass$cisco_test"
            ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "enablepass",
                "device_type": "cisco_test",
            }
        ],
        "type": "string"
    },
    {
        "input_data": [
            ";$--admin;password123;enablepass$cisco_test",
            "admin2:password321@cisco_test2"
            ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "enablepass",
                "device_type": "cisco_test",
            },
            {
                "username": "admin2",
                "password": "password321",
                "secret": "password321",
                "device_type": "cisco_test2",
            }
        ],
        "type": "string"
    },
    {
        "comment": "##### First file test. One file, one entry",
        "input_data": [
            {
                "filename": "something.json",
                "data": {
                    "username": "admin",
                    "password": "password123"
                }
            }
        ],
        "expect": [
            {
                "username": "admin",
                "password": "password123",
                "secret": "enablepass",
                "device_type": "cisco_test",
            },
            {
                "username": "admin2",
                "password": "password321",
                "secret": "password321",
                "device_type": "cisco_test2",
            }
        ],
        "type": "file"
    }
]


run_tests(tests)
