from .rpc_libs import rpc_protocol
from ..utils import dataconversions
from ..utils import stringconversions
from ..utils import algorithms

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/25/14"

class SwiftPacket(rpc_protocol.RPCMessageFrame):
	"""
	Description: this is a subclass of the low level RPCMessageFrame class and the primary interface to higher level applications for accessing/storing information  
				within an rpc frame. this class differentiates itself from RPCMessageFrame by abstracting the more complex, low level methods and multi-step operations
				into "higher level" methods that are more convenient to call at the script or application level. As such, All RPC frames received by the radio are
				wrapped and stored as SwiftPacket instances which high level applications can later use as needed. Ideally, little to no knowledge of low level rpc 
				protocol is required to use any of the SwiftPacket methods.
	"""	
	#----------------------------------------------------------------------------------
	# public methods	
	#-----------------------------------------------------------------------------------
	def get_command_data(self, data_type = None):
		"""
		Description: searches packet (rpc frame) contents for data returned from the radio as a result of executing a radio command 
					 (rpc "response" element) and returns the data to caller if found. For example, if the radio receives a "time" 
					 command and returns an rpc frame containing "seconds" data, get_command_data will return the seconds data. Note that 
					 since the data type of all radio responses cannot be predetermined, this method returns the data as a raw list of hex 
					 bytes unless the data_type parameter is specified. 
		Optional Parameters: data_type - will attempt to convert the data field (which is a raw hex list by default) to specified data type. 
										 data_type values:
										 "uint" - converts 4 element hex list into a unsigned integer
										 "int" - converts 4 element hex list into a signed integer
										 "float" - converts 8 element hex list into a float value
										 "str" - converts a hex list of any length into a ascii string
										 "raw" - returns a list of hex object items (default)
		Return: A raw list of 'hex' objects or a value in the specified data format. If there is no command data 
				in the frame, a None object is returned instead.
		Note: if command data is found in the frame but cannot be converted according to specified data_type, the data is
			  returned in the default format (list of 'hex' bytes).
		"""
		return_data = None

		# check if this packet has any command response data (iterate through each "element" in rpc frame for a parameter/response element)
		for element, etag, etype in self.frame_element_list:

			# check if this element is a parameter/response element
			if etag == "COMMAND DATA":

				# search element for matching field name, get value
				raw_data = element.get_field_val("data", "info")	# note: returns -1 if field name DNE

				# check if field value was obtained
				if raw_data != -1:

					# if data_type specified, attempt to convert bytelist to desired data type
					if data_type != None:

						# convert bytelist
						return_data = dataconversions.convert_raw_bytelist(raw_data, data_type)

						# if bytelist could not be converted, just return raw bytelist
						if return_data == None:
							return_data = raw_data

					# otherwise, return the raw bytelist
					else:
						return_data = raw_data

		return return_data

	def get_command_data_by_name(self, name, data_type=None):
		"""
		Description: searches rpc frame for a "command data" element and returns the data if, and only if, the fletcher
					 of the name parameter matches the command data's hash value. 
		Optional Parameters: name - name of the response data. 
							 data_type - will attempt to convert the data field (which is a raw hex list by default)
										 to specified data type. 
										 valid data conversion data types:
										 "uint" - converts 4 element hex list into a unsigned integer
										 "int" - converts 4 element hex list into a signed integer
										 "float" - converts 8 element hex list into a float value
										 "str" - converts a hex list of any length into a ascii string
										 "raw" - returns the unmodified hex list as is
		Return: A raw list of 'hex' objects or a value in the specified data format. If there is no command data 
				in the frame or no matching command data hash was found, a None object is returned instead.
		Note: ** if command data is found in the frame but cannot be converted according to specified data_type, the raw 
			  'hex' list will be returned instead. **
		Example:
				...
				packetlist = Radio.execute("time")
				for packet in packetlist:
					seconds_data = packet.get_command_data_by_name("sec", "uint")
					if seconds_data != None:
						print "sec: {}".format(seconds_data)
				...
		"""
		command_data = None
		command_hash = None
		name_hash = None

		# get the command data hash in this frame
		command_hash = self.get_command_data_hash()

		# continue if a command hash value was found
		if command_hash != None:

			# convert the "name" parameter to a hash value
			name_hash = algorithms.fletcher16(name)

			# compare the name hash with the command data hash
			if name_hash == command_hash:

				# finally, get the command data in the format specified by "data_type"
				command_data = self.get_command_data(data_type)

		# return the command data
		return command_data

	def get_command_data_hash(self):
		"""
		Description: returns the hash name accompanying a command data field
		Parameters: None
		Return: integer representing the command data hash or a None object
				if not command data could be found
		"""
		hash = self.get_field("COMMAND DATA", "name")
		return hash

	def get_command_return_val(self):
		"""
		Description: returns the CMDERR value that is returned during a successful rpc command execution
					 transaction. this will be negative if an error state occurred during the execution of the command
					 or 0 otherwise.
		Parameters: None
		Return: integer representing the CMDERR return value.
		Note: if the radio experiences any error will attempting to execute a requested command, this value will be negative.
				a 0 value indicates the command was successfully executed.
		"""
		return_val = self.get_field("CMDERR", "value")
		return return_val		

	def get_error_info(self):
		"""
		Description: returns a complete list of error information. 
		Parameters: None
		Return: list containing error information in the rpc frame
				list format:
				error_list = [ error1, error2..., errorn ]
				error = (error_type, error_code, error_hash)
		"""
		errors_list = list()

		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			error_tag = element.generate_default_tag()
			
			if error_tag == "INVCMD":
				errors_list.append( (error_tag, None, self.get_frame_command_hash()) )

			elif error_tag == "NOARG":
				errors_list.append( (error_tag, None, element.get_field_val("param")) )

			elif error_tag == "INVPARAM":
				errors_list.append( (error_tag, element.get_field_val("error"), element.get_field_val("param")) )

			elif error_tag == "CMDERR":
				# per rpc protocol, only negative values represent an error 
				cmdinfo_val = element.get_field_val("value")
				if cmdinfo_val < 0:
					errors_list.append( ( error_tag, cmdinfo_val, self.get_frame_command_hash() ) )

		return errors_list			

	def print_contents(self, data_format=None):
		"""
		Description: prints low level udp information contained in packet
		Parameters: 
		Return: None
		Example: 
				...
				packetlist = Radio.execute("time")
				for packet in packetlist:
					packet.print_contents()
				...		
		"""		
		i = 0
		print "time stamp: {}".format(self.timestamp)
		print "frame size: {}".format(self.frame_size)
		print "frame elements: {}".format(len(self.frame_element_list))
		for element, tag, etype in self.frame_element_list:
			print ""
			print "element: {}".format(tag)
			print "type: {}".format(etype)
			element.print_fields()		
			i += 1	

	def print_packet_contents(self, data_format=None):
		"""
		Description: for legacy compatibility only, use print_contents() instead
		Parameters: 
		Return: 
		"""				
		self.print_contents(data_format)


