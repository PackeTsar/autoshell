###  [(Next) to Module Writing Instructions >](TUTORIAL-2.md)

# Getting Started with Autoshell ![Rocket](img/rocket_100.png)

### Get started with [Autoshell](https://github.com/PackeTsar/autoshell) by writing your own module!


Autoshell is a shell utility which can be used to ease SSH-based automation tasks by handling many of the pedestrian functions (handling credentials, addresses, CLI arugments, logging, etc) inherent to SSH-based automation. Autoshell relies on user-written (or bundled) modules to do the real work, but allows you to keep your module code terse while multiplying its efficacy.


# **Install Python** ![Python](img/python_65.png)
The first step is to install the Python interpreter on your PC

## **Windows** ![Windows](img/windows_65.png)
### 1. If you have not yet installed Python on your Windows OS, then download and install the latest Python2 or Python3 from [Python Downloads Page](https://www.python.org/downloads/)
- Make sure to check the box during installation which adds Python to PATH. Labeled something like **Add Python X.X to PATH**

### 2. Once Python is installed, you should be able to open a command window, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to [Install Autoshell](TUTORIAL-2.md).
- If you cannot run `python` or `pip` from a command prompt, you may need to add the Python installation directory path to the Windows PATH variable
	- The easiest way to do this is to find the new shortcut for Python in your start menu, right-click on the shortcut, and find the folder path for the `python.exe` file
		- For Python2, this will likely be something like `C:\Python27`
		- For Python3, this will likely be something like `C:\Users\<USERNAME>\AppData\Local\Programs\Python\Python37`
	- Open your Advanced System Settings window, navigate to the "Advanced" tab, and click the "Environment Variables" button
	- Create a new system variable:
		- Variable name: `PYTHON_HOME`
		- Variable value: <your_python_installation_directory>
	- Now modify the PATH system variable by appending the text `;%PYTHON_HOME%\;%PYTHON_HOME%;%PYTHON_HOME%\Scripts\` to the end of it.
	- Close out your windows, open a command window and make sure you can run the commands `python` and `pip`

## **MacOS** ![MacOS](img/apple_65.png)
MacOS often comes with a native version of Python, but we likely want to upgrade that and install PIP. The best way to do this is with a MacOS Linux-like package manager called [Homebrew](https://brew.sh/). You can visit the below pages to walk you through installing Homebrew and an updated Python interpreter along with it

### 1. Open Terminal and run: `xcode-select --install`. This will open a window. Click **'Get Xcode'** and install it from the app store.
### 2. Install Homebrew. Run: `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
### 3. Install latest Python2: `brew install python@2`
### 4. Install latest Python3: `brew install python`
### 5. Link your default Python path to the new install `brew link --overwrite python`
### 6. Close Terminal and reopen it. You should see Python 2.7.15 when you run `python -V`
### 7. Once Python is installed, you should be able to open Terminal, type `python`, hit ENTER, and see a Python prompt opened. Type `quit()` to exit it. You should also be able to run the command `pip` and see its options. If both of these work, then move on to [Install Autoshell](TUTORIAL-2.md)
- Additional resources on [Installing Python 2 on Mac OS X](https://docs.python-guide.org/starting/install/osx/)
- Additional resources on [Installing Python 3 on Mac OS X](https://docs.python-guide.org/starting/install3/osx/)

## **Linux** ![Linux](img/linux_65.png)
- ### **Raspberry Pi** may need Python and PIP
	- ### Install them: `sudo apt install -y python-pip` as well as `sudo apt-get install libffi-dev`
- ### **Debian (Ubuntu)** distributions may need Python and PIP
	- ### Install Python and PIP: `sudo apt install -y python-pip`
- ### **RHEL (CentOS)** distributions usually need PIP
	- ### Install the EPEL package: `sudo yum install -y epel-release`
	- ### Install PIP: `sudo yum install -y python-pip`


###  [(Next) to Module Writing Instructions >](TUTORIAL-2.md)
