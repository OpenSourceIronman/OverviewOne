#!/usr/bin/env python

__author__ = "Steve Alvarado"
__maintainer__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__version__ = "1.0.0"
__date__ = "Late Updated: 05/06/16 (SRA)"
__doc__ = """
This is a very simple example of how to use the swiftradio library to
fetch radio telemetry information from a SWIFT-SDR and print the information
to the console. The SwiftRadioClient class is used to connect to a Swift-SDR
unit, execute the 'sysstat' command and then process and print the received
information to stdout.
"""

#-------------------------------------------------------------------------------------------------------------
# 	Imports
#-------------------------------------------------------------------------------------------------------------
import os
import sys
import traceback
import argparse
import time
sys.path.insert(1, "../..")
from swiftradio.clients import SwiftRadioEthernet
from swiftradio.command_interfaces import DummyCommandInterface

#---------------------------------------------------------------------------------------------------
# 	Main Program
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	radio_interface = None

	# Create Command Line Parser
	parser = argparse.ArgumentParser(prog = __file__, description = __doc__, add_help=True)
	parser.add_argument("ip", type = str, help = "ip address of radio.")
	args = parser.parse_args()

	print "--"
	print "Command Interfaces Test"
	print "Version {}".format(__version__)
	print "Tethers Unlimited Inc. (c)"

	try:
		# Create a SWIFT-SDR Interface and Connect to Radio
		radio_interface = SwiftRadioEthernet(args.ip, name="TestRadio")

		# Connect to Radio
		if radio_interface.connect():

			# add command interface
			radio_interface.attach_command_interface("dummy_interface", DummyCommandInterface)

			# test command interface methods
			print "\nRadio Client Name: {}".format(radio_interface.dummy_interface.get_radioclient_name())
			print "Device ID: 0x{}".format(radio_interface.dummy_interface.get_devid())
			print "10^2 = {}\n".format( radio_interface.dummy_interface.square(10) )

			# destroy interface connections
			radio_interface.destroy_command_interfaces()

			# test command interface methods
			radio_interface.disconnect()

	except KeyboardInterrupt:
		print "\nexiting program...\n"

	except:
		traceback.print_exc()

	# Exit Program
	if radio_interface != None:
		radio_interface.disconnect()	# Always close connection before program exit!
