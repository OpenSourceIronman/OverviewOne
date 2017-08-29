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
        self.cur_time = self.start_time
    
    def time(self):
        return self.cur_time

    def advance_time(self, delta):
        self.cur_time = self.cur_time + delta

    def log_and_print(self, func_name, extra=""):
        print("HardwareMock::%-15.15s time=%0.1f %s \n" % 
                  (func_name, 
                   self.start_time,
                   extra))

    def deploy_solar_panels(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def power_eyestar(self, enable):
        self.log_and_print( sys._getframe().f_code.co_name, "ON" if enable else "OFF" )
    def power_cpm(self, enable):
        self.log_and_print( sys._getframe().f_code.co_name, "ON" if enable else "OFF" )
    def power_cameras(self, enable):
        self.log_and_print( sys._getframe().f_code.co_name, "ON" if enable else "OFF" )
    def power_gps(self, enable):
        self.log_and_print( sys._getframe().f_code.co_name, "ON" if enable else "OFF" )
    def turn_on_ffameras(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def run_capture_360(self, num_frames):
        self.log_and_print( sys._getframe().f_code.co_name, "Num_frames=%d" % num_frames )
    def run_capture_180(self, num_frames):
        self.log_and_print( sys._getframe().f_code.co_name, "Num_frames=%d" % num_frames )
    def run_payload_noop(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def abort_capture(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def point_cells_to_sun(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def point_cameras_to_ground(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def point_antenna_to_transmit(self):
        self.log_and_print( sys._getframe().f_code.co_name )
    def transmit_health_data(self):
        self.log_and_print( sys._getframe().f_code.co_name )