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
##   INSTALLATION   ##

### Use Autoshell Binaries (Easiest)
You can download and use the Autoshell binaries if you do not want to install the Python interpreter. This is the quickest way to start using Autoshell, but since more advanced usage of Autoshell requires you to write your own modules using Python, it is recommended that you follow the below process to install Python and PIP on your operating system, then use PIP to install Autoshell.


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
1. MacOS often comes with a native version of Python, but we likely want to upgrade that. The best way to do this is with a MacOS Linux-like package manager called [Homebrew](https://brew.sh/). You can visit the below pages to walk you through installing Homebrew and an updated Python interpreter along with it
	- [Installing Python 2 on Mac OS X](https://docs.python-guide.org/starting/install/osx/)
	- [Installing Python 3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)
2. Once Python is installed, you should be able to open Terminal, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to install Autoshell.

#### Linux
1. Install required OS packages
	- **Raspberry Pi** may need Python and PIP `sudo apt install -y python-pip` as well as `sudo apt-get install libffi-dev`
	- **Debian (Ubuntu)** distributions may need Python and PIP `sudo apt install -y python-pip`
	- **RHEL (CentOS)** distributions usually don't need any non-native packages


### Install Autoshell using PIP (Recommended)
1. Install Autoshell using pip by running the command `pip install autoshell`
2. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.



### Install Autoshell from source (Advanced)
1. Retrieve the source code repository using one of the two below methods
	- Method #1: Install a Git client (process differs depending on OS) and clone the Autoshell repository using Git `git clone https://github.com/packetsar/autoshell.git`
		- Change to the branch you want to install using `git checkout <branch_name>`
	- Method #2: Download and extract the repository files from the [Github Repo](https://github.com/PackeTsar/autoshell)
		- Make sure to download the branch you want to install
2. Move into the autoshell project directory `cd autoshell`
3. Run the setup.py file to build the package into the ./build/ directory `python setup.py build`
4. Use PIP to install the package `pip install .`
5. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.


-----------------------------------------
##   GETTING STARTED   ##
Once you have installed Autoshell, you can see the command guide with `autoshell -h`.

Since modules are able to add their own arguments into the argument parser when they are imported, you can see a module's help by importing it (ie: `-m crawl`) and then adding the `-h` argument. You can see this by trying `autoshell -m crawl -h`. In here you will see a section of argument descriptions for that module.

The simplest way to connect to a host is to point Autoshell directly at it (`autoshell 192.168.1.1`). If you do not provide credentials, it will prompt you for them. It is easy to add them inline with `-c username:password`. You are able to add as many hosts and credentials as you want and they are processed in the order you provide them.


### Credentials
Credentials can be provided to Autoshell in a few different ways:
1. At the command line as a string. The default full format for credentials is `-c <username>:<password>:<secret>@<device_type>`. This default format has optional values included. A credential string can have just one value (ie: `-c admin`) and Autoshell will use that `admin` value for the username, password, and secret; it will leave the device_type blank unless provided. You can instead provide `-c admin:password` and Autoshell will use the provided password for both the password and secret values. More examples are provided in the command help guide at the command line.
2. As a structured JSON or YAML file. You can use the [examples/example_structured_credentials_file.json](#example_structured_credentials_filejson) and [examples/example_structured_credentials_file.yml](#example_structured_credentials_fileyml) files as examples, then reference them from the command-line like `-c example_structured_credentials_file.json`. You can reference as many credential files as you want.
3. As an unstructured file. See [examples/example_unstructured_credentials.txt](#example_unstructured_credentialstxt) for an example. In the unstructured format, each line in the file will contain a credential string in the standard command-line format. You can then reference the file from the command-line like `-c example_unstructured_credentials.txt`. You can reference as many credential files as you want.




### Addresses
Addresses are provided to Autoshell at the command-line using positional arguments (without a prepended `-x` or `--xxxx` tag). You are able to provide as many addresses as you want here and they will processed in the order you give them. Below are some examples of how you can provide addresses.
1. As a simple string at the command-line. Addresses use the format of `<address>@<device_type>` where the device_type value is optional. A simple example is just using the IP address or dns-name like `192.168.1.1` or with a device_type like `192.168.1.1@cisco_ios`.
2. As a structured JSON or YAML file. You can use the [examples/example_structured_addresses_file.json](#example_structured_addresses_filejson) and [examples/example_structured_addresses_file.yml](#example_structured_addresses_fileyml) files as examples, then reference them from the command-line like `example_structured_addresses_file.json`. You can reference as many address files as you want.
3. As an unstructured file. In this format, each line in the file will contain a address string in the standard command-line format.
3. As an unstructured file. See [examples/example_unstructured_addresses_file.txt](#example_unstructured_addresses_filetxt) for an example. In the unstructured format, each line in the file will contain an address string in the standard command-line format. You can then reference the file from the command-line like `example_unstructured_addresses_file.txt`. You can reference as many address files as you want.




### Using config files
Since you may often need to define many command-line arguments, it is often easier to provide command-line arguments using a config file. You can use a structured JSON or YAML config file to define your arguments and reference the config file using `-f` or `--config_file` at the command-line. Example config files can be found in the examples/ project folder.

You can define known or unknown arguments in the config file and both will be passed into the program and into any modules you import. You can also define multiple config files which will either overwrite or append to each others settings (depending on the argument can have multiple values).

Arguments can still be defined at the command-line even when using config files. If the argument is a single value (like the debugging level) then the command-line value will overwrite any config file values. If the argument allows multiple entries (like credentials) then the command-line values will prepend any config-file values.


-----------------------------------------
##   EXAMPLE FILES   ##
Below are some example files you can use for reference. You can find these files in the `examples/` folder.


### example_structured_credentials_file.json
```
[
	{
		"username": "file_admin1",
		"password": "file_password1"
	},
	{
		"username": "file_admin2",
		"password": "file_password2"
	}
]
```

### example_structured_credentials_file.yml
```
- username: file_admin3
  password: file_password3
- username: file_admin4
  password: file_password4
```

### example_unstructured_credentials.txt
```
unst_admin1:unst_password1
unst_admin2:unst_password2@cisco_ios
```

### example_structured_addresses_file.json
```
[
	{
		"address": "192.168.1.1",
		"type": "cisco_ios"
	},
	{
		"address": "192.168.1.2"
	}
]
```

### example_structured_addresses_file.yml
```
- address: 192.168.1.1
  type: cisco_ios
- address: 192.168.1.2
```

### example_unstructured_addresses_file.txt
```
192.168.1.10
192.168.1.11@cisco_ios
```




[logo]: http://www.packetsar.com/wp-content/uploads/autoshell_logo4_100.png
