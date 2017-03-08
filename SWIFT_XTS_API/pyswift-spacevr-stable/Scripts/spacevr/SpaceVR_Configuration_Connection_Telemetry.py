#!/usr/bin/env python
__author__ =  "Blaze Sanders"
__email__ =   "blaze@spacevr.co"
__company__ = "Space Virtual Reality Corp."
__status__ =  "Development"
__date__ =    "Late Updated: 2017-03-01"
__doc__ =     "Script to perform Radio Test Case #1"

"""
The script shall configure:
  - IP address of the radio
  - IP address of the FC
  - UDP socket for transmitting on S band
  - UDP socket for transmitting on X  band
  - UDP socket for receiving on S band
  - Data rate & transmit power on S (up and down) and X (down), Default to .5/1 Mbps for S and 10 Mbps for X
  - Gather telemetry from the radio
"""

import sys, time, traceback, argparse
sys.path.insert(1, "../../Packages")
import swiftradio
import os
from swiftradio.clients import SwiftRadioEthernet

# Preset Variables
SRX_FREQUENCY = 2.072e9		# S-Band Receiver center frequency
STX_FREQUENCY = 2.250e9		# S-Band Transmitter center freuency
XTX_FREQUENCY = 8.084e9		# X-Band Transmitter center frequency
SRX_DATARATE = 5e3		# S-Band Receiver data rate
STX_DATARATE = 1e6		# S-Band Transmitter data rate
XTX_DATARATE = 10e6		# X-Band Transmitter data rate
SRX_PKTSIZE = 1028		# S-Band Reciever Packet Size (1024 bytes + 4 byte sync marker)
STX_PKTSIZE = 1028		# S-Band Transmitter Packet Size (1024 bytes + 4 byte sync marker)
XTX_PKTSIZE = 1028		# X-Band Transmitter Packet Size (1024 bytes + 4 byte sync marker) ??? 
SRX_LINK_DEV = "0.rx1.0"
STX_LINK_DEV = "0.tx0.0"
SRX_LINK_FM = "1.rx1.0" 	# TBR
STX_LINK_FM = "1.tx0.0"		# TBR
XTX_LINK_FM = "0.tx0.0"		# TBR
FLIGHT_MODEL = "fm"             # Flight Model configuration constant
DEV_MODEL = "dev"               # Flight Model configuration constant
DEBUG_STATEMENTS_ON = True      # Toogle debug statements on and off for this python file

def ip_config(radio, unit, fcip, srx_socket, stx_socket, xtx_socket):
	"""
	Description: Configures the radio's link ports.
	"""

	print("::Configuring radio's link ports")
	if unit == FLIGHT_MODEL:
		radio.execute_command("linkfwd {} -t socket -a {} -p {}".format(SRX_LINK_FM, fcip, srx_socket))
		radio.execute_command("linkfwd {} -t socket -a {} -p {}".format(STX_LINK_FM, fcip, stx_socket))
		radio.execute_command("linkfwd {} -t socket -a {} -p {}".format(XTX_LINK_FM, fcip, xtx_socket))
	elif unit == DEV_MODEL:
		radio.execute_command("linkfwd {} -t socket -a {} -p {}".format(SRX_LINK_DEV, fcip, srx_socket))
		radio.execute_command("linkfwd {} -t socket -a {} -p {}".format(STX_LINK_DEV, fcip, stx_socket))
        else:
		print("Unit Type not defined as DEV MODEL or FLIGHT MODEL.")

def srx_config(radio, link, rx_frequency, rx_datarate, rx_pktsize):
	"""
	Description: Configures the radio's S-Band Receiver.
	"""
	# @todo need to configure forwarding ip address
	print("::Configuring radio's S-Band Receiver")
	#radio.execute_command("linkclose {}".format(link))
	#radio.execute_command("linkfreq {} -f {}".format(link, rx_frequency))
	#radio.execute_command("linkrate {} -r {}".format(link, rx_datarate))
	#radio.execute_command("linkmod {} -m bspk".format(link))
	#radio.execute_command("linkfec {} -i none -r 0".format(link))
	#radio.execute_command("linkcod {} -s none".format(link))
	#radio.execute_command("linkfmt {} -f raw-concat -n {}".format(link, rx_pktsize))
	#radio.execute_command("linkopen {}".format(link))  #!!!TURNS ON S-BAND RECIEVER!!!


def stx_config(radio, link, tx_frequency, tx_datarate, tx_pktsize):
	"""
	Description: Configures the radio's S-Band Transmitter .
	"""
	print("::Configuring radio's S-Band Transmitter")
	radio.execute_command("linkclose {}".format(link))
	#radio.execute_command("linkfreq {} -f {}".format(link, tx_frequency))
	#radio.execute_command("linkmod {} -m oqpsk".format(link))
	#radio.execute_command("linkrate {} -r {}".format(link, tx_datarate))
	#radio.execute_command("linkfec {} -i cc7 -o none -r 0.5 -d 0 -n 1".format(link))
	#radio.execute_command("linkcod {} -s none".format(link))
	#radio.execute_command("linkfmt {} -f raw-concat -n {}".format(link, tx_pktsize))
	#radio.execute_command("linkopen {}".format(link)) #!!!TURNS ON S-BAND TRANSMITTER!!!
	radio.execute_command("linkpower {} -p -8".format(link))


