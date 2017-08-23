#!/usr/bin/env python2.7

# Copyright SpaceVR, 2017.  All rights reserved.

import sys, inspect

from hardware import Hardware

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

def print_usage():
    print("Usage: "+sys.argv[0]+" <command> [args...]")

    print("\nAvailable commands:")
    for (name, func) in inspect.getmembers(Hardware(), inspect.ismethod):
        if name.startswith("__"):
            continue

        args = inspect.getargspec(func).args[1:] # exclude 'self'

        if len(args) == 0:               
            print("    %-30.30s" % name)
        else:
            print("    %-30.30s | args= %s" % (name, repr(args)) )

    print("\nNOTE: arguments are not yet supported.")


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "--help":
        print_usage()
        sys.exit(0)

    hw = Hardware()
    cmd = sys.argv[1]

    for (name, func) in inspect.getmembers(hw, inspect.ismethod):
        if name != cmd:
            continue

        args = inspect.getargspec(func).args[1:] # exclude 'self'
        if len(args) > 0:
            # TODO: add support for arguments.
            print("Error: Commands with arguments not yet supported.")
            sys.exit(1)

        # OK, run the command!
        try:
            rval = func()
        except NotImplementedError as ex:
            print("Error: Command not yet implemented.")
            sys.exit(1)            

        print("Executed command successfully.")
        sys.exit(0)


    print("Error: Invalid command \""+cmd+"\".  For usage info, "+sys.argv[0]+" --help")
    sys.exit(1)


if __name__ == "__main__":
    main()
