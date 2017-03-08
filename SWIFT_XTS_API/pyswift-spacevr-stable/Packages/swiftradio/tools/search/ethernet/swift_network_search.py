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
import socket

# * import SwiftTest library *
from ..db import swiftradiodatabase
from ..db import swiftradiodef

def swift_network_search(swiftradio_obj, reg_modules):
	"""
	Search network for SWIFT-SDR devices and display information to console.

	:param SwiftRadioInterface() swiftradio_obj: SwiftRadioInterface object for performing search queries.
	:param list reg_modules: A list of radio database registration modules.

	.. todo:: Parameter documentation is a bit unclear. Needs to be better clarified (examples would be helpful).

	Last Updated: 7/16/15 (SRA)
	"""
	print "\nSWIFT-SDR Network Search Program\nTethers Unlimited Inc. (c)\nwww.tethers.com\n"
	try:
		# [1] create radio database instance
		radio_db = swiftradiodatabase.RadioDatabase()

		# [2] register radio databases
		for radio_reg_module in reg_modules:
			radio_db = radio_reg_module.register_swiftradio_database(radio_db)

		# [3] perform network enumeration and get definitions of ALL radios on network
		print "discovering all swift devices on local network...",
		all_network_radios = list()
		all_network_radios = network_enumerate_database_radios(swiftradio_obj, radio_db, broadcasts=2)

		# [4] error check network enumeration
		if len(all_network_radios) > 0:
			print "done.\n"
		else:
			print "failed to find any radios.\n"
			print "***No Swift-SDR devices detected on network***"
			sys.exit(1)

		# [5] display available radios for user
		choice_num = 1
		print "LAN SWIFT-SDR Radios:"
		for radio_defn in all_network_radios:

			# get name of this radio
			name = radio_defn.get_name()
			stackup = radio_defn.get_stackup()

			# get radio information
			connection_info = radio_defn.get_connection_info()
			firmware_info = radio_defn.get_firmware_info()
			software_builder = firmware_info["software_builder"]
			ip_address = connection_info["ipv4"]
			baseband_info = ("baseband", [radio_defn.get_baseband_info()])
			frontend_info = ("frontend", radio_defn.get_frontend_info())
			breakout_info = ("breakout", [radio_defn.get_breakout_info()])
			radio_boards = [baseband_info, frontend_info, breakout_info]
			devid = radio_defn.get_devid()

			# print basic radio info
			print "{:>4} {}".format("[{}]".format(choice_num), name)
			print "{:>5}ipv4: {}".format("", ip_address)
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

def network_enumerate_database_radios(swiftradio_obj, radio_db, broadcasts = 1, return_as_dict = False):
	"""
	Description:
	Parameters:
	Return: a list of tuples containing RadioTestUnit objects representing the radios on the network and
			the ip address of that radio.
	"""
	discovered_swiftradios = list()
	unregistered_swiftradios_num = 0

	# [1] get all swift radio devices on the local network
	network_swiftradios = network_enumerate_sysinfo(broadcasts=broadcasts)

	# [2] create "swiftradio database definitions" for each radio
	for firmware_info, ipv4 in network_swiftradios:

		# lookup this radio in database using its device id (lookup returns a radio definition)
		swiftradiodef_object = radio_db.get_radio_by_devid(firmware_info["id"])

		# check if the radio was found in database, if not, create new definition
		if swiftradiodef_object == -1:

			# increment unregistered radios counter (helps us to give each radio a unique name)
			unregistered_swiftradios_num += 1

			# create a new database definition
			unregistered_radio = swiftradiodef.SwiftRadioDefinition()

			# set basic radio info
			unregistered_radio.set_name("*Unknown{}".format(unregistered_swiftradios_num))
			if len(firmware_info["id"]) == 16:
				unregistered_radio.set_devid(firmware_info["id"])
			unregistered_radio.set_connection_type("ethernet")

			# save newly created definition
			swiftradiodef_object = unregistered_radio

		# save firmware information in the radio definition
		swiftradiodef_object.set_firmware_info(firmware_info)

		# save connection information in the radio definition
		connection_info = {"ipv4": ipv4, "type":"ethernet"}
		swiftradiodef_object.set_connection_info("ethernet", connection_info)

		# convert radio definition object into a dictionary if return_as_dict is True
		if return_as_dict:
			radio_dict = dict() 	# dictionary formatted according to above documentation
			temp_radiodef = swiftradiodef_object

			# get name and devid of this radio
			radio_dict["name"] = temp_radiodef.get_name()
			radio_dict["stackup"] = temp_radiodef.get_stackup()
			radio_dict["devid"] = temp_radiodef.get_devid()

			# get connection information
			connection_info = temp_radiodef.get_connection_info()
			radio_dict["connection"] = connection_info["type"]
			radio_dict["host"] = connection_info["ipv4"]

			# get firmware information (get_firmware_info() returns dict in format documented above
			radio_dict["build"] = temp_radiodef.get_firmware_info()

			# get hardware information
			radio_dict["hardware"] = dict()
			radio_dict["hardware"]["breakout"] = temp_radiodef.get_breakout_info(return_as_dict = True)
			radio_dict["hardware"]["baseband"] = temp_radiodef.get_baseband_info(return_as_dict = True)
			radio_dict["hardware"]["frontends"] = temp_radiodef.get_frontend_info(return_as_dict = True)

			swiftradiodef_object = radio_dict

		# save database information in discovered radios list
		discovered_swiftradios.append(swiftradiodef_object)

	# [3] return list
	return discovered_swiftradios

