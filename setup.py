#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

with open("README.md", "r") as readme:
    long_description = readme.read()
    readme.close()

setup(name='autoshell',
      version="0.0.1",
      description='Simple, fully programmable,\
 shell-based network automation utility',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='John W Kerns',
      author_email='jkerns@packetsar.com',
      url='https://github.com/PackeTsar/autoshell',
      packages=find_packages(),
      install_requires=[
          'future',
          'netmiko'
      ]
      )
