#!/usr/bin/env python
"""
This script will import the SwiftRadio registration module and discover every SwiftRadio on the network.
If the SwiftRadio doesn't match any registration modules, the user will be prompted if they'd like to provide
information to add the radio to the registration module.
"""
__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Demo"
__date__ = "Late Updated: 7/16/15"

import sys
import traceback
import os
import platform
import serial
import serial.tools.list_ports

# * import SwiftTest library *
from ..db import swiftradiodatabase
from ..db import swiftradiodef

def swift_com_search(swiftradio_obj, reg_modules, baud=None):
	"""
	Search for a Serial SWIFT-SDR device connected to this computer and display information to console.

	:param SwiftRadioInterface() swiftradio_obj: SwiftRadioInterface object for performing search queries.
	:param list reg_modules: A list of radio database registration modules.

	.. todo:: Parameter documentation is a bit unclear. Needs to be better clarified (examples would be helpful).

	Last Updated: 7/16/15 (SRA)
	"""
	print "\nSWIFT-SDR COM Port Search Program\nTethers Unlimited Inc. (c)\nwww.tethers.com\n"
	try:
		# [1] create radio database instance
		radio_db = swiftradiodatabase.RadioDatabase()

		# [2] register radio databases
		for radio_reg_module in reg_modules:
			radio_db = radio_reg_module.register_swiftradio_database(radio_db)

		# [3] perform network enumeration and get definitions of ALL radios on network
		print "discovering all swift devices...",
		com_radios = comport_enumerate_sysinfo(swiftradio_obj, radio_db, baud)

		# [4] error check network enumeration
		if len(com_radios) > 0:
			print "done.\n"
		else:
			print "failed to find any radios.\n"
			print "***No Swift-SDR devices detected***"
			sys.exit(1)

		# # [5] parsing radio information using radio database
		# discovered_radios_defs = enumerate_database_radios(swiftradio_obj, com_radios, radio_db, return_as_dict = False)

		# [5] display available radios for user
		choice_num = 1
		print "SWIFT-SDR Radios:"
		for comport, radio_defn in com_radios:

			# get name of this radio
			name = radio_defn.get_name()
			stackup = radio_defn.get_stackup()

			# get radio information
			firmware_info = radio_defn.get_firmware_info()
			software_builder = firmware_info["software_builder"]
			baseband_info = ("baseband", [radio_defn.get_baseband_info()])
			frontend_info = ("frontend", radio_defn.get_frontend_info())
			breakout_info = ("breakout", [radio_defn.get_breakout_info()])
			radio_boards = [baseband_info, frontend_info, breakout_info]
			devid = radio_defn.get_devid()

			# print basic radio info
			print "{:>4} {}".format("[{}]".format(choice_num), name)
			print "{:>5}COM: {}".format("", comport)
			if stackup != None:
				print "{:>5}stack up: {}".format("", stackup)
			print "{:>5}device id: {}".format("", devid)
			for board_type, board_info_list in radio_boards:
				if board_info_list != None:
					for board_info in board_info_list:
						if board_info != None:
							print "{:>5}{}: {} {}-{}-{}".format("", board_type, board_info.get_name(), board_info.get_board_index(), board_info.get_assembly_variant(), board_info.get_assembly_board())
			print "{:>5}programmer: {}".format("", software_builder)

			# increment choice number
			choice_num += 1

	except SystemExit:
		pass

	except:
		traceback.print_exc()

def swift_com_enumerate():
	"""
	Description: get a list of COM Ports/Device names and SWIFT-SDR device identifiers of all the Swift SDR
				devices currently connected to host CPU.
	Parameters: broadcasts - number of times perform a network broadcast. Sometimes the radios will
	 						not respond to a broadcast due to poor network performance.
	Return: a list of tuples that contain the radio info and ip address information of all the Swift
			SDR devices on the local network. the 2-item tuples have the following format:

				(device_id, swift_sdr_network_ip_address)
	"""
	clients_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
	sys.path.append(clients_dir)
	from clients import SwiftRadioRS422
	del sys.path[-1]

	swiftradio_list = list()

	# perform a network broadcast, get ip address of every network device that responds
	com_port_list = get_ports()

	# ping the up address of every network device that responded to broadcast
	for device_port in com_port_list:

		if (platform.system() in ("Windows", "Microsoft")) and (serial.VERSION[0] == "2"):
			port = int(str(device_port).replace("COM",""))
		else:
			port = device_port

		# A) define a client for sending commands to device
		radio_interface = SwiftRadioRS422(port=port)

		# B) attempt to connect to the device
		if radio_interface.connect():

			sysinfo = None
			radio_info = None

			# get sysinfo
			sysinfo = radio_interface.execute_command("sysinfo", timeout=1, fail_retries=3)

			if sysinfo["_error"] is None:

				# store radio's device id and device port information
				radio_info = (sysinfo["id"], device_port)

				# add radio information to list of found radios (don't place duplicates in list)
				if radio_info not in swiftradio_list:
					swiftradio_list.append(radio_info)

		# D) delete the interface connection to this device
		radio_interface.disconnect()

		radio_interface = None

	return swiftradio_list

