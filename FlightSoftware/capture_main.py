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
import time

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

        self.start_time = time.time() # Epoch seconds.

        signal.signal(signal.SIGTERM, CaptureMain.sigterm_handler)

        parser = argparse.ArgumentParser(description='Capture photo sequence.')
        parser.add_argument('--frames', type=int, nargs=1, default=1,
                            help='Number of frames to capture (default=1)')
        parser.add_argument('--cameras', type=int, nargs=1, default=1,
                            help='Number of cameras to capture (default=1)')
        parser.add_argument('--size', type=int, nargs=2,
                            help='Frame size')
        parser.add_argument('--timestamp', type=int, nargs=1,
                            help='Actual time (epoch seconds) at start (default=system)')
        parser.add_argument('--debug', action='store_true',
                            help='Enable debug output')

        args = parser.parse_args()

        # Read parsed arguments
        if args.debug: CaptureMain.DEBUG = True
        self.nframes = args.frames
        self.ncameras = args.cameras
        if args.timestamp:
            self.timestamp = args.timestamp
        else:
            self.timestamp = self.start_time
        if args.size:
            self.framesize = args.size
        else:
            self.framesize = (4192, 3104)

    def set_exif_timestamp(self, filename, epochsecs):
        """
        Add EXIF tag for DateTimeOriginal.

        Use exiftool (perl) command line utility.
        Run in a background process.  Q: Is this too slow
        """

        try:
            date = subprocess.check_output(
                'date --rfc-3339=seconds --date=@'+str(epochsecs),
                shell=True)

            if CaptureMain.DEBUG: print("    timestamp is "+date)

            # Spawn process
            subprocess.Popen(
                ['exiftool', '-DateTimeOriginal="'+date+'" '+filename])

        except Exception as e:
            if CaptureMain.DEBUG: print("ERROR setting EXIF time "+repr(e))


    def do_one(self, filename, camera):
        """
        Capture one image and write to a file.

        Arguments:
            filename - output file to write
            camera   - numeric ID of camera (between 0 and 7)
        """

        # Time for this photo is the start timestamp plus the number of elapsed seconds
        epochsecs = time.time() - self.start_time + self.timestamp

        p = subprocess.Popen(
            ["sudo", "../UVCstill/snapshot", filename,
                     "--dev", "/dev/still%d" % camera,
                     "--format", "jpg",
                     "--size", str(self.framesize[0]), str(self.framesize[1]),
                     "--suspend", "--resume"],
            stdout=subprocess.PIPE)
        try:
            (output, err) = p.communicate(timeout=30)
            output_str = output.decode("utf-8")
        except Exception as e:
            if CaptureMain.DEBUG: print("ERROR during capture "+repr(e))

        self.set_exif_timestamp(filename, epochsecs)


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
