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


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "--help":
        print_usage()
        sys.exit(0)

    hw = Hardware()
    cmd = sys.argv[1]
    cmd_args = sys.argv[2:]

    for (name, func) in inspect.getmembers(hw, inspect.ismethod):
        if name != cmd:
            continue

        args = inspect.getargspec(func).args[1:] # exclude 'self'
        if len(args) != len(cmd_args):
            print("Error: Command %s requires %d arguments but %d provided." %
                      (cmd, len(args), len(cmd_args)))

        # Parse all arguments as integers
        # NOTE: this assumes that all arguments *are* integers / booleans
        cmd_args_parsed = [int(a) for a in cmd_args]

        # OK, run the command!
        try:
            rval = func(*cmd_args_parsed)
        except NotImplementedError as ex:
            print("Error: Command not yet implemented.")
            sys.exit(1)            

        print("Executed command successfully.")
        sys.exit(0)


    print("Error: Invalid command \""+cmd+"\".  For usage info, "+sys.argv[0]+" --help")
    sys.exit(1)


if __name__ == "__main__":
    main()
