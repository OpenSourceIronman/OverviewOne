##
# @file hdlc.py
# @brief 
# @author Steve Alvarado <alvarado@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2014, Tethers Unlimited, Inc

import sys
import os
import time
import logging
import struct
import binascii
import crcmod

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Created: 7/20/15"

class HDLCCodec:
	"""
	Author: S. Alvarado
	Created: 7/20/15
	Description: 

	Notes: SWIFT HDLC Frame Format 	
			1. Frame Check Sequence
				- A 16-bit CRC-CCITT
				- Inverted bit-wise before insertion into the frame
				- Computed prior to octet stuffing
				- Covers the entire data frame frame, including the header elements and payload.
			2. NO PAYLOAD ZERO PADDING IS PRESUMED
	"""
	def __init__(self, sof_flag = '\x7E', eof_flag = '\x7E', escape = '\x7D', escapemask = '\x20', 
					crc_width = 2, crc_poly = 0x11021, endianess = "big", loglevel=logging.CRITICAL, 
					logfile="stdout"):
		"""
		Author: S. Alvarado
		Last Updated: 7/22/15 (SRA)		
		Description: Class constructor
		"""
		self._HDLC_SOF_FLAG 			= sof_flag 		# start of frame flag
		self._HDLC_EOF_FLAG 			= eof_flag 		# end of frame flag
		self._HDLC_ESCAPE 				= escape 		# character escape indicator
		self._ESCAPE_MASK				= escapemask 	# mask to XOR the escaped character
		self._HDLC_SOF_FLAG_ESCAPED 	= chr( ord(self._HDLC_SOF_FLAG) ^ ord(self._ESCAPE_MASK) )
		self._HDLC_EOF_FLAG_ESCAPED 	= chr( ord(self._HDLC_EOF_FLAG) ^ ord(self._ESCAPE_MASK) )
		self._HDLC_ESCAPE_ESCAPED 		= chr( ord(self._HDLC_ESCAPE) ^ ord(self._ESCAPE_MASK) )
		self._MIN_HDLC_FRAME_SIZE 		= 4
		self._CRC_WIDTH 				= crc_width 	# crc byte width (2 for CRC 16, 4 for CRC 32)
		self._CRC_POLY 					= crc_poly 		# polynomial representation (CCIT)
		self._endianess 				= endianess 	# data type endianess
		self._stream_parser = HDLCStreamFrameFinder(sof_flag, eof_flag, escape, escapemask, endianess)

		# determine where to save log messages
		if logfile == None:
			current_time = time.strftime( "%H%M_%m%d%y", time.localtime( time.time() ) )
			logging.basicConfig(format="[HDLC Codec] %(asctime)s %(levelname)s: %(message)s", datefmt='%m/%d/%y %H:%M:%S', filename="hdlc_codec_{}.log".format(current_time), level=loglevel)
		elif logfile == "stdout":
			logging.basicConfig(format="[HDLC Codec] %(asctime)s %(levelname)s: %(message)s", datefmt='%m/%d/%y %H:%M:%S', level=loglevel)			
		else:
			logging.basicConfig(format="[HDLC Codec] %(asctime)s %(levelname)s: %(message)s", datefmt='%m/%d/%y %H:%M:%S', filename=logfile, level=loglevel)

		self._logger = logging.getLogger(__name__)

	def encode(self, buf, length = None):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)
		Description: encoded a HDLC frame and return decoded data (HDLC payload without escaped bytes) as list.
		Parameters: buf - a list of bytes (string objects) that will be framed into a HDLC packet
					length - length of buf
		Return: an hdlc-encoded list of bytes (string objects)
		Notes: SWIFT HDLC Frame Format 	
			1. 
			2. Frame Check Sequence
				- A 16-bit CRC-CCITT
				- Inverted bit-wise before insertion into the frame
				- Computed prior to octet stuffing
				- Covers the entire data frame frame, including the header elements and payload.
			3. NO PAYLOAD ZERO PADDING IS PRESUMED
		"""	
		hdlc_frame = list()

		# define header fields
		header = list()
		header.append("\xFF") 		# address field (broadcast)
		header.append("\x03") 		# control field (UI frame)
		header.append("\x00") 		# PROTO field
		header.append("\x00")

		# define payload field
		payload = buf

		# [1] calculate crc, including the header and payload (before octet stuffing)
		crc16_int = self._calculate_crc16(header + payload)

		# [2] inverse the crc before you insert into frame
		crc16_int_inv = 0xFFFF ^ crc16_int
		
		# [3] convert crc into 2 byte list
		crc_buf = self._uint16_to_list(crc16_int_inv, endianess=self._endianess) 

		# [4] assemble unencoded HDLC frame

		# insert start of frame flag delimiter
		unencoded_frame = list()
		
		# insert header fields
		unencoded_frame += header

		# insert payload
		unencoded_frame += payload 

		# insert crc
		unencoded_frame += crc_buf

		# [5] encoded frame (octect stuff 0x7D and 0x7E)
		hdlc_frame = self._octect_stuff(unencoded_frame)

		# insert HDLC frame flag delimiter
		hdlc_frame.insert(0, self._HDLC_SOF_FLAG)
		hdlc_frame.append(self._HDLC_EOF_FLAG)

		# return HDLC frame to caller
		return hdlc_frame
				
	def decode(self, hdlc_frame, length=None): 
		""" 
		Author: S. Alvarado 
		Last Updated: 7/20/15 (SRA) 
		Description: decode a HDLC frame and return decoded data (HDLC payload without escaped bytes) as list.
		Parameters: buf - a list of bytes (string objects) that will be framed into a HDLC packet 
					length - length of buf 
		Return: - a list of bytes (string objects) without the HDLC frame information 
				OR
				- empty list if a valid HDLC packet was not found
		TODO: implement HDLC ADDR, CTRL, and PROTO processing logic
		"""	
		decoded_buffer = list()

		# make sure frame size is greater than the minimum
		if len(hdlc_frame) < self._MIN_HDLC_FRAME_SIZE:
			self._logger.warn("HDLC frame has a size of {}. Minimum size is {}. Dropping HDLC frame.".format(len(hdlc_frame), self._MIN_HDLC_FRAME_SIZE))
			return []
		
		# check frame delimiters
		if hdlc_frame[0] != self._HDLC_SOF_FLAG:
			self._logger.warn( "invalid start of frame delimiter {}. Must be {}. Dropping HDLC frame.".format(hex(ord(hdlc_frame[0])), hex(ord(self._HDLC_SOF_FLAG))) )
			return []
		if hdlc_frame[-1] != self._HDLC_EOF_FLAG:
			self._logger.warn( "invalid start of frame delimiter {}. Must be {}. Dropping HDLC frame.".format(hex(ord(hdlc_frame[0])), hex(ord(self._HDLC_EOF_FLAG))) )
			return []

		# [1] remove frame delimitors
		del hdlc_frame[0]
		del hdlc_frame[-1]

		# [2] decode HDLC frame (unstuff escaped bytes such as 0x7E and 0x7D)
		unpacked_hdlc_frame = self._unpack_frame(hdlc_frame)

		# [3] extract HDLC fields

		# get HDLC header field
		HEADER_WIDTH = 4
		header = unpacked_hdlc_frame[:HEADER_WIDTH]

		# get HDLC paylod (information) field, this will be what's returned if CRC's are good
		decoded_buffer = unpacked_hdlc_frame[HEADER_WIDTH: len(unpacked_hdlc_frame) - self._CRC_WIDTH]

		# get HDLC CRC field, invert the CRC checksum to conform with HDLC standard
		crc_field = unpacked_hdlc_frame[len(unpacked_hdlc_frame) - self._CRC_WIDTH:]
		crc_field[0] = chr( ord(crc_field[0]) ^ 0xFF )
		crc_field[1] = chr( ord(crc_field[1]) ^ 0xFF )

		# [4] Validate frame CRC checksums

		# convert crc buffer to an integer
		crc_int = self._list_to_uint16( crc_field, endianess = self._endianess )

		# validate crc checksum
		valid_crc = self._validate_crc16_ccitt(header + decoded_buffer, crc_int)


		# return decoded payload
		if valid_crc:
			return decoded_buffer
		else:
			return []


	def decode_stream(self, stream_buffer): 
		""" 
		Author: S. Alvarado 
		Last Updated: 7/20/15 (SRA) 
		Description: parses a continual stream of bytes and extracts the decoded HDLC frame payload.
		Parameters: stream_buffer - a list of bytes (string objects) that will be searched for HDLC frames
		Return: 0 - HDLC frame was not found in given buffer
				OR
				a list of bytes (string objects) without the HDLC header or escape bytes.
		"""
		return_data = list()

		# find HDLC packet
		for byte in stream_buffer:
			parser_state = self._stream_parser.process_byte(byte)
			if parser_state == "COMPLETE":
				return_data = self._stream_parser.get_hdlc_frame()
			# else:
			# 	print parser_state

		# decode HDLC packet and return
		if len(return_data) > 0:
			return self.decode(return_data, len(return_data) )
		else:
			return 0

	def _unpack_frame(self, buf):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description: unstuffed escaped bytes in HDLC frame
		Parameters: buf - a list of bytes containing the information field of the HDLC frame (including padding)
		Return: 
		NOTE: NO ZERO PADDING IS PRESUMED IN INFORMATION FIELD
		"""		
		decoded_buffer = list()

		# remove escape characters
		mask = False
		for byte in buf:

			# check if this byte is escape character
			if byte == self._HDLC_ESCAPE:

				# dont store in list and indicate that next byte should be XORed with escape mask
				mask = True

			# if not, store in list
			else:

				# if previous byte was an escape character mask this byte before storing
				if mask == True:
					masked_byte = chr( ord(byte) ^ ord(self._ESCAPE_MASK) )
					decoded_buffer.append( masked_byte )
					mask = False

				# otherwise, store as is
				else:
					decoded_buffer.append( byte )

		# return decoded buffer
		return decoded_buffer

	def _validate_crc32(self, hdlc_buf):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description:
		Parameters: length - number of bytes to read, defaults to 1
		Return: 
		"""		
		WIDTH = 4

		# make sure the frame is greater than the minimum size before continuing
		if len(hdlc_buf) < self._MIN_HDLC_FRAME_SIZE:
			self._logger.error( "Cannot calculate CRC 16, HDLC frame has a size of {}. Minimum size is {}. Dropping HDLC frame.".format( len(hdlc_frame), self._MIN_HDLC_FRAME_SIZE ) )
			return []

		# extract the hdlc frame's crc as a integer
		frame_crc = hdlc_buf[len(hdlc_buf) - WIDTH:]

		# convert to integer
		received_crc = self._list_to_uint32(frame_crc)

		# calculate crc 32 and return result
		calculated_crc = self._calculate_crc32( hdlc_buf[:len(hdlc_buf)-WIDTH] )

		return 1

		if received_crc == calculated_crc:
			return 1
		else:
			self._logger.warn( "invalid CRC 32 {}. Expected {}. Dropping HDLC frame.".format( hex(received_crc), hex(calculated_crc) ) )
			return 0

	def _validate_crc16_ccitt(self, buf, expected_crc):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description: 
		Parameters: length - number of bytes to read, defaults to 1 
		Return: 
		"""	
		# make sure the frame is greater than the minimum size before continuing
		if len(buf) < self._MIN_HDLC_FRAME_SIZE:
			self._logger.warn( "Cannot calculate CRC 16, HDLC frame has a size of {}, minimum size is {}. Dropping HDLC frame".format( len(buf), self._MIN_HDLC_FRAME_SIZE ) )
			return 0

		# calculate crc 32 and return result
		calculated_crc = self._calculate_crc16( buf )

		if expected_crc == calculated_crc:
			return 1
		else:
			self._logger.warn( "invalid CRC16-CCITT: {} (calculated: {}). Dropping HDLC frame. ".format( hex(expected_crc).zfill(6), hex(calculated_crc).zfill(6) ) )
			return 0

	def _calculate_crc32(self, buf):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description: read data from an opened connection
		Parameters: length - number of bytes to read, defaults to 1
					timeout - length of time, in seconds to wait for read data
		Return: read data - a list of byte objects representing the data read 
							from device. will be empty if no data was read in.
		"""		
		# convert buffer to string
		buffer_string = "".join( buf )

		# calculate crc 32 and return result (as positive integer)
		crc32 = binascii.crc32( buffer_string ) & 0xffffffff

		return crc32

	def _calculate_crc16(self, buf):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description: performs a 16-bit CRC-CCIT frame check sequence of the given buffer.
		Parameters: buf - buf used to calculate the crc value
		Return: crc16 - crc checksum value, as a integer 
		"""		
		CCITT_POLYNOMIAL = self._CRC_POLY
		crc16_calculator = crcmod.mkCrcFun(poly=CCITT_POLYNOMIAL, initCrc=0xFFFF, rev=False, xorOut=0x0000)

		# convert buffer to string
		buffer_string = "".join(buf)

		# calculate crc 32 and return result (as positive integer)
		crc16 = crc16_calculator( buffer_string )

		return crc16

	def _uint16_to_list(self, value, endianess="little"):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a python unsigned integer object into a list of bytes (string objects) in the specified Endianess
		Parameters: value - unsigned integer value to convert to list
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
		Return: list of bytes representing unsigned integer value
		"""						
		UINT_WIDTH = 2
		bytelist = list()

		if endianess == 'big' or endianess == 'network':
			bytelist = list(struct.pack("!I",value))
			bytelist = bytelist[(4-UINT_WIDTH):]
		elif endianess == 'little':
			bytelist = list(struct.pack("<I",value))
			bytelist = bytelist[:UINT_WIDTH]
		else:
			raise HDLCCODECError( "invalid Endianess type {}.".format( endianess ) )
			
		return bytelist	

	def _uint32_to_list(self, value, endianess="little"):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a python unsigned integer object into a list of bytes (string objects) in the specified Endianess
		Parameters: value - unsigned integer value to convert to list
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
		Return: list of bytes representing unsigned integer value
		"""						
		UINT_WIDTH = 4

		if endianess == 'big' or endianess == 'network':
			bytelist = list(struct.pack("!I",value))
			bytelist = bytelist[(4-UINT_WIDTH):]
		elif endianess == 'little':
			bytelist = list(struct.pack("<I",value))
			bytelist = bytelist[:UINT_WIDTH]
		else:
			raise HDLCCODECError( "invalid Endianess type {}.".format( endianess ) )
			
		return bytelist	

	def _int32_to_list(value, endianess='big'):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a python integer object into a list of bytes (string objects) in the specified Endianess
		Parameters: value - integer value to convert to list
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
		Return: list of bytes representing integer value
		"""		
		UINT_WIDTH = 4

		if endianess == 'big' or endianess == 'network':
			bytelist = list(struct.pack("!i",value))
		elif endianess == 'little':
			bytelist = list(struct.pack("<i",value))
		else:
			raise HDLCCODECError( "invalid Endianess type {}.".format( endianess ) ) 
			
		return bytelist	
	
	def _list_to_int32(self, bytelist, endianess='little'):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a list of bytes (string objects) into a Python integer
		Parameters: bytelist - a list of bytes
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
		Return: integer converted from byte list
		"""		
		INT_WIDTH = 4	
		return_int = self._list_to_uint32(bytelist, endianess)
		if return_int > (0xFFFFFFFF / 2):
			return_int -= (0xFFFFFFFF + 1) 					
		
		return return_int	

	def _list_to_uint32(self, bytelist, endianess="big"):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a list of bytes (string objects) into a Python unsigned integer
		Parameters: bytelist - a list of bytes
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of the list of bytes
		Return: unsigned integer converted from byte list
		"""			
		UINT_WIDTH = 4
		return_uint = 0x00000000

		if endianess == "little":
			bytelist = bytelist[::-1]
		
		for i in range(UINT_WIDTH):
			return_uint += ord( bytelist[i] ) << (8 * ( UINT_WIDTH - ( i + 1 ) ) )
			
		return return_uint		

	def _list_to_uint16(self, bytelist, endianess="big"):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a list of bytes (string objects) into a Python unsigned integer
		Parameters: bytelist - a list of bytes
					endianess - Endianess (https://en.wikipedia.org/wiki/Endianness) of bytelist
		Return: unsigned integer converted from byte list
		"""			
		UINT_WIDTH = 2
		return_uint = 0x00000000

		if endianess == "little":
			bytelist = bytelist[::-1]
		
		for i in range(UINT_WIDTH):
			return_uint += ord( bytelist[i] ) << (8 * ( UINT_WIDTH - ( i + 1 ) ) )
			
		return return_uint			


	def _octect_stuff(self, buf):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)	
		Description: convert a list of bytes into a list of bytes that has been octet stuffed with the 
					 appropriate escape sequences. See HDLC format for more info.
					 https://tools.ietf.org/html/rfc1662#section-4
		Parameters: buf - a list of bytes that will be octet stuffed.
		Return: octet-stuffed list of bytes.
		"""			
		new_buf = list()

		# remove escape characters
		stuff_byte = False

		for byte in buf:

			# check if this byte is a character that needs to be octet-stuffed
			if byte == self._HDLC_SOF_FLAG:
				stuff_byte = True
			elif byte == self._HDLC_EOF_FLAG:
				stuff_byte = True
			elif byte == self._HDLC_ESCAPE:
				stuff_byte = True				

			# stuff byte if necessary  
			if stuff_byte == True:

				# insert escape character into the new buffer
				new_buf.append(self._HDLC_ESCAPE)

				# insert new masked character
				masked_byte = chr( ord(byte) ^ ord(self._ESCAPE_MASK) )
				new_buf.append( masked_byte )				

				stuff_byte = False

			# otherwise, simply add to buffer
			else:

				new_buf.append( byte )
		
		return new_buf

class HDLCStreamFrameFinder:
	"""
	Author: S. Alvarado
	Created: 7/20/15
	Description: parses a continual stream of bytes and extracts HDLC frame
	NOTE: no HDLC packet size limit is enforced.
	"""		  	
	def __init__(self, sof_flag = '\x7E', eof_flag = '\x7E', escape = '\x7D', escapemask = '\x20', 
					crc_width = 2, crc_poly = 0x1021, endianess = "little"):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)		
		Description: Class constructor
		"""
		self._HDLC_SOF_FLAG 			= sof_flag 		# start of frame flag
		self._HDLC_EOF_FLAG 			= eof_flag 		# end of frame flag
		self._HDLC_ESCAPE 				= escape 		# character escape indicator
		self._ESCAPE_MASK				= escapemask 	# mask to XOR the escaped character
		self._HDLC_SOF_FLAG_ESCAPED 	= chr( ord(self._HDLC_SOF_FLAG) ^ ord(self._ESCAPE_MASK) )
		self._HDLC_EOF_FLAG_ESCAPED 	= chr( ord(self._HDLC_EOF_FLAG) ^ ord(self._ESCAPE_MASK) )
		self._HDLC_ESCAPE_ESCAPED 		= chr( ord(self._HDLC_ESCAPE) ^ ord(self._ESCAPE_MASK) )
		self._MIN_HDLC_FRAME_SIZE 		= 4
		self._CRC_WIDTH = crc_width 	# crc byte width (2 for CRC 16, 4 for CRC 32)
		self._CRC_POLY = crc_poly 		# polynomial representation (CCIT)
		self._endianess = endianess

		self._parse_states = ( 	"IDLE", 		# no bytes received.
								"SEARCHING", 	# bytes received search for start of frame flag.
								"BUFFERING", 	# saving bytes, searching for end of frame flag.
								"ESCAPED", 		# escape character received, waiting for next character.
								"COMPLETE") 	# HDLC frame has been successfully parsed.
		self.endianess = endianess 				# data type Endianess.
		self.state = "IDLE" 					# parser state
		self._hdlc_frame = None 				# once parser completes, contains an entire HDLC frame
		self._stream_buffer = list() 			# buffer of bytes received
		self._max_buffer_size = 0xFFFFFFFF

	def find_hdlc_frame(self, inbuf):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)		
		Description: add byte to stream buffer
		Return: 0 - hdlc frame not found in buffer
				list of bytes
		"""			
		pass

	def get_hdlc_frame(self):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)		
		Description: clears the stream buffer and resets parsing process
		Return: HDLC frame as a list of bytes
				OR
				NoneType object if hdlc frame has not yet been fully parsed
		"""	
		hdlc_frame = None

		# check if an HDLC frame is been fully stored
		if self.state == "COMPLETE":
			hdlc_frame = self._hdlc_frame

			# reset parser buffers and state
			self.state = "IDLE"
			self.decoded_frame = list()
			self._hdlc_frame = list()

		# return result
		return hdlc_frame

	def process_byte(self, byte):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)		
		Description: clear stream buffer and reset parsing state 
		Return: state of the parser, as a string
				"IDLE" - parser in idle state and no bytes have been processed
				"SEARCHING" - parser searching for HDLC start of frame character
				"BUFFERING" - start of frame received, searching for end of frame flag.
				"ESCAPED" - escaped character received, ignoring next byte
				"COMPLETE" - HDLC frame has been located and saved
		"""	
		# run parser state machine
		if self.state == "IDLE":
			self.state = "SEARCH"

		# check if byte is a start of frame flag
		if self.state == "SEARCH":
			if byte == self._HDLC_SOF_FLAG:

				# change to new state
				self.state = "BUFFERING"

				# add byte to HDLC frame
				self._hdlc_frame = list()
				self._hdlc_frame.append( byte )

		# store byte, check for end of frame flag or escaped characters
		elif self.state == "BUFFERING":

			self._hdlc_frame.append( byte )

			# check if this is a end of frame flag
			if byte == self._HDLC_EOF_FLAG:
				self.state = "COMPLETE"

				# clear stream buffer
				self._steam_buffer = list()

		# don't do anything if complete
		elif self.state == "COMPLETE":
			self._logger.warn( "parser in 'COMPLETE' state, please extract HDLC frame " )

		else:
			self._logger.error( "parser in unrecognized state: {}".format(self.state) )
			self.state

		return self.state

class HDLCCODECError(RuntimeError):
	"""
	Description:
	"""
	def __init__(self, error_msg):
		"""
		Description:
		Parameters: 
		"""
		self.error = str(error_msg)	

	def get_error(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		class_name = self.__class__.__name__
		return_error = "\n{}: {}".format(str(class_name), str(self.error))
		return return_error	

if __name__ == "__main__":

	def format_buf(buf):
		"""

		"""
		print_buf = list()
		for byte in buf:
			print_buf.append( hex(ord(byte))[2:].zfill(2)  )
		
		return " ".join(print_buf)

	buffer_in = [ "\xFD", "\xFB", "\xFA" ]
	DELIMITER = ["\x7E"]
	HEADER = ["\xFF", "\x03", "\x00", "\x21"]
	payload = list("123456\x7E789") 	
	crc16 = ["\x69","\x49"]
	hdlc_frame = DELIMITER + HEADER + payload + crc16 + DELIMITER
	buffer_in += hdlc_frame
	hdlc_codec = HDLCCodec()

	print "\nencoding buffer: {}".format( format_buf(payload) )
	encoded_buffer = hdlc_codec.encode( payload )
	print "HDLC encoded buffer: {}".format( format_buf(encoded_buffer) )

	print "\ndecoding buffer: {}".format( format_buf(encoded_buffer) )
	decoded_buffer = hdlc_codec.decode_stream( encoded_buffer )
	if decoded_buffer != 0:
		print "decoded buffer: {}".format( format_buf(decoded_buffer) )
	else:
		print "decoded buffer: **unable to decode**"