def network_discover(swiftradio_obj, device_id, portnum = 12345, debug = 0 ):
	"""
	Description: performs a network discover for a swiftradio that has a device id that matches
				 the device id passed in as a parameter
	Parameters: device_id - device identification number of the Radio being searched for
	Optional Parameters: portnum - radio's network port number to send query (defaults to cmdhost packet port)
						 debug - verbosity level (prints extra information during search process)
	Return: the host name (ip address as a string) if the radio is located or a None object if not found
	Note: The Discovery stream service must be active on the radio side for the broadcast function to work correctly.
	"""
	localhosts = list()
	device_id = str(device_id)
	cmdhostmode = "packet"
	radio_trace = 0

	# [1] create a temporary radio instance for sending/receiving data at each local host ip address
	search_trace_output("creating dummy radio to test connections... ", current_tracelevel=debug, msg_tracelevel=1, newline=0)
	if debug > 2:
		radio_trace = 3
	radio = swiftradio_obj

	search_trace_output("done.", current_tracelevel=debug, msg_tracelevel=1)

	# [2] get a list local host addresses on this network
	search_trace_output("gathering list of local hosts addresses... ", current_tracelevel=debug, msg_tracelevel=1, newline=0)
	localhosts = network_broadcast()

	# return an error code if no hosts were found
	if len(localhosts) < 1:
		search_trace_output("no local hosts found.", current_tracelevel=debug, msg_tracelevel=1)
		search_trace_output("swiftradio '%s' not found on network."%(device_id), current_tracelevel=debug, msg_tracelevel=1)
		return None
	search_trace_output("done.", current_tracelevel=debug, msg_tracelevel=1)

	# report local hosts found if debug level is set high enough
	search_trace_output("local hosts:", current_tracelevel=debug, msg_tracelevel=2)
	search_trace_output(localhosts, current_tracelevel=debug, msg_tracelevel=2)

	# [3] ping each host address for a matching devid value
	search_trace_output("performing network search:", current_tracelevel=debug, msg_tracelevel=1)
	for localhost in localhosts:

		# add temporary ethernet connection
		radio.add_ethernet_connection(name="test", host=str(localhost),
										bind_port = 39000,
										port=portnum, transport_layer="UDP")

		# connect to host
		connected = radio.connect("test", fail_exception = False)
		if connected:

			# ping host
			search_trace_output("pinging host '%s'... "%(localhost), current_tracelevel=debug, msg_tracelevel=1, newline=0)
			pkt_list = radio.execute("devid", timeout = 1, fail_retry=True, max_retries=3)

			# process any return packets
			if len(pkt_list) > 0:
				search_trace_output("done.", current_tracelevel=debug, msg_tracelevel=1)
				search_trace_output("%d packets received."%(len(pkt_list)), current_tracelevel=debug, msg_tracelevel=2)

				# extract devid string from packets (should be in first packet received)
				devid = pkt_list[0].get_command_data("str")
				if devid != None:
					search_trace_output("devid read: '%s'"%(devid), current_tracelevel=debug, msg_tracelevel=2)

					# check if devid value matches given device id
					search_trace_output("verifying radio device id... ", current_tracelevel=debug, msg_tracelevel=1, newline=0)
					if device_id in devid:
						search_trace_output("done.", current_tracelevel=debug, msg_tracelevel=1)

						# radio is found, disconnect from dummy radio
						radio.disconnect("test")
						radio.remove_connection("test")
						search_trace_output("swiftradio '%s' found at ip address '%s'"%(devid, str(localhost)), current_tracelevel=debug, msg_tracelevel=1)

						# add a slight delay to allow connection to be completely destroyed
						time.sleep(1)

						# return discovered swiftradio ip address
						return str(localhost)
					else:
						search_trace_output("non-match.", current_tracelevel=debug, msg_tracelevel=1)
						search_trace_output("Radio device id '%s' does not match given search id '%s'"%(devid, device_id), current_tracelevel=debug, msg_tracelevel=2)

			else:
				search_trace_output("no response.", current_tracelevel=debug, msg_tracelevel=1)
		else:
			search_trace_output("could not connect to '%s'."%(localhost), current_tracelevel=debug, msg_tracelevel=1)

		radio.disconnect("test")
		radio.remove_connection("test")

		# time.sleep(1)

	# if at this point, radio with given devid was not found, return -1
	search_trace_output("swiftradio '%s' not found on network."%(device_id), current_tracelevel=debug, msg_tracelevel=1)

	return None

