# Autoshell ![Autoshell][logo]

[![Build Status](https://travis-ci.org/PackeTsar/autoshell.svg?branch=master)](https://travis-ci.org/PackeTsar/autoshell)
[![PyPI](https://img.shields.io/pypi/v/autoshell.svg)](https://pypi.python.org/pypi/autoshell)
[![Python Versions](https://img.shields.io/pypi/pyversions/autoshell.svg)](https://pypi.python.org/pypi/autoshell)


A simple, fully programmable, shell-based network automation utility


-----------------------------------------
##   VERSION   ##
The version of Autoshell documented here is: **v0.0.1**


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

Autoshell is a "shell" application in that it handles a part of the automation process, mainly parsing user arguments and connecting to hosts. It then depends on bundled and/or user-written modules to perform desired tasks on the connected hosts. Since Autoshell does the heavy lifting (connecting to devices, importing modules, sorting through credentials, providing module libraries, etc) it allows the modules to be very short and simple while making their effects quite powerful.


-----------------------------------------
##   REQUIREMENTS   ##
Interpreter: **Python 2.7+ or 3.4+**


-----------------------------------------
##   INSTALLATION   ##


### Prepare OS
#### Windows
1. If you have not yet installed Python on your Windows OS, then download and install the latest Python2 or Python3 from [Python Downloads Page](https://www.python.org/downloads/)
	- Make sure to check the box during installation which adds Python to PATH. Labeled something like `Add Python 3.7 to PATH`
2. Once Python is installed, you should be able to open a command window, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to Step 3
	- If this does not work, you will need to add the Python installation directory path to the Windows PATH variable
		- The easiest way to do this is to find the new shortcut for Python in your start menu, right-click on the shortcut, and find the folder path for the `python.exe` file
			- For Python2, this will likely be something like `C:\Python27`
			- For Python3, this will likely be something like `C:\Users\<USERNAME>\AppData\Local\Programs\Python\Python37`
		- Open your Advanced System Settings window, navigate to the "Advanced" tab, and click the "Environment Variables" button
		- Create a new system variable:
			- Variable name: `PYTHON_HOME`
			- Variable value: <your_python_installation_directory>
		- Now modify the PATH system variable by appending the text `;%PYTHON_HOME%\;%PYTHON_HOME%;%PYTHON_HOME%\Scripts\` to the end of it.
		- Close out your windows, open a command window and make sure you can run the commands `python` and `pip`




### Install Autoshell
3. Install Autoshell using pip by running the command `pip install autoshell`
4. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.






### Install from PyPi (Recommended)

Some OS distributions may need you to install Python and PIP

`sudo apt install -y python-pip`

Install Autoshell

`pip install autoshell`


### Install from Source
`pip install autoshell`


-----------------------------------------
##   GETTING STARTED   ##
Once you have installed Autoshell, you can see the command guide with `autoshell -h`.

Since modules are able to add their own arguments into the argument parser when they are imported, you can see a module's help by importing it. You can see this by trying `autoshell -m crawl -h`.


-----------------------------------------






[logo]: http://www.packetsar.com/wp-content/uploads/autoshell_logo4_100.png
