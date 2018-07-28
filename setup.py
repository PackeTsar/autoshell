#!/usr/bin/env python

import re
import os
import sys
from setuptools import setup
from setuptools import find_packages


# Fix for tox to run OK. Adds in path to find README and requirements files
for path in sys.path:
    if ("autoshell" in path):
        __file__ = os.path.join(re.findall(".*autoshell", path)[0],
                                "setup.py")
        home_dir = os.path.split(os.path.abspath(__file__))[0]
        break


# Add the Autoshell project directory to sys.path so we can import __version__
project_dir = os.path.join(home_dir, "autoshell")
sys.path = [project_dir] + sys.path


# Using a function to make the damn linter happy
def version():
    import __version__
    return __version__.version


with open(os.path.join(home_dir, "README.md"), "r") as readme:
    long_description = readme.read()
    readme.close()


with open(os.path.join(home_dir, "requirements.txt"), "r") as req_file:
    install_requires = []
    for package in req_file.read().split("\n"):
        if package:
            install_requires.append(package)
    req_file.close()


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Information Technology',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Natural Language :: English',
    'Operating System :: MacOS',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Internet',
    'Topic :: Utilities',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System',
    'Topic :: System :: Networking']


setup(name='autoshell',
      version=version(),
      description='Simple, fully programmable,\
 shell-based network automation utility',
      long_description=long_description,
      author='John W Kerns',
      classifiers=CLASSIFIERS,
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