def comport_enumerate_sysinfo(radio_interface, db, baudrate=115200):
	"""
	Description:
	Optional Parameters:
	Return:
	Note:
	"""
	swift_com_list = list()

	# get a list of available com ports to connect to
	com_port_list = get_ports()

	for com_port in com_port_list:

		# convert com port number to integer
		if (platform.system() in ("Windows", "Microsoft")) and (serial.VERSION[0] == "2"):
			com_num = int(str(com_port).replace("COM",""))
		else:
			com_num = com_port

		try:
			# A) define a temporary connection
			if baudrate is None:
				radio_interface.add_uart_connection(com_num, name="test", framing="HDLC")
			else:
				radio_interface.add_uart_connection(com_num, name="test", baud=baudrate, framing="HDLC")

			# B) attempt to "open" the connection to the device
			device_connection_opened = radio_interface.connect("test", fail_exception=True)

		except serial.SerialException:
			device_connection_opened = 0
		except serial.SerialTimeoutException:
			device_connection_opened = 0

		# C) check if connection was successfully opened
		if device_connection_opened:

			# check if this is a swift device
			device_info = device_verification( radio_interface )

			# if so, save device firmware info and comport number
			if device_info is not None:

				firmware_info = enumerate_database_def(device_info, db, "uart")
				swift_com_list.append( (com_num, firmware_info) )

		radio_interface.disconnect("test")

		# D) delete the interface connection to this device
		radio_interface.remove_connection("test")

	return swift_com_list

def enumerate_database_def(firmware_info, radio_db, connection_type, return_as_dict = False):
	"""
	Description:
	Parameters:
	Return: a list of tuples containing RadioTestUnit objects representing the radios on the network and
			the ip address of that radio.
	"""
	# lookup this radio in database using its device id (lookup returns a radio definition)
	radio_def = radio_db.get_radio_by_devid(firmware_info["id"])

	# check if the radio was found in database, if not, create new definition
	if radio_def == -1:

		# create a new database definition
		unregistered_radio = swiftradiodef.SwiftRadioDefinition()

		# set basic radio info
		unregistered_radio.set_name("*Unknown")
		if len(firmware_info["id"]) == 16:
			unregistered_radio.set_devid(firmware_info["id"])
		unregistered_radio.set_connection_type(connection_type)

		# save newly created definition
		radio_def = unregistered_radio

	# save firmware information in the radio definition
	radio_def.set_firmware_info(firmware_info)

	# [3] return list
	return radio_def


def device_verification(device, max_attempts=3, timeout=1):
	"""
	Description:
	Parameters:
	Return: device id string or None if device could not be found
	"""
	radio_found = False
	firmware_info = dict()
	attempts = 0

	while (radio_found == False) and (attempts < max_attempts) and (radio_found is False):
		attempts += 1

		# send a Swift "device id" command request to network device
		pkt_list, error, etype = device.execute("sysinfo", timeout = timeout, return_error=True)

		if error == 0:
			firmware_info["id"] = pkt_list.find_command_data_by_name("id", "str")
			firmware_info["platform"] = pkt_list.find_command_data_by_name("platform", "str")
			firmware_info["hardware_builder"] = pkt_list.find_command_data_by_name("hardware_builder", "str")
			firmware_info["software_builder"] = pkt_list.find_command_data_by_name("software_builder", "str")
			firmware_info["build_revision"] = pkt_list.find_command_data_by_name("build_revision", "uint")
			firmware_info["hardware_timestamp"] = pkt_list.find_command_data_by_name("hardware_timestamp", "uint")
			firmware_info["software_timestamp"] = pkt_list.find_command_data_by_name("software_timestamp", "uint")
			firmware_info["hardware_id"] = pkt_list.find_command_data_by_name("hardware_id", "uint")

			# convert the time resolution value to nanoseconds
			timeres = pkt_list.find_command_data_by_name("time_resolution", "float")

			# but make sure the data was received before converting
			if timeres != None:
				firmware_info["time_resolution"] = timeres*1e9

			# check if device responded with a valid device ID
			if (firmware_info["id"] != None) and (firmware_info["software_builder"] != None):

				# if found, store radio's device id and ipv4 information
				radio_found = True

		# if the radio responded but took too long to return desync, increase timeout and try again
		if (error==-999) and (etype==-2):
			timeout+=2

		device.clear_packet_list()

	if radio_found:
		return firmware_info
	else:
		return None

def get_com_ports():
	"""
	Description:
	Optional Parameters:
	Return:
	Note:
	"""
	def order_com_ports(port_list):
		"""
		Description:
		Optional Parameters:
		Return:
		Note
		"""
		com_num_list = list()
		new_port_list = list()
		for port in port_list:
			com_num = int(str(port).replace("COM",""))
			com_num_list.append(com_num)
		com_num_list.sort()
		for com_num in com_num_list:
			new_port_list.append("COM" + str(com_num))
		return new_port_list

	com_port_nums = list()

	ports_iterable = serial.tools.list_ports.comports()
	ports = [i for i in ports_iterable]
	for item in ports:
		com_port_nums.append(item[0])

	# order the com ports numerically
	ordered_com_ports = order_com_ports(com_port_nums)
	return ordered_com_ports

def get_ports():
	"""
	Description:
	Optional Parameters:
	Return:
	Note:
	"""
	import platform
	def order_com_ports(port_list):
		"""
		Description:
		Optional Parameters:
		Return:
		Note
		"""
		com_num_list = list()
		new_port_list = list()
		for port in port_list:
			com_num = int(str(port).replace("COM",""))
			com_num_list.append(com_num)
		com_num_list.sort()
		for com_num in com_num_list:
			new_port_list.append("COM" + str(com_num))
		return new_port_list

	ports = list()

	ports_iterable = [i for i in serial.tools.list_ports.comports()]
	for item in ports_iterable:
		ports.append(item[0])

	# order the com ports numerically
	if platform.system() in ("Windows", "Microsoft"):
		ports = order_com_ports(ports)
	return ports
