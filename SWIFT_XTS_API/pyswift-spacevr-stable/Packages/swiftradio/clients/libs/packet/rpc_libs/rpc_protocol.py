import datetime
from . import rpc_elements

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 10/30/14"

# RPC Control Sequence Protocol
# Rules
# - All command and parameter string names are converted to lower-case before computing the 16-bit Fletcher checksum.
# - All multi-byte fields are packed/unpacked in little-Endian byte order.
# - Command and response messages are always a multiple of 4-bytes.
# - Counting residual bytes, parameter and response data fields always consume a multiple of 4-bytes. The specified lengths may not be a multiple of 4-bytes.
# - If a protocol parser is in an idle state, the information needed to proceed will always be contained in the next 4-bytes.
# - Unknown parameters and responses can be ignored and safely skipped. This allows the protocol to be extended later without breaking compatibility with implemented clients.
# - A message frame will always start with either a SYNC, DESYNC, INVSYNC, or NOOP control sequence. After that, the ordering of elements is not important.
# - All client-host interactions initiated by a SYNC will always be terminated by a separate DESYNC message frame. This is true irregardless of any errors generated during the execution of the SYNC

class RPCMessageFrame:
	"""
	Description: low level wrapper class for parsing a raw buffer with rpc data and unpacking a fully populated wrapper to a 
				 raw buffer. provides various other useful utility functions as well (i.e. like printing frame contents)
	"""
	def __init__(self, frame_endianess = "little"):
		"""
		Description:
		Parameters: 
		"""
		self.frametype = self.__class__.__name__
		self.frame_endianess = frame_endianess

		# an rpc protocol element is defined as either a control sequence element or a command parameter element
		self.frame_element_list = list()				# [object, tag]
		self.frame_size = 0
		self.timestamp = 0

	#----------------------------------------------------------------------------------
	# public methods	
	#-----------------------------------------------------------------------------------
	def parse_raw_frame(self, raw_buffer, raw_buffer_length, endianess="little"):
		"""
		Description: process a raw rpc message bytelist. each element in message list is converted to it's equivalent
					 class and placed in the element list as received
		Parameters: 
		Return: 
		"""	
		rpc_elements_list = list()			# list of (hdr object, buffer, length) tuples
		tag_list = list()
		ctrl_hdr = None						#
		param_hdr = None					#
		parsing_done = 0 					#
		byte_ctr = 0      					#

		# define some values for error checking parsed data
		temp1 = rpc_elements.RPCControlSequenceHeader()
		CTRL_HDR_LEN = temp1.HEADER_LENGTH
		temp2 = rpc_elements.RPCParameterAndResponseHeader()
		PARAM_HDR_LEN = temp2.HEADER_LENGTH
		ctrl_hdr = rpc_elements.RPCControlSequenceHeader()
		sof_found = 0
		sof_marker = 0
		self.frame_size = 0

		# check that frame is large enough to parse (must be at least 4 bytes)
		if raw_buffer_length < CTRL_HDR_LEN:
			# print "**frame size error: received buffer size is {} bytes. minimum size is {} bytes (size of a control sequence header)**".format(raw_buffer_length, CTRL_HDR_LEN)
			return -1

		# [1] find start of message frame (this should be a indicated with a escape code 0xFF00, can use a ctrl_hdr to help with this)
		while (sof_found != 1) and (byte_ctr <= (raw_buffer_length - CTRL_HDR_LEN)):

			# A) parse a chunk of the input buffer and verify that this is a valid control sequence header
			buffer_chunk = raw_buffer[byte_ctr:]
			sof_found = ctrl_hdr.parse_raw_header(buffer_chunk, CTRL_HDR_LEN, endianess)

			# B) check if parsing attempt failed
			if sof_found != 1:
				# print "searching for next valid control sequence header..."
				ctrl_hdr = rpc_elements.RPCControlSequenceHeader()
				# move on to next byte
				byte_ctr += 1

			# C) otherwise, place control sequence information in rpc_elements list
			else:
				# 1. get the proper control sequence instance based on parsed header
				element_instance = None
				element_instance = self._get_ctrl_element(ctrl_hdr.get_ctrl_code_str(), endianess)

				# 2. populate the control sequence's header and info fields
				element_instance.set_header(ctrl_hdr)
				element_instance.parse_raw_info_fields(buffer_chunk[CTRL_HDR_LEN:], ctrl_hdr.data_length[1], endianess)

				# 3. generate a unique tag identifier for this element for easier accessing
				tag = self._generate_element_tag(element_instance, rpc_elements_list)

				# 4. store in list
				rpc_elements_list.append( (element_instance, tag, "control") )

				# 5. increment length counters (watch out for zero padding)
				sof_marker = byte_ctr
				byte_ctr += CTRL_HDR_LEN + ctrl_hdr.data_length[1]
				self.frame_size += CTRL_HDR_LEN + ctrl_hdr.data_length[1]
				if (self.frame_size%4) != 0:
					self.frame_size += (4-(self.frame_size%4))
				if (byte_ctr%4) != 0:
					byte_ctr += (4-(byte_ctr%4))

		# [2] parse rest of message frame
		if sof_found == 1:
			parsing_done = 0
			while (parsing_done == 0) and (byte_ctr <= (raw_buffer_length - CTRL_HDR_LEN)):
				# setup basic test variables
				ctrl_hdr = rpc_elements.RPCControlSequenceHeader()
				param_hdr = rpc_elements.RPCParameterAndResponseHeader()

				# A) parse a chunk of the input buffer and verify result
				buffer_chunk = raw_buffer[byte_ctr:]
				parse_result = ctrl_hdr.parse_raw_header(buffer_chunk, CTRL_HDR_LEN, endianess)
				
				# B) check if this is a control sequence
				if parse_result == 1:
					# 1. get the proper control sequence instance based on parsed header
					element_instance = None
					element_instance = self._get_ctrl_element(ctrl_hdr.get_ctrl_code_str(), endianess)

					# 2. populate the control sequence's header and info fields
					element_instance.set_header(ctrl_hdr)
					element_instance.parse_raw_info_fields(buffer_chunk[CTRL_HDR_LEN:], ctrl_hdr.data_length[1], endianess)

					# 3. generate a unique tag identifier for this element for easier accessing
					tag = self._generate_element_tag(element_instance, rpc_elements_list)

					# 4. store in list
					rpc_elements_list.append( (element_instance, tag, "control") )

					# increment length counters (watch out for zero padding)
					byte_ctr += CTRL_HDR_LEN + ctrl_hdr.data_length[1]
					self.frame_size += CTRL_HDR_LEN + ctrl_hdr.data_length[1]
					if (self.frame_size%4) != 0:
						self.frame_size += (4-(self.frame_size%4))
					if (byte_ctr%4) != 0:
						byte_ctr += (4-(byte_ctr%4))					

				# C) if not, check for a Named Response/Parameter
				else:
					parse_result = param_hdr.parse_raw_header(buffer_chunk, PARAM_HDR_LEN, endianess)

					if parse_result == 1:
						# 1. create a Name Response Parameter instance
						element_instance = None
						element_instance = rpc_elements.RPCParameterAndResponse(endianess)

						# 2. populate the header and data fields
						element_instance.set_header(param_hdr)
						element_instance.parse_raw_data_fields(buffer_chunk[PARAM_HDR_LEN:], param_hdr.data_length[1], endianess) 

						# 3. generate a unique tag identifier for this element for easier accessing
						tag = self._generate_element_tag(element_instance, rpc_elements_list)

						# 4. store in list
						rpc_elements_list.append( (element_instance, tag, "parameter/response") )

						# 5. increment length (watch out for zero padding)
						byte_ctr += PARAM_HDR_LEN + param_hdr.data_length[1]
						self.frame_size += PARAM_HDR_LEN + param_hdr.data_length[1]
						if (self.frame_size%4) != 0:
							self.frame_size += (4-(self.frame_size%4))
						if (byte_ctr%4) != 0:
							byte_ctr += (4-(byte_ctr%4))						
					else:
						# print "**a valid control sequence or named response element could be found. exiting parser...**"
						parsing_done = 1

		# ignore if frame is corrupt
		else:
			# if leading control sequence could be found, ignore this frame 
			# print "**leading control sequence could not be found. exiting parser...**"
			return -1
		
		self.frame_element_list = rpc_elements_list
		self.timestamp = self._timestamp_new_frame()
		return 1	

	def get_frame_control_code(self, code_type = "int"):
		"""
		Description: returns the control code of the first element in the frame. 
		Parameters: None 		
		Return: an unsigned integer value representing the transaction identifier. if transaction identifier 
				was not assigned, a integer value of 0 will be returned. a None object will be returned if
				frame does not have command hash field.	
		"""
		code = None

		if len(self.frame_element_list) > 0:
			element = self.frame_element_list[0][0]

		if element.__class__.__name__ != "RPCParameterAndResponse":
			if code_type == "str":
				code = element.get_control_code_str()
			else:
				code = element.get_control_code()

		return code

	def get_frame_control_sequence_name(self):
		"""
		Description: returns the leading control sequence (i.e. SYNC, DESYNC, INVSYNC) name as a string.
		Parameters: None
		Return: a string containing the leading control sequence name
		"""
		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			if etag in ["SYNC", "DESYNC", "INVSYNC", "NOOP"]:
				# search element for matching field name, get value
				return etag	
		return None

	def get_frame_command_hash(self):
		"""
		Description: returns the frame command hash.
		Parameters: None
		Return: an unsigned integer value representing the command hash. a None object will be returned if
				frame does not have command hash field.	
		"""
		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			if etag in ["SYNC", "DESYNC", "INVSYNC", "NOOP"]:
				# search element for matching field name, get value
				return element.get_field_val("name")	# note: returns -1 if field name DNE
		return None

	def get_frame_transid(self):
		"""
		Description: returns the frame transaction identifier. 
		Parameters: None 		
		Return: an unsigned integer value representing the transaction identifier. if transaction identifier 
				was not assigned, a integer value of 0 will be returned. a None object will be returned if
				frame does not have transid hash field.			
		"""
		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			if etag in ["SYNC", "DESYNC", "INVSYNC", "NOOP"]:
				# search element for matching field name, get value
				return element.get_field_val("transid")	# note: returns None if field name DNE
		return None

	def get_frame_elements(self):
		"""
		Description: returns a list of current elements in this frame
		Parameters: None
		Return: list of element information in the frame. Below is the list format:
				element_list = [element1, element2..., elementn]
				element = ( tag, [ field1, field2..., fieldn ] )
				field = (field_name, field_val)
		Note: the 'tag' in the element tuple will be a string representing the element name (i.e.
			  'DESYNC', 'SYNC', 'COMMAND DATA', 'INVSYNC'). the field name will also be a string representing
			  the name of the field (i.e. 'error', 'data')
		"""
		frame_elements_list = list()

		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			# get list of fields from this element 
			temp_list = element.get_fields()	
			
			frame_element = list()

			# note: this list will contain more information than will be returned
			for field in temp_list:
				frame_element.append( (field[0], field[1]) )

			# place this frame element in frame element list
			frame_elements_list.append( (etag, frame_element) )

		# return list to user
		return frame_elements_list

	def get_field(self, element_tag, field_name):
		"""
		Description: returns the field value for the specified element.
		Parameters: element_tag - name of the element
					field_name - name of the field
		Return: value of the specified field (data format depends on the field) or a None object if the 
				field could not be found within the frame.
		Example:
			error_code = packet.get_field("INVPARAM", "error")
		"""
		# iterate through each element in field for matching tag
		for element, etag, etype in self.frame_element_list:
			if etag == element_tag:
				# search element for matching field name, get value
				return element.get_field_val(field_name)	# note: returns -1 if field name DNE
		return None

	def get_elements(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		element_list = list()

		for element, tag, etype in self.frame_element_list:
			element_list.append(element)
			
		return element_list

	def get_element_tags(self):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		tag_list = list()
		for element, tag, etype in self.frame_element_list:
			tag_list.append(tag)

		return tag_list

	def get_command_parameter(self, command_parameter):
		"""
		Description: 
		Parameters: 
		Return: a CommandParameter instance if in message frame or a -1 if none exists
		Notes: there can only be one command parameter element per message frame
		"""
		# loop through to find any command parameter information in this frame
		pass

	def get_frame_timestamp(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""	
		return self.timestamp

	#----------------------------------------------------------------------------------
	# private methods	
	#-----------------------------------------------------------------------------------
	def _timestamp_new_frame(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		return datetime.datetime.now().strftime("%H:%M:%S.%f")

	def _generate_element_tag(self, element, element_list):
		"""
		Description:
		Parameters: 
		Return: 
		"""			
		new_tag = element.generate_default_tag()
		duplicate_tags = 0
		for element, tag, etype in element_list:
			if new_tag in tag:
				duplicate_tags += 1

		if duplicate_tags > 0:
			new_tag += str(duplicate_tags+1)

		return new_tag

	def _get_ctrl_element(self, control_code, endianess="little"):		
		"""
		Description:
		Parameters: 
		Return: 
		"""		
		element = None
		
		if control_code == "SYNC":
			element = rpc_elements.Sync(endianess)

		elif control_code == "DESYNC":
			element = rpc_elements.Desync(endianess)				

		elif control_code == "INVSYNC":
			element = rpc_elements.Invsync(endianess)				

		elif control_code == "NOOP":
			element = rpc_elements.Noop(endianess)								

		elif control_code == "CMDERR":
			element = rpc_elements.Cmderr(endianess)				

		elif control_code == "INVPARAM":
			element = rpc_elements.Invparam(endianess)				

		elif control_code == "NOARG":
			element = rpc_elements.Noarg(endianess)				

		elif control_code == "INVCMD":
			element = rpc_elements.Invcmd(endianess)

		elif control_code == "EXECTIME":
			element = rpc_elements.Exectime(endianess)				

		elif control_code == "THROTTLE":
			element = rpc_elements.Throttle(endianess)	

		else:
			element = -1

		return element

	def _populate_ctrl_element(self, control_code, raw_buffer, raw_buffer_length, endianess="little"):		
		"""
		Description:
		Parameters: 
		Return: 
		"""		

		return element

	def _zpad_size(self, control_code, raw_buffer, raw_buffer_length, endianess="little"):		
		"""
		Description:
		Parameters: 
		Return: 
		"""		

		return element		
