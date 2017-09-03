#!/usr/bin/env python2.7

"""
Main entry point for process that captures camera images.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys
import signal
import argparse
import os, os.path
import subprocess

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class CaptureMain:

    DEBUG = False

    # This is the root directory where all photos are stored.
    FILE_ROOT = "/home/ahurst/spacevr/test_photos/"
    # FILE_ROOT = "/media/ubuntu/VRcameraSSD/tmp/"

    num_sigterms = 0

    @staticmethod
    def sigterm_handler(signal, frame):
        """
        Signal handler for SIGTERM signals.

        Continue execution and exit gracefully.
        """
        CaptureMain.num_sigterms += 1


    def __init__(self):
        """ Constructor

        The command line arguments are parsed here.
        """

        signal.signal(signal.SIGTERM, CaptureMain.sigterm_handler)

        parser = argparse.ArgumentParser(description='Capture photo sequence.')
        parser.add_argument('--frames', type=int, nargs=1, default=1,
                            help='Number of frames to capture (default=1)')
        parser.add_argument('--cameras', type=int, nargs=1, default=1,
                            help='Number of cameras to capture (default=1)')
        parser.add_argument('--debug', action='store_true',
                            help='Enable debug output')

        args = parser.parse_args()

        # Read parsed arguments
        if args.debug: CaptureMain.DEBUG = True
        self.nframes = args.frames
        self.ncameras = args.cameras


    def do_one(self, filename, camera):
        """
        Capture one image and write to a file.

        Arguments:
            filename - output file to write
            camera   - numeric ID of camera (between 0 and 7)
        """

        return # TODO: test

        p = subprocess.Popen(
            ["sudo", "./snapshot", filename,
                     "--dev", ("/dev/still%d" % i),
                     "--format", "jpg",
                     "--size", str(4192), str(3104),
                     "--suspend", "--resume"], # TODO: still needed?
            stdout=subprocess.PIPE)
        try:
            (output, err) = p.communicate(timeout=30)
            output_str = output.decode("utf-8")
        except Exception as e:
            None


    def main(self):
        """
        Main action.  Loop over all frames and cameras and exit when finished.
        """

        if CaptureMain.DEBUG: print("Capturing...")

        # Loops.
        self.frame = 0
        while self.frame < self.nframes:

            for camera in range(0, self.ncameras):

                outfile = os.path.join(CaptureMain.FILE_ROOT, "img%d_cam%d.jpg" % (self.frame, camera))
                if CaptureMain.DEBUG: print("  * "+outfile)

                self.do_one(outfile, camera)

                # If we've received a SIGTERM, exit gracefully between images.
                if (CaptureMain.num_sigterms > 0):
                    print("Exiting gracefully due to SIGTERM")
                    return

            self.frame += 1


if __name__ == "__main__":
    # Was --debug passed on the command line?
    CaptureMain().main()
