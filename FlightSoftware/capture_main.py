#!/usr/bin/env python2.7

"""
Main entry point for process that captures camera images.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
import signal
import os
import subprocess

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class CaptureMain:

    DEBUG = False

    # This is the root directory where all photos are stored.
    FILE_ROOT = "/home/ahurst/spacevr/test_photos/"

    num_sigterms = 0

    @staticmethod
    def sigterm_handler(signal, frame):
        """
        Signal handler for SIGTERM signals.

        Continue execution and exit gracefully.
        """
        CaptureMain.num_sigterms += 1

    def __init__(self):
        """ Constructor """

        signal.signal(signal.SIGTERM, CaptureMain.sigterm_handler)


    def main(self):
        if CaptureMain.DEBUG: print("Capturing...")

        # Loops.
        while True:

            if (CaptureMain.num_sigterms > 0):
                print("Exiting gracefully due to SIGTERM")
                break
                
            None


if __name__ == "__main__":
    # Was --debug passed on the command line?
    if "--debug" in sys.argv:
        CaptureMain.DEBUG = True

    CaptureMain().main()