def swift_network_enumerate(broadcasts=1):
	"""
	Description: get a list of ip addresses and SWIFT-SDR device identifiers of all the Swift SDR
				devices currently on the network.
	Parameters: broadcasts - number of times perform a network broadcast. Sometimes the radios will
	 						not respond to a broadcast due to poor network performance.
	Return: a list of tuples that contain the radio info and ip address information of all the Swift
			SDR devices on the local network. the 2-item tuples have the following format:

				(device_id, swift_sdr_network_ip_address)
	"""
	clients_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
	sys.path.append(clients_dir)
	from clients import SwiftRadioEthernet
	del sys.path[-1]

	broadcast_attempts = broadcasts	# sometimes the radios will not respond to a broadcast due to poor network performance
	swiftradio_list = list()
	discovered_devices_ip = list()

	# perform a network broadcast, get ip address of every network device that responds
	discovered_devices_ip = network_broadcast(broadcasts=broadcast_attempts)

	# ping the up address of every network device that responded to broadcast
	for device_ip in discovered_devices_ip:

		# A) define a temporary connection at this network device's ip address
		radio_interface = SwiftRadioEthernet(host=device_ip)

		# B) attempt to connect to the device
		if radio_interface.connect():

			sysinfo = None
			radio_info = None

			# get sysinfo
			sysinfo = radio_interface.execute_command("sysinfo", timeout=1, fail_retries=3)

			if sysinfo["_error"] is None:

				# store radio's device id and ipv4 information
				radio_info = (sysinfo["id"], device_ip)

				# add radio information to list of found radios (don't place duplicates in list)
				if radio_info not in swiftradio_list:
					swiftradio_list.append(radio_info)

		# D) delete the interface connection to this device
		radio_interface.disconnect()

		radio_interface = None

	return swiftradio_list

