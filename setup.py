#!/usr/bin/env python

import re
import os
import sys
from setuptools import setup
from setuptools import find_packages
from autoshell import __version__

# Fix for tox to run OK. Adds in path to find README and requirements files
for path in sys.path:
    if "autoshell" in path:
        __file__ = os.path.join(re.findall(".*autoshell", path)[0],
                                "setup.py")


with open(
        # Use absolute path of README.md file
        os.path.join(
            os.path.split(os.path.abspath(__file__))[0], "README.md"),
        "r") as readme:
    long_description = readme.read()
    readme.close()
with open(
        os.path.join(
            os.path.split(os.path.abspath(__file__))[0], "requirements.txt"),
        "r") as req_file:
    install_requires = []
    for package in req_file.read().split("\n"):
        if package:
            install_requires.append(package)
    req_file.close()

setup(name='autoshell',
      version=__version__,
      description='Simple, fully programmable,\
 shell-based network automation utility',
      long_description=long_description,
      author='John W Kerns',
      author_email='jkerns@packetsar.com',
      url='https://github.com/PackeTsar/autoshell',
      license="GNU",
      packages=find_packages(),
      install_requires=install_requires,
      entry_points={
          'console_scripts': [
              'autoshell = autoshell.__main__:start'
              ]
          }
      )
