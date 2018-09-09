#!/usr/bin/python


# Autoshell Libraries
import autoshell


# ######## BEFORE PUBLISH
# ### FIXME Add ability to add port to address
# ### FIXME Fix the import of modules so we can use single name
# ### FIXME Fix string vs list entry for logfile, credential, addresses, etc
# ### FIXME Expressions needs to error with bad YAML (read as strings)
# ### FIXME Expressions to interpret raw lines from unknown file
# ### FIXME Test and fix logfiles
# ### FIXME Put into PyPi
# ### FIXME Modules (cmd)
# FIXME CDP and LLDP adding empty neighbors
# FIXME Get the default device type working
# FIXME Get crawl max_hops working
# FIXME Go through and replace all % uses with .format
# FIXME Write documentation


# ######## AFTER PUBLISH
# FIXME Modules: (config?, cdp2desc)
# FIXME Add in object tags (tag addresses and credentials?)
# FIXME Add way to use certificates in credentials
# FIXME Crawl needs some serious rewriting for multi-connect to work
# FIXME Build unit tests
# FIXME Change common.expressions to be variable depth?
# FIXME?? -p to edit profile (timeout, threads, etc) '-p 10:25:60'


if __name__ == "__main__":
    autoshell.__main__.start()