def network_enumerate_sysinfo(broadcasts=1):
	"""
	Description: get a list of ip addresses and radio information (obtained via sysinfo command) of
				Swift SDR devices currently on the network.
	Parameters: broadcasts
	Return: a list of tuples that contain the radio info and ip address information of all the Swift
			SDR devices on the local network. the 2-item tuples have the following format:

				(swift_sdr_sysinfo, swift_sdr_network_ip_address)
	"""
	clients_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../.."
	sys.path.append(clients_dir)
	from clients import SwiftRadioEthernet
	del sys.path[-1]

	broadcast_attempts = broadcasts	# sometimes the radios will not respond to a broadcast due to poor network performance
	swiftradio_list = list()
	discovered_devices_ip = list()

	# perform a network broadcast, get ip address of every network device that responds
	discovered_devices_ip = network_broadcast(broadcasts=broadcast_attempts)

	# ping the up address of every network device that responded to broadcast
	for device_ip in discovered_devices_ip:

		# A) define a temporary connection at this network device's ip address
		radio_interface = SwiftRadioEthernet(host=device_ip)

		# B) attempt to connect to the device
		if radio_interface.connect():

			sysinfo = None
			radio_info = None

			# get sysinfo
			sysinfo = radio_interface.execute_command("sysinfo", timeout=1, fail_retries=3)

			if sysinfo["_error"] is None:

				# store radio's device id and ipv4 information
				radio_info = (sysinfo, device_ip)

				# add radio information to list of found radios (don't place duplicates in list)
				if radio_info not in swiftradio_list:
					swiftradio_list.append(radio_info)

		# D) delete the interface connection to this device
		radio_interface.disconnect()

		radio_interface = None

	return swiftradio_list

def device_verification(network_device, found_swiftradios, max_attempts=2):
	"""
	Description:
	Parameters:
	Return: device id string or None if device could not be found
	"""
	radio_found = False
	firmware_info = dict()
	attempts = 0

	while (radio_found == False) and (attempts < max_attempts):
		attempts += 1

		# send a Swift "sysinfo" command request
		sysinfo = network_device.execute_command("sysinfo", timeout=1, fail_retries=3)

		# check if device responded with a valid device ID
		if (sysinfo["id"] != None):

			# if found, store radio's device id and ipv4 information
			radio_found = True

			# get ip address
			connection_info = network_device.get_connection_info()
			network_device_ip = connection_info["host"]

			radio_info = (sysinfo, network_device_ip)

			# add radio information to list of found radios (don't place duplicates in list)
			if radio_info not in found_swiftradios:
				found_swiftradios.append(radio_info)

	return found_swiftradios

def network_broadcast(trace=-1, timeout=2, broadcasts=5):
	"""
	Description:
	Parameters:
	Return:
	"""
	hosts = dict()
	discovery_port=802

	if os.name == "nt":
		localhosts = socket.gethostbyname_ex('')[2]
	else:
		localhosts = list()
		localhosts.append('')

	swiftradio_iplist = list()

	for i in range(broadcasts):

		for localhost in localhosts:

			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.bind((localhost, 0))
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			sock.settimeout(timeout)
			sock.sendto("", ('<broadcast>', discovery_port))

			while 1:
				try:
					(buf, addr) = sock.recvfrom(32)
					hosts[len(hosts)] = addr[0]
				except socket.timeout:
					sock.close()
					break
				except:
					raise
				# print "'{}'".format(buf)
			for key in hosts:
				if hosts[key] not in swiftradio_iplist:
					swiftradio_iplist.append(hosts[key])

	return swiftradio_iplist

def swift_network_find(device_id):
	"""
	Find the IP address of the SWIFT device with the given device id.

	Parameters:	device_id - device identifier.

	Returns: ipv4 address of device or None if device was not found on network.

	Last Updated: 06/30/16 (SRA)
	"""
	swift_ip = None

	# get list of all swift devices connected to the network
	discovered_devices = swift_network_enumerate()

	# check if any discovered device has a matching device id.
	for devid, ip in discovered_devices:
		if devid == device_id:
			swift_ip = ip

	return swift_ip

def search_trace_output(output, current_tracelevel=0, msg_tracelevel=1, newline=1):
	"""
	Description: prints a output message to console. the current tracelevel must be set higher than the
				 message output tracelevel for the message to be printed
	Parameters: output message, tracelevel of output message, flag indicating if message should be terminated with a newline
				when printed (terminates with a space otherwise)
	Return: None
	"""

	if current_tracelevel >= msg_tracelevel:
		if newline == 0:
			# Note: stdout may not be portable across OS platforms
			sys.stdout.write(output)
		else:
			print output
