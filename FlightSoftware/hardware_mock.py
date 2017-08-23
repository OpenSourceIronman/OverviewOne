#!/usr/bin/env python2.7

"""
Mock hardware for testing for BBB flight software.

Copyright SpaceVR, 2017.  All rights reserved.
"""

import sys

# Assert Python 2.7
assert sys.version_info[0:2] == (2,7)

class HardwareMock:

    def __init__(self):
        # Time will advance manually in our mock hardware layer
        self.start_time = 0
    
    def log_and_print(self, func_name):
        print("HardwareMock::%-15.15s time=%0.1f\n" % 
                  (func_name, 
                   self.start_time))

    def deploy_solar_panels(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def turn_on_cpm(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def turn_off_cpm(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def turn_on_cameras(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def turn_on_ffameras(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def run_capture_360(self, num_frames):
        self.log_and_print( sys._getframe().f_code.co_name )
    def run_capture_180(self, num_frames):
        self.log_and_print( sys._getframe().f_code.co_name )
    def send_payload_noop(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def abort_capture(self):
        self.log_and_print( sys._getframe().f_code.co_name )
