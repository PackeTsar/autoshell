#!/usr/bin/env python

import re
import os
import sys
from setuptools import setup
from setuptools import find_packages


# Fix for tox to run OK. Adds in path to find README and requirements files
for path in sys.path:
    if "autoshell" in path:
        __file__ = os.path.join(re.findall(".*autoshell", path)[0],
                                "setup.py")

# Add the Autoshell project directory to sys.path so we can import __version__
project_dir = os.path.join(
    os.path.split(os.path.abspath(__file__))[0], "autoshell")
sys.path = [project_dir] + sys.path


# Using a function to make the damn linter happy
def version():
    import __version__
    return __version__.version


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
      version=version(),
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