def xtx_config(radio, link, tx_frequency, tx_datarate, tx_pktsize):
	"""
	Description: Configures the radio's X-Band Transmitter.
	"""

	# If there is no XTX don't configure (dev)
	if not link:
		return

	print("::Configuring radio's X-Band Transmitter")
	#radio.execute_command("linkclose {}".format(link))
	#radio.execute_command("linkfreq {} -f {}".format(link, tx_frequency))
	#radio.execute_command("linkrate {} -r {}".format(link, tx_datarate))
	#radio.execute_command("linkmod {} -m bpsk".format(link))
	#radio.execute_command("linkfec {} -i none -r 0".format(link))
	#radio.execute_command("linkcod {} -s none".format(link))
	#radio.execute_command("linkfmt {} -f raw-concat -n {}".format(link, tx_pktsize))
	#radio.execute_command("linkopen {}".format(link)) #!!!TURNS ON X-BAND TRANSMITTER!!!
	#radio.execute_command("linkpower {} -p -8".format(link))


def PrintTelemetry(radio, unit):
	"""
	Description: Reads the telemetry from the radio and prints it to the console.
	"""
	sysstat = radio.execute_command("sysstat")			# Reads the system status
	tempsen = radio.execute_command("tempsen")			# Reads the Baseband temperature sensors
	if(unit == FLIGHT_MODEL):
		stxtemp = radio.execute_command("txtemp -s 1")		# Reads the SLX-TX temperature sensor
		srxtemp = radio.execute_command("rxtemp -s 1 -c 1")	# Reads the SLX-RX temperature sensor
		xtxtemp = radio.execute_command("txtemp -s 0")		# Reads the XTX temperature sensor
	else:
		stxtemp = radio.execute_command("txtemp -s 0")		# Reads the SLX-TX temperature sensor
		srxtemp = radio.execute_command("rxtemp -s 0 -c 1")	# Reads the SLX-RX temperature sensor

	print "\n\n-----  Radio Telemetry  -----"
	print("      Power:   {:0.2f}\t(W)".format(sysstat['power']))
	print("     Uptime:   {}\t(s)".format(sysstat['uptime']))
	print("  FPGA Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "fpga", "float")))
	print(" Clock Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "clock", "float")))
	print("   PLL Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "refclk", "float")))
	print(" DRAM0 Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "dram0", "float")))
	print(" DRAM1 Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "dram1", "float")))
	print("HostIF Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(tempsen, "hostiface", "float")))
	print("SLX-TX Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(stxtemp, "pa", "float")))
	print("SLX-RX Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(srxtemp, "rx1_lo", "float")))
	
	if unit == FLIGHT_MODEL:
		print("   XTX Temp:   {:0.2f}\t(C)".format(swiftradio.tools.find_command_data_by_name(xtxtemp, "pa", "float")))

def InitializeRadio(radio, unit, radioIP_Address, computerIP_Address, sRxSocket, sTxSocket, xTxSocket):
	try:
		print "\n----- SpaceVR Configuration Script -----"

		if(unit == FLIGHT_MODEL):
			SRX_LINK = SRX_LINK_FM
			STX_LINK = STX_LINK_FM
			XTX_LINK = XTX_LINK_FM
		else:
			SRX_LINK = SRX_LINK_DEV
			STX_LINK = STX_LINK_DEV
			XTX_LINK = None

		# Connect to the radio with the given IP address.
		radio = SwiftRadioEthernet(radioIP_Address)
		if not radio.connect():
			raise RuntimeError("ERROR: Failed to connect to the radio.")
		radio.execute_command("loglevel -l debug")

		# Configure the radio with the correct Payload or Flight Computer IP address and udp sockets
		ip_config(radio, unit, computerIP_Address, sRxSocket, sTxSocket, xTxSocket)

		# Configure the S-Band Transmitter
		stx_config(radio, STX_LINK, STX_FREQUENCY, STX_DATARATE, STX_PKTSIZE)

		# Configure the S-Band Receiver
		srx_config(radio, SRX_LINK, SRX_FREQUENCY, SRX_DATARATE, SRX_PKTSIZE)

		# Configure the X-Band Transmitter
		if (unit == FLIGHT_MODEL):
			xtx_config(radio, XTX_LINK, XTX_FREQUENCY, XTX_DATARATE, XTX_PKTSIZE)

		# Gather Teletmetry
		print "\nRadio configured, gathering bootup telemetry one time..."
		PrintTelemetry(radio, unit)

	except KeyboardInterrupt:
		print "\n**Keyboard Interrupt Detected**\n"
		if radio != None:
			radio.execute_command("linkclose {}".format(SRX_LINK))
			radio.execute_command("linkclose {}".format(STX_LINK))
			if(args.unit == FLIGHT_MODEL):
				radio.execute_command("linkclose {}".format(XTX_LINK))
			radio.disconnect()
		print "Exiting program..."

	except:
		if radio != None:
			radio.execute_command("linkclose {}".format(SRX_LINK))
			radio.execute_command("linkclose {}".format(STX_LINK))
			if(unit == FLIGHT_MODEL):
				radio.execute_command("linkclose {}".format(XTX_LINK))
			radio.disconnect()
                        print "No radio found, closing connection to SWIFT radio"
		traceback.print_exc()
