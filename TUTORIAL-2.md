###  [< (Back) to Python Install Instructions](TUTORIAL-1.md)

# Autoshell Tutorial ![Rocket](img/rocket_100.png)

# **Install Autoshell** ![Autoshell](img/autoshell_65.png)
Now we can use PIP to install the Autoshell library and scripts

### Open a command prompt (**COMMAND** in Windows, **TERMINAL** in MacOS) and run the command:
### `pip install autoshell`

You should see the PIP package manager install Autoshell and its dependencies.

### Once complete, you should be able to run the command `autoshell` from the command prompt and see the Autoshell help output.


# **Build a Module** ![Module](img/lego_65.png)
Now it's time for the fun stuff: writing our own custom code to do what we want!

## The objectives for our new module are as follows:
- ## Open a specified text file
- ## Send each line of the file as a configuration command to the SSH host

### First, let's create a simple text file called `commands.txt` with some config commands (in the same directory as example.py). An example of this is:

```
access-list 1 permit any
access-list 1 deny any
```

### Now, download the [Example Module File](https://cdn.rawgit.com/PackeTsar/Autoshell-Getting-Started/95a6394b/example.py) and open it in a text editor

If you use Notepad (Windows) or TextEdit (MacOS) to edit text files, please go download a proper editor. I recommend **[Atom](https://atom.io/)**

### Once opened, you will see some boiler plate code in the example.py file

### We want to write all our code under the `my_function` function at the very bottom of the file. Let's take a look at that.

```python
def my_function(parent, host):
    # Log that we are starting work on this host
    log.debug("example.my_function: Starting on {}".format(host.hostname))
    # Grab the actual SSH connection object out of the passed in host
    connection = host.connections["cli"].connection
    # Do something cool...
```

## Append each section of example code to the function as we go. Remember to keep the code indented so it remains a part of the function

### The first thing we need to do is to open a specific text file. We can use the built in `open` function to open the file:

```python
    # Set our file name
    MY_FILE_PATH = "commands.txt"
    # Open the file in read mode and set a variable as that file object
    FILE = open(MY_FILE_PATH)
    # Read the file contents into a new variable
    RAW_TEXT = FILE.read()
    # Close the file
    FILE.close()
```

### Cool, we have the raw text from the file. Now we will want to remove any carriage return characters from the text. They sometimes get added alongside the linefeed characters when using certain text editors (think "\r\n"). Notice how we can reuse the `RAW_TEXT` variable by setting it in relation to itself.

```python
    # Clean the linefeed characters from the raw text by replacing them with
    #  an empty string
    RAW_TEXT = RAW_TEXT.replace("\r", "")
```

### Next we will use the built in `split` function to split the text using the linefeed character. This will take a single string and give us a list of strings. `split` also consumes the linefeed characters in the process, so they get deleted automatically.

```python
    # Create a list of commands from the raw text by splitting on newlines
    COMMANDS = RAW_TEXT.split("\n")
```

### Now that we have our list of commands, let's enter config-mode on our device. Rather than sending a `config t` command, we want to use the API on the SSH library ([Netmiko](https://github.com/ktbyers/netmiko)) since it continuously keeps track of the SSH prompt and will get confused if we enter config mode manually.

```python
    # Enter config mode on the host
    connection.config_mode()
```

### We're in config-mode now and ready to send commands! Let's loop through our list of commands and send them one by one. We can also log as we go:

```python
    # Loop through each command
    for COMMAND in COMMANDS:
        # Log what we are doing so we can see the action
        log.info("Sending ({}) to {}".format(COMMAND, host.hostname))
        # Send the command over SSH
        RESPONSE = connection.send_command(COMMAND)
        # Log the device response in case we misspell something
        log.info("Response from {}: {}".format(host.hostname, RESPONSE))
```

### Commands are sent, now let's exit config mode to clean up after ourselves

```python
    # Exit config mode on the host
    connection.exit_config_mode()
```

### Now that we have our code, let's take a look at the completed function.

```python
def my_function(parent, host):
    # Log that we are starting work on this host
    log.debug("example.my_function: Starting on {}".format(host.hostname))
    # Grab the actual SSH connection object out of the passed in host
    connection = host.connections["cli"].connection
    # Do something cool...
    # Set our file name
    MY_FILE_PATH = "commands.txt"
    # Open the file in read mode and set a variable as that file object
    FILE = open(MY_FILE_PATH)
    # Read the file contents into a new variable
    RAW_TEXT = FILE.read()
    # Close the file
    FILE.close()
    # Clean the linefeed characters from the raw text by replacing them with
    #  an empty string
    RAW_TEXT = RAW_TEXT.replace("\r", "")
    # Create a list of commands from the raw text by splitting on newlines
    COMMANDS = RAW_TEXT.split("\n")
    # Enter config mode on the host
    connection.config_mode()
    # Loop through each command
    for COMMAND in COMMANDS:
        # Log what we are doing so we can see the action
        log.info("Sending ({}) to {}".format(COMMAND, host.hostname))
        # Send the command over SSH
        RESPONSE = connection.send_command(COMMAND)
        # Log the device response in case we misspell something
        log.info("Response from {}: {}".format(host.hostname, RESPONSE))
    # Exit config mode on the host
    connection.exit_config_mode()
```

### Save your file and now we are ready to run the module

# **Run Your Module** ![Execute](img/execute_65.png)
Wind it up and let it go!

### Modules are imported by file name at the command-line when running Autoshell using the `-m` argument switch.

### In the below example command, we are having Autoshell connect to the host with IP `192.168.1.1` using the Username: `admin` and the Password: `password123`

### We are also setting a debug level of 2 so we have some visibility into what Autoshell is doing and will be able to see the debug logs from our code.

Make sure your command prompt is in the same folder as `example.py` or else provide a complete path to the file. The `commands.txt` file will also need to be in your current directory.

## `autoshell -c admin:password123 -m example.py -dd 192.168.1.1`

### We can also do this one more time and add in the bundled `cmd` module which will let us run a command manually after our module completes

## `autoshell -c admin:password123 -m example.py -m cmd -dd 192.168.1.1`

## Congratulations! You just wrote some Python code and automated a network device. The sky is the limit now!

###  [< (Back) to Python Install Instructions](TUTORIAL-1.md)
