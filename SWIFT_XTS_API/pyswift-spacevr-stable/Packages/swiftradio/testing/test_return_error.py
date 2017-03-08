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
	radio = None

	# create command line parser
	parser = argparse.ArgumentParser(prog = __file__, description = __doc__, add_help=True)
	parser.add_argument("ip", type = str, help = "ip address of radio.")
	parser.add_argument("-t", "--trace", type = int, default=0, help = "radio client trace level.")
	args = parser.parse_args()

	# Create a SWIFT-SDR Interface and Connect to Radio
	radio = SwiftRadioEthernet(args.ip, trace=args.trace)

	# connect to radio
	if radio.connect():
		try:
			# test return values with and without return error parameter
			print "return error = False"
			print radio.execute_command("sysstat")
			print "\nreturn error = True"
			print radio.execute_command("sysstat", return_rpc_error=True)

			# test return values when setting parameter using default_execmd_settings()
			print "\nreturn error = True"
			radio.default_execmd_settings(return_rpc_error=True)
			print radio.execute_command("sysstat")
			print "\nreturn error = False"
			print radio.execute_command("sysstat", return_rpc_error=False)

		except:
			traceback.print_exc()

	# Exit Program
	if radio.connection_isopen():
		radio.disconnect()
