# Autoshell ![Autoshell][logo]

[![Build Status](https://travis-ci.org/PackeTsar/autoshell.svg?branch=master)](https://travis-ci.org/PackeTsar/autoshell)

A simple, fully programmable, shell-based network automation utility


-----------------------------------------
##   VERSION   ##
The version of AutoShell documented here is: **v0.0.1**


-----------------------------------------
##   TABLE OF CONTENTS   ##
1. [What is Autoshell](#what-is-autoshell)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Contributing](#contributing)


-----------------------------------------
##   WHAT IS AUTOSHELL   ##
Autoshell is a Command-Line Utility and Python Library built to make quick automation tasks of a network easy.

Autoshell is a "shell" application in that it handles a part of the automation process, mainly parsing user arguments and connecting to hosts. It then depends on bundled and/or user-written modules to perform desired tasks on the connected hosts. Since Autoshell does the heavy lifting (connecting to devices, sorting through credentials, etc) it allows the modules to be very short and simple while making their effects very powerful.


-----------------------------------------
##   REQUIREMENTS   ##
Interpreter: **Python 2.7+ or 3.4+**


-----------------------------------------
##   INSTALLATION   ##

Coming Soon...


-----------------------------------------
##   GETTING STARTED   ##
Once you have installed Autoshell, you can see the command guide with `autoshell -h`.

Since modules are able to add their own arguments into the argument parser when they are imported, you can see a module's help by importing it. You can see this by trying `autoshell -m crawl -h`.


-----------------------------------------






[logo]: http://www.packetsar.com/wp-content/uploads/autoshell_100.png
