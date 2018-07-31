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
2. Once Python is installed, you should be able to open a command window, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to install Autoshell.
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

#### MacOS
1. MacOS often comes with a native version of Python, but we likely want to upgrade that. The best way to do this is with a MacOS Linux-like package manager called Homebrew. You can visit the below pages to walk you through installing Homebrew and an updated Python interpreter along with it
	- [Installing Python 2 on Mac OS X](https://docs.python-guide.org/starting/install/osx/)
	- [Installing Python 3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)
2. Once Python is installed, you should be able to open Terminal, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to install Autoshell.

#### Linux
1. Install required OS packages
	- Raspberry Pi may need Python and PIP `sudo apt install -y python-pip` as well as `sudo apt-get install libffi-dev`
	- Ubuntu distributions may need Python and PIP `sudo apt install -y python-pip`
	- RHEL distributions usually don't need any non-native packages


### Install Autoshell using PIP (Recommended)
1. Install Autoshell using pip by running the command `pip install autoshell`
2. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.

### Install Autoshell from source (Advanced)
1. Retrieve the source code repository using one of the two below methods
	- Install a Git client (process differs depending on OS) and clone the Autoshell repository using Git `git clone https://github.com/packetsar/autoshell.git`
		- Change to the branch you want to install using `git checkout <branch_name>`
	- Download and extract the repository files from the [Github Repo](https://github.com/PackeTsar/autoshell)
		- Make sure to download the branch you want to install
2. Move into the autoshell project directory `cd autoshell`
3. Run the setup.py file to build the package into the ./build/ directory `python setup.py build`
4. Use PIP to install the package `pip install .`
5. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.


-----------------------------------------
##   GETTING STARTED   ##
Once you have installed Autoshell, you can see the command guide with `autoshell -h`.

Since modules are able to add their own arguments into the argument parser when they are imported, you can see a module's help by importing it. You can see this by trying `autoshell -m crawl -h`.


-----------------------------------------






[logo]: http://www.packetsar.com/wp-content/uploads/autoshell_logo4_100.png
