#!/usr/bin/python


# Autoshell Libraries
import autoshell


#### FIXME Fix the import of modules so we can use single name
#### FIXME Fix string vs list entry for logfile, credential, addresses, etc
#### FIXME Expressions needs to error with bad YAML (read as strings)
#### FIXME Expressions to interpret raw lines from unknown file
# FIXME CDP and LLDP adding empty neighbors
# FIXME Get crawl max_hops working
# FIXME Crawl needs some serious rewriting for multi-connect to work
#### FIXME Test and fix logfiles
# FIXME Go through and replace all % uses with .format
# FIXME Build unit tests
# FIXME Integrate CI system for testing
# FIXME Write documentation
#### FIXME Put into PyPi
# FIXME Modules: (config, cmd, cdp2desc)
# FIXME Change common.expressions to be variable depth?
# FIXME?? -p to edit profile (timeout, threads, etc) '-p 10:25:60'


if __name__ == "__main__":
    autoshell.__main__.start()
