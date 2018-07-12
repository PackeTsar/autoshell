#!/usr/bin/env python

from distutils.core import setup

from autoshell import __version__

setup(name='autoshell',
      version=__version__,
      description='Simple, fully programmable,\
 shell-based network automation utility',
      author='John W Kerns',
      author_email='jkerns@packetsar.com',
      url='https://github.com/PackeTsar/autoshell',
      packages=['netmiko'],
      )
