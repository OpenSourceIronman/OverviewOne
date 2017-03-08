#!/usr/bin/env python
import os, sys, time, traceback, argparse
sys.path.insert(1, "../../Packages")
from swiftradio.clients import SwiftRadioEthernet
from swiftradio.clients import SwiftUDPClient
import swiftradio

__author__ = "Ethan Sharratt"
__email__ = "sharratt@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 08/02/16"
__doc__ = "Script for sending a file to the radio to be downlinked."


# Create command line parser
parser = argparse.ArgumentParser(prog = "SpaceVR Downlink File", description = __doc__, add_help=True)
parser.add_argument("-i", "--ip_addr", type=str, default="192.168.1.42", help="IPv4 address of the radio.")
parser.add_argument("-p", "--port", type=int, default=30000, help="Port number on the radio to forward data from.")
parser.add_argument("-b", "--bind_port", type=int, default=30500, help="Port number on the Flight Computer to forward data to.")
parser.add_argument("-f", "--filename", type=str, default="rxfile_{}.bin".format(time.strftime("%m%d%Y%H%M")), help="File to save received data to.")
parser.add_argument("-l", "--loop", type=int, default=0, help="Set to 1 to loop file.")
args = parser.parse_args()

SRX_PKTSIZE = 1024

if __name__ == "__main__":
	try:
		# Open the receive data file
		try:
			f = open("sampleData.txt", 'wb')			
			#f = open(args.filename, 'wb')
		except:
			print "Could not open {}, ensure the filepath is correct.".format(args.filename)
			sys.exit(1)


		# Instantiate a UDP connection to the uplink port.
		try:
			udp = SwiftUDPClient(args.ip_addr, args.bind_port, args.port)
			udp.connect()
		except:
			print "Could not open a udp client for the provided IPv4 address and port."
			sys.exit(1)


		# Send file to radio.
		bytes = 0
		print "Press CTRL+C to stop receiving data."
		while True:
			data = udp.read(SRX_PKTSIZE)
			if data:
				f.write(''.join(data))

	except KeyboardInterrupt:
		f.close()
		udp.disconnect()
	except:
		traceback.print_exc()
