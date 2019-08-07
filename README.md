# Autoshell ![Autoshell][logo]

[![Build Status](https://travis-ci.org/PackeTsar/autoshell.svg?branch=master)](https://travis-ci.org/PackeTsar/autoshell)
[![PyPI](https://img.shields.io/pypi/v/autoshell.svg)](https://pypi.python.org/pypi/autoshell)
[![Python Versions](https://img.shields.io/pypi/pyversions/autoshell.svg)](https://pypi.python.org/pypi/autoshell)


A simple, fully programmable, shell-based network automation utility

Quick Install: `pip install autoshell`

Get started fast with the **[Autoshell Tutorial](TUTORIAL-1.md)**

-----------------------------------------
##   VERSION   ##
The version of Autoshell documented here is: **0.0.29**


-----------------------------------------
##   TABLE OF CONTENTS   ##
1. [What is Autoshell](#what-is-autoshell)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Contributing](#contributing)
6. [Autoshell Tutorial](TUTORIAL-1.md)

-----------------------------------------
##   WHAT IS AUTOSHELL   ##
Autoshell is a Command-Line Utility and Python Library built to make quick automation tasks of a network easy.

Autoshell is a "shell" application in that it handles a part of the automation process, mainly parsing user arguments and connecting to hosts. It then depends on bundled and/or user-written modules to perform desired tasks on the connected hosts. Since Autoshell does the heavy lifting (connecting to hosts, importing modules, sorting through credentials, providing module libraries, etc) it allows the modules to be very short and simple while making their effects quite powerful.


-----------------------------------------
##   INSTALLATION   ##

The installation process is also covered in the **[Autoshell Tutorial](TUTORIAL-1.md)**
<!--
< ### Autoshell Binaries (Easiest)
You can download and use the Autoshell binaries if you do not want to install the Python interpreter. This is the quickest way to start using Autoshell, but since more advanced usage of Autoshell requires you to write your own modules using Python, it is recommended that you follow the below process to install Python and PIP on your operating system, then use PIP to install Autoshell.
-->

### Prepare Your OS
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
MacOS often comes with a native version of Python, but we likely want to upgrade that and install PIP. The best way to do this is with a MacOS Linux-like package manager called [Homebrew](https://brew.sh/). You can visit the below pages to walk you through installing Homebrew and an updated Python interpreter along with it
1. Open Terminal and run: `xcode-select --install`. This will open a window. Click **'Get Xcode'** and install it from the app store.
2. Install Homebrew. Run: `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
3. Install latest Python2: `brew install python@2`
4. Install latest Python3: `brew install python`
5. Link your default Python path to the new install `brew link --overwrite python`
6. Close Terminal and reopen it. You should see Python 2.7.15 when you run `python -V`
7. Once Python is installed, you should be able to open Terminal, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to [Install Autoshell](#install-autoshell-using-pip-recommended)
	- Additional resources on [Installing Python 2 on Mac OS X](https://docs.python-guide.org/starting/install/osx/)
	- Additional resources on [Installing Python 3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)

#### Linux
1. Install required OS packages
	- **Raspberry Pi** may need Python and PIP `sudo apt install -y python-pip` as well as `sudo apt-get install libffi-dev`
	- **Debian (Ubuntu)** distributions may need Python and PIP
		- Install Python and PIP: `sudo apt install -y python-pip`
	- **RHEL (CentOS)** distributions usually need PIP
		- Install the EPEL package: `sudo yum install -y epel-release`
		- Install PIP: `sudo yum install -y python-pip`


### Install Autoshell using PIP (Recommended)
1. Install Autoshell using pip by running the command `pip install autoshell`
2. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.



### Install Autoshell from source (Advanced)
1. Retrieve the source code repository using one of the two below methods
	- **Method #1**: Install a Git client (process differs depending on OS) and clone the Autoshell repository using Git `git clone https://github.com/packetsar/autoshell.git`
		- Change to the branch you want to install using `git checkout <branch_name>`
	- **Method #2**: Download and extract the repository files from the [Github Repo](https://github.com/PackeTsar/autoshell)
		- Make sure to download the branch you want to install
2. Move into the autoshell project directory `cd autoshell`
3. Run the setup.py file to build the package into the ./build/ directory `python setup.py build`
4. Use PIP to install the package `pip install .`
5. Once the install completes, you should be able to run the command `autoshell -h` and see the help menu. Autoshell is now ready to use.


-----------------------------------------
##   GETTING STARTED   ##

Below are some nuts and bolts to help you understand how to use Autoshell. If you want a quick 'how-to', then check out the **[Autoshell Tutorial](TUTORIAL-1.md)**.

Once you have installed Autoshell, you can see the command guide with `autoshell -h`.

Since modules are able to add their own arguments into the argument parser when they are imported, you can see a module's help by importing it (ie: `-m crawl`) and then adding the `-h` argument. You can see this by trying `autoshell -m crawl -h`, there you will see a section of argument descriptions for the Crawl module.

The simplest way to connect to a host is to point Autoshell directly at it (`autoshell 192.168.1.1`). If you do not provide credentials, it will prompt you for them. It is easy to add them inline with `-c username:password`. You are able to add as many hosts and credentials as you want and they are processed in the order you provide them.


### Credentials
Credentials can be provided to Autoshell in a few different ways:
1. **At the command line as a string.** The default full format for credentials is `-c <username>:<password>:<secret>@<host_type>`. This default format has optional values included. A credential string can have just one value (ie: `-c admin`) and Autoshell will use that `admin` value for the username, password, and secret; it will leave the host_type blank unless provided. You can instead provide `-c admin:password` and Autoshell will use the provided password for both the password and secret values. More examples are provided in the command help guide at the command line.
2. **As a structured JSON or YAML file.** You can use the [examples/example_structured_credentials_file.json](#examplesexample_structured_credentials_filejson) and [examples/example_structured_credentials_file.yml](#examplesexample_structured_credentials_fileyml) files as examples, then reference them from the command-line like `-c example_structured_credentials_file.json`. You can reference as many credential files as you want.
3. **As an unstructured file.** See [examples/example_unstructured_credentials.txt](#examplesexample_unstructured_credentialstxt) for an example. In the unstructured format, each line in the file will contain a credential string in the standard command-line format. You can then reference the file from the command-line like `-c example_unstructured_credentials.txt`. You can reference as many credential files as you want.




### Addresses
Addresses are provided to Autoshell at the command-line using positional arguments (without a prepended `-x` or `--xxxx` tag). You are able to provide as many addresses as you want here and they will processed in the order you give them. Below are some examples of how you can provide addresses.
1. **As a simple string at the command-line.** Addresses use the format of `<address>@<host_type>` where the host_type value is optional. A simple example is just using the IP address or dns-name like `192.168.1.1` or with a host_type like `192.168.1.1@cisco_ios`.
2. **As a structured JSON or YAML file.** You can use the [examples/example_structured_addresses_file.json](#examplesexample_structured_addresses_filejson) and [examples/example_structured_addresses_file.yml](#examplesexample_structured_addresses_fileyml) files as examples, then reference them from the command-line like `example_structured_addresses_file.json`. You can reference as many address files as you want.
3. **As an unstructured file.** See [examples/example_unstructured_addresses_file.txt](#examplesexample_unstructured_addresses_filetxt) for an example. In the unstructured format, each line in the file will contain an address string in the standard command-line format. You can then reference the file from the command-line like `example_unstructured_addresses_file.txt`. You can reference as many address files as you want.




### Using Config Files
Since you may often need to define many command-line arguments, it is often easier to provide command-line arguments using a config file. You can use a structured JSON or YAML config file (examples can be found at [examples/example_config_file.json](#examplesexample_config_filejson) and [examples/example_config_file.yml](#examplesexample_config_fileyml)) to define your arguments and reference the config file using `-f` or `--config_file` at the command-line (like `-f example_config_file.json`). The example config files can also be found in the [examples project folder](examples).

You can define known or unknown arguments in the config file and both will be passed into the program and into any modules you import. You can also define multiple config files which will either overwrite or append to each others settings (depending on if the argument can have multiple values).

Arguments can still be defined at the command-line even when using config files. If the argument is a single value (like the debugging level) then the command-line value will overwrite any config file values. If the argument allows multiple entries (like credentials) then the command-line values will prepend any config-file values.

> **TIP:** If you want to take your working autoshell command and convert the inline options to a config file, you can run your command with level 4 (``-dddd``) or level 5 (``-ddddd``) debugging enabled and look for the ``###### INPUT ARGUMENTS #######`` section. You can copy that JSON data into a file and use that file as your config file. Remember to readjust your debugging level in the config file as it will show as 4 or 5.


-----------------------------------------
##   MODULES   ##
The power and flexibility of Autoshell is realized by the use of modules. Modules are python files or libraries which are used to manipulate the hosts connected to by Autoshell. Autoshell includes some modules bundled in the installation. These bundled modules can be found in the [modules folder](autoshell/modules) at path `autoshell/modules/`. Modules can (and often should) also be user-written using Python to do whatever the user wants. Modules can be imported in two different ways:
1. Using a command-line argument like `-m neighbors`.
2. Using a config-file. See the [Using Config Files](#Using-Config-Files) section for more info.

Modules may [optionally] introduce their own arguments into the argument parser when they are imported. These module-specific arguments are recognized by the argparser and will have a help-menu displayed when using the `-h` argument. You can see an example of this by issuing `autoshell -m crawl -h`.

### Bundled Modules
Bundled modules are included in the default installation of Autoshell and can be imported for use immediately after installation. The bundled module files can be found in the [modules folder](autoshell/modules) at path `autoshell/modules/`. You can use these bundled modules as a reference when writing your own module as they too must adhere to the [Autoshell Module API](#autoshell-module-api).
- **cmd**: `cmd` is a bundled module and can be imported with `-m cmd`. You can also use `-m cmd -h` to see all options and switches related to it. When no options are used, the `cmd` module will prompt the user for a command to execute on all connected hosts. It will then execute the command and return the output.
	- The `-C` option can be used to run one or more commands without user interaction.
		- You can prepend the term `config:` to a command to have it run in config mode on the device. Example: `config: router ospf 1`
	- The `-O` option can be used to write host output (from all hosts) to a filepath.
	- The `-P` option can be used to write each hosts output to a different file. In this option you can use the Jinja2 language to templatize the names of the files/folders where the output is written. For example: `-P /root/{{hostname}}.txt` will write the output for each host into a file named from the hosts hostname. All attributes from the `host.info` dictionary are available here as well as the `now` function from the `datetime` library. This allows you to structure file/folder names with a timestamp like `-P /root/{{now.strftime('%Y-%m-%d_%H.%M.%S')}}.txt`.

### User-Written Modules
If you are not able to accomplish the automation tasks you want using the bundled modules (which is common), then you can write your own module to accomplish your task. Autoshell makes this quite easy since much of the difficult work will have been done by the time the code in your module is called. User-written modules can be imported using its file path (ie: `-m mymods/mymodule.py`) or you can reference the file name in a config-file.

### Autoshell Module API
Autoshell will attempt to call any imported module at three (3) points during execution.

1. `add_parser_options(parser)` (*optional*): The first call against your module will be done against your `add_parser_options` function. This is an *optional* call and will only be done if the `add_parser_options` function exists in your code. This call will hand program control over to your module and allow you to populate custom arguments into the Autoshell argument parser. This call is made before the arguments are parsed and before we connect to hosts (this is how you can see a module's help info when using the `-h` switch).

2. `load(ball)` (*optional*): The second call against your module will be done against your `load` function. This is an *optional* call and will only be done if the `load` function exists in your code. This call will hand program control over to your module to allow you to perform input checks on user-provided arguments before Autoshell starts connecting to hosts. The `load` call exists to permit your module to perform input checks and throw warnings/errors early on in the program instead of waiting until all hosts have been connected and all other modules have run. You can also use the `load` function to do some pre-processing of user inputs and store them in a namespace object to be used later when the module is run.
3. `run(ball)` (*required*): The third and final call against your module will be done against your `run` function. This is a *required* call and your module must include a `run` function in order to operate. The `run` function is called after all hosts have been processed/connected and after all previously imported modules (since modules are processed in the order in which they are referenced from the CLI) have completed. The `run` function is where you want to perform your custom tasks on connected hosts.
	- **Threading**: Autoshell includes a queueing/threading library called `autoqueue` which can be very useful when wanting to perform your custom tasks on many hosts in parallel. Autoqueue can be imported and used in your module by importing the autoshell library (`import autoshell`) and instantiating an autoqueue object (`autoshell.common.autoqueue.autoqueue(<arguments>)`). You can reference the example modules for examples on how to use autoqueue.

Once the module's `run` function returns control of the main thread back to the Autoshell program, Autoshell will call the `run` function of the next module if there is a module in order after this one. Once all modules complete and the last module returns control, Autoshell will perform a final processing of all active hosts by gracefully disconnecting from them and quitting the program.

### The Autoqueue Library
Autoqueue is an Autoshell library which makes threading and queueing much easier than using the threading and queue libraries separately. Autoqueue also provides functions for blocking the main thread until the queue is empty and the threads are idle.

To use Autoqueue in a module. You can import autoshell as a library (`import autoshell`) and referece autoqueue at `queue = autoshell.common.autoqueue.autoqueue(thread_count, worker_func, worker_args)`.

#### Autoqueue Arguments
- **thread_count**: A integer defining how many worker threads you want to use. All threads are supervised and managed by Autoqueue and you don't need to worry about dealing with them.
- **worker_func**: The worker function which will be run inside each thread. Since each thread is monitored and maintained by autoqueue's supervisor, any returned object will be discarded. If you need to return any object/data out of your worker function, you will have pass in and write them to a namespace object or something similar.
- **worker_args**: A tuple containing any arguments you want to have passed into your worker function by the thread supervisor in addition to the default arguments which get passed in (`parent_object` and `queue_item`)

Once the queue has been instantiated, it will begin waiting for items to be put into the queue. When items begin being `.put(item)` into the queue, the thread supervisors will begin calling the worker functions, passing the queue items into them.


-----------------------------------------
##   EXAMPLE FILES   ##
Below are some example files you can use for reference. You can find these files in the [examples project folder](examples).


### examples/example_structured_credentials_file.json
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

### examples/example_structured_credentials_file.yml
```
- username: file_admin3
  password: file_password3
- username: file_admin4
  password: file_password4
```

### examples/example_unstructured_credentials.txt
```
unst_admin1:unst_password1
unst_admin2:unst_password2@cisco_ios
```

### examples/example_structured_addresses_file.json
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

### examples/example_structured_addresses_file.yml
```
- address: 192.168.1.1
  type: cisco_ios
- address: 192.168.1.2
```

### examples/example_unstructured_addresses_file.txt
```
192.168.1.10
192.168.1.11@cisco_ios
```

### examples/example_config_file.json
```
{
	"modules": [
		"neighbors",
		"cli"
	],
	"debug": 5,
	"addresses": [
		"192.168.1.1",
		"192.168.1.2"
	],
	"credentials": [
		"cfg_file_admin1:cfg_file_password1",
		"cfg_file_admin2:cfg_file_password2@cisco_ios",
		"examples/example_structured_credentials_file.json"
	],
	"dump_hostinfo": false,
	"logfiles": [
		"autoshell_log1.log",
		"autoshell_log2.log"
	]
}
```

### examples/example_config_file.yml
```
modules:
  - neighbors
  - cli
debug: 5
addresses:
  - 192.168.1.1
  - 192.168.1.2
credentials:
  - admin1:password1
  - admin2:password2@cisco_ios
  - examples/example_structured_credentials_file.json
dump_hostinfo: false
logfiles:
  - autoshell_log1.log
  - autoshell_log2.log
```



[logo]: http://www.packetsar.com/wp-content/uploads/autoshell_logo4_100.png