class UdpDgramPacket:
	"""
	Description:
	"""	
	def __init__(self, name = "UdpDgramPacket"):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		self.name = name
		self.time_stamp = ""
		self.src_port = ""
		self.dest_port = ""
		self.src_addr = ""
		self.dest_addr = ""
		self.data = list()

	def get_packet_info(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		packet_info = dict()
		packet_info["packet_type"] = self.name
		packet_info["src_addr"] = self.src_addr
		packet_info["src_port"] = self.src_port
		packet_info["dest_addr"] = self.dest_addr
		packet_info["dest_port"] = self.dest_port
		packet_info["time_stamp"] = self.time_stamp

		return packet_info		

	def get_data(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		return self.data	

	def print_contents(self, data_format="raw"):
		"""
		Description: prints low level udp information contained in packet
		Parameters: 
		Return: None
		Example:
		"""			
		print "-- {} -- ".format(str(self.name))
		print "Time Stamp: " + str(self.time_stamp)
		print "Source: {}:{}".format(self.src_addr, self.src_port)
		print "Destination: {}:{}".format(self.dest_addr, self.dest_port)
		print "Data (raw): {}".format(self.data) + '\n'

	def print_packet_contents(self, data_format="raw"):
		"""
		Description: prints low level rpc information contained in packet
		Parameters: 
		Return: None
		"""
		self.print_contents(data_format)

	def set_data(self, data):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		self.data = data			

	def set_packet_info(self, src_addr, dest_addr, src_port, dest_port):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		self.src_addr = src_addr
		self.dest_addr = dest_addr		
		self.src_port = src_port
		self.dest_port = dest_port

	def set_time_stamp(self, time = ""):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		self.time_stamp = time


class SwiftPacketList(list):
	"""
	Description: The SwiftPacketList class was created to help automate the process of iterating through a 
				list of SwiftPacket objects in search of a specific piece of information or data (and simplify 
				code by removing redundant loop statements). SwiftPacketList objects are, in essence, slightly 
				modified versions of standard Python list objects (in fact, the SwiftPacketList class inherits 
				from the list() class) and are designed to store and handle one or more SwiftPacket objects. 
				All the standard attributes and methods that can be used with a standard python list (such as append()
				or insert() or using indexing syntax for fetching items in the list) are also available to SwiftPacketlist 
				objects. However, the SwiftPacketList class extends the base list class with a few additional methods that 
				aid in locating and extracting information contained in SwiftPackets stored within the SwiftPacketList. By 
				default, the SwiftRadioInterface methods execute() and get_packet_list() return a SwiftPacketList. 
	"""	
	def find_command_data(self, data_format=None, include_hash=True):
		"""
		Description: 
		Parameters: 
		Return: - a list of one or more items containing the command data requested in the 
				  data format specified.
				- a None object if no packet data could be found in list
		Note: this method is intended to work with SwiftPacket Objects only. A None object will always
				be returned for any other instance contained in the SwiftPacketList
		"""	
		found = False
		packet_data = list()

		# iterate through each packet in list and search for packets containing command data
		for i in range(self.__len__()):

			# extract packet from list
			packet = self.__getitem__(i)

			# make sure this is a SwiftPacket object
			if isinstance(packet, SwiftPacket):

				# try to extract specified command data from packet
				data = packet.get_command_data(data_format)

				# check if data was recovered
				if data != None:
					
					# save command data in list
					if include_hash:
						packet_data.append( (packet.get_command_data_hash(), data) )
					else:
						packet_data.append( data )

		# if data was found return list to caller
		if len(packet_data) > 0:
			return packet_data

		# otherwise, return None object	
		else:
			return None

	def find_command_data_by_name(self, cmd_data_name, data_format=None, all_matches=False):
		"""
		Description: 
		Parameters: 
		Return: - a list of one or more items containing the command data requested in the 
				  data format specified.
				- a None object if no packet data could be found  
		Note: this method is intended to work with SwiftPacket Objects only. A None object will always
				be returned for any other instance contained in the SwiftPacketList
		"""	
		found = False
		packet_data = list()

		# iterate through each packet in list and search for packets containing command data
		for i in range(self.__len__()):

			# extract packet from list
			packet = self.__getitem__(i)

			# make sure this is a SwiftPacket object
			if isinstance(packet, SwiftPacket):

				# try to extract specified command data from packet
				data = packet.get_command_data_by_name(cmd_data_name, data_format)

				# check if data was recovered
				if data != None:

					if all_matches == True:
						# save command data in list
						packet_data.append(data)
					else:
						return data

		# if data was found return list to caller
		if len(packet_data) > 0:
			return packet_data

		# otherwise, return None object	
		else:
			return None

	def find_error_info(self):
		"""
		Description: This method iterates through each SwiftPacket objects contained within a 
					 SwiftPacketList instance and searches for error data returned by radio. 
		Parameters: None
		Return: 
		Note: 
		"""	
		found = False
		error_info_list = list()

		# iterate through each packet in list
		for i in range(self.__len__()):

			# extract packet from list
			packet = self.__getitem__(i)

			# make sure this is a SwiftPacket object
			if isinstance(packet, SwiftPacket):

				# try to extract error info from packet
				data = packet.get_error_info(cmd_data_name, data_format)

				# check if data was recovered
				if data != None:

					# save command data in list
					error_info_list.append(data)

		# if data was found return list to caller
		if len(error_info_list) > 0:
			return error_info_list

		# otherwise, return None object	
		else:
			return None	

	def print_packet_info_all(self):
		"""
		Description: 
		Parameters: 
		Return:
		"""	
		found = False
		packet_data = list()
		packet_ctr = 0

		# iterate through each packet in list and search for packets containing command data
		for i in range(self.__len__()):

			# extract packet from list
			packet = self.__getitem__(i)

			# make sure this is a SwiftPacket object
			if isinstance(packet, SwiftPacket):

				# print the packet content information
				print "== RPC FRAME {} ==".format(i + 1)
				packet.print_contents()
				print "--\n"

	def print_rpc_info(self):
		"""
		Description: Prints low-level RPC message frame data of every SwiftPacket object to the console in a human-readable format. 
		Parameters: None
		Return: None
		"""	
		found = False
		packet_data = list()
		packet_ctr = 0

		# iterate through each packet in list and search for packets containing command data
		for i in range(self.__len__()):

			# extract packet from list
			packet = self.__getitem__(i)

			# make sure this is a SwiftPacket object
			if isinstance(packet, SwiftPacket):

				# print the packet content information
				print "[RPC FRAME {}]".format(i + 1)
				packet.print_contents()
				print "--\n"
