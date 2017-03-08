#!/usr/bin/env python
"""
This is a simple example of how to use the swiftradio library to
fetch radio telemetry information from a SWIFT-SDR and print the information
to the console. The SwiftRadioClient class is used to connect to a Swift-SDR
unit, execute the 'sysstat' command and then process and print the received
information to stdout.
"""

__author__ = "Steve Alvarado"
__maintainer__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__version__ = "1.0.0"
__date__ = "Late Updated: 05/18/16 (SRA)"

#-------------------------------------------------------------------------------------------------------------
# 	Imports
#-------------------------------------------------------------------------------------------------------------
import sys
import traceback
import argparse
import time
sys.path.insert(1, "../..")
import swiftradio
from swiftradio.clients import SwiftRadioEthernet

#---------------------------------------------------------------------------------------------------
# 	Main Program
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	radio_interface = None

	# create command line parser
	parser = argparse.ArgumentParser(prog = __file__, description = __doc__, add_help=True)
	parser.add_argument("ip", type = str, help = "ip address of radio.")
	args = parser.parse_args()

	print "--"
	print "Display Radio Status"
	print "Version {}".format(__version__)
	print "Tethers Unlimited Inc. (c)"

	try:
		# Create a SWIFT-SDR Interface and Connect to Radio
		radio_interface = SwiftRadioEthernet(args.ip)

		# connect to radio
		if radio_interface.connect():

			# display connected radio information
			sysinfo = radio_interface.execute_command("sysinfo")
			print "\n[Radio Info]"
			print "  Device ID      : {}".format( sysinfo["id"] )
			print "  Platform       : {}".format( sysinfo["platform"] )
			print "  Programmer     : {}".format( sysinfo["software_builder"] )
			print "  Build Revision : {}".format( sysinfo["build_revision"] )

			while(1):
				# execute sysstat command to get real-time temp and uptime data
				sysstat = radio_interface.execute_command("sysstat")

				if "temp" in sysstat and "uptime" in sysstat:
					temp = sysstat["temp"]
					uptime = sysstat["uptime"]

				# note that sysstat outputs are not registered in some FPGA builds yet. However
				# we can use find_command_data_by_name() to parse returned sysstat data.
				else:
					temp = swiftradio.tools.find_command_data_by_name(sysstat, "temp", "float")
					uptime = swiftradio.tools.find_command_data_by_name(sysstat, "uptime", "uint")

				if (temp is None) or (uptime is None):
					print "\n**dropped packets**"
					continue

				hrs = (uptime / 60) / 60
				mins = (uptime / 60) % 60
				secs = uptime % 60

				# Print Telemetry Data
				print "\n---------------------------------------------"
				print " Telemetry"
				print "---------------------------------------------"
				print "       Uptime: {} hours {} mins {} secs".format( hrs, mins, secs)
				print "  Temperature: {:.2f} C".format( temp )
				time.sleep(1)

	except KeyboardInterrupt:
		print "\nexiting program...\n"

	except:
		traceback.print_exc()

	# Exit Program
	if radio_interface != None:
		radio_interface.disconnect()	# Always close connection before program exit!
