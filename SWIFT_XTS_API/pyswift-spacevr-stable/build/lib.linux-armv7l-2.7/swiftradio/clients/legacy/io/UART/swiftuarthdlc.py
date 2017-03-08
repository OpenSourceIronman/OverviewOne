import sys
import os
import time
import binascii
import serial
import logging
import platform
if __name__ == "__main__":
	import swiftuart
	import hdlc
else:
	from . import swiftuart
	from . import hdlc

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 7/20/15"

class SwiftUartHDLC(swiftuart.SwiftRawUART):
	"""
	Author: S. Alvarado
	Created: 7/20/15
	Description:
	"""
	def __init__(self, port, baudrate, timeout = 1, codec_loglevel=logging.CRITICAL, codec_logfile="stdout"):
		"""
		Author: S. Alvarado
		Last Updated: 7/24/15 (SRA)
		Description: Class constructor
		Parameters: port - Host COM port number (Windows), or device name (Unix).
					baudrate - serial data baud rate, must be an integer value
					timeout - port read/write timeout period in seconds
		"""
		self._port = port 				# COM Port Number or Device Name
		self._baudrate = baudrate 		# Baud rate
		self._connection_status = 0 	# opened/closed connection status
		self._timeout = timeout 		# default read/write timeout period in seconds
		self._hdlc_codec = hdlc.HDLCCodec(logfile=codec_logfile, loglevel=codec_loglevel)
		self._hdlc_stream_parser = hdlc.HDLCStreamFrameFinder()

		# create a serial object

		if platform.system() in ("Windows", "Microsoft"):
			if serial.VERSION[0] == "2":
				self._port = serial.Serial( port=( int( self._port ) - 1 ), baudrate=int( baudrate ), timeout = timeout )
			else:
				raise SwiftUartError("pyserial version {} not supported".format(serial.VERSION))
				self._port = serial.Serial( port= self._port , baudrate=int( baudrate ), timeout = timeout )
		else:
			self._port = serial.Serial( port=self._port, baudrate=int( baudrate ), timeout = timeout )

		# close port and don't reopen until the connect() method is called
		self._port.close()

	def write( self, buf, length = None ):
		"""
		Author: S. Alvarado
		Last Updated: 7/20/15 (SRA)
		Description: send data to a device via the opened connection.
		Parameters: buf - a list of data to be sent over connection
								   OR
 								   a string of data to be send over connection
					length - length of data to be written. Note that if length
							is None, all bytes in list will be written.
		Return: number of bytes written - positive non-zero integer representing number of
			   				   			  bytes sent to device
				0 - write attempt unsuccessful
			   -1 - length value invalid
		"""
		# encode buffer in HDLC format
		encoded_buffer = self._hdlc_codec.encode( buf, length )

		# write buffer via UART
		bytes_written = self._unencoded_write( encoded_buffer, length )
		return bytes_written

	def read_frame(self, timeout = 2):
		"""
		Author: S. Alvarado
		Updated: 7/20/15 (SRA)
		Description: parse an HDLC packet and return the decoded data contained in it's payload.
		Parameters: timeout - length of time, in seconds to wait for read data
		Return: buffer - a list of byte objects representing the data read via UART.
						The buffer will be decoded and free of any HDLC frame information and
						octet stuffing. Basically, the decoded HDLC frame payload is returned.
						The list will be empty if a frame could not be read before the timeout
						occurred.
		"""
		hdlc_packet_read = False
		hdlc_decoded_buffer = list()

		# setup timeouts
		listen_timeout = False
		current_time = time.time()
		end_time = current_time + int(timeout)

		# listen for response message by reading in one byte at a time stop
		# listening once the end-of-line character is read or a timeout occurs
		while (hdlc_packet_read == False) and (listen_timeout == False):

			# attempt to read byte via UART
			byte = self.read(1)

			# check if a byte was received
			if len( byte ) > 0:

				byte = byte[0]

				# if so, add byte to stream buffer and check if a HDLC frame has been received
				parser_state = self._hdlc_stream_parser.process_byte( byte )

				# if a HDLC frame has been received, process_byte() will return "COMPLETE"
				if parser_state == "COMPLETE":

					# once a frame has been found, get the HDLC frame
					hdlc_encoded_buffer = self._hdlc_stream_parser.get_hdlc_frame()

					# decode HDLC frame, the resulting buffer should be free of HDLC header and CRC info and
					# not contain any escaped byte sequences (octet stuffing).
					hdlc_decoded_buffer = self._hdlc_codec.decode( hdlc_encoded_buffer )

					# our HDLC data has been found and decoded, return to caller
					hdlc_packet_read = True

			# check if a timeout has occurred ( only if timeout parameter is specified )
			if end_time != None:

				# update time
				current_time = time.time()

				# check if listen period has expired
				if current_time >= end_time:
					listen_timeout = True

		# return the decoded data
		return hdlc_decoded_buffer

	def _unencoded_write(self, write_buffer, length = None):
		"""
		Author: S. Alvarado
		Last Updated: 5/8/15 (SRA)
		Description: send data to a device via the opened connection.
		Parameters: write_buffer - a list of data to be sent over connection
								   OR
 								   a string of data to be send over connection
					length - length of data to be written. Note that if length
							is None, all bytes in list will be written.
		Return: number of bytes written - positive non-zero integer representing number of
			   				   			  bytes sent to device
				0 - write attempt unsuccessful
			   -1 - length value invalid
		"""
		totalsent = 0
		msg_len = 0
		sent = 0

		# [1] check if connection is open
		if self.open_status() == 1:

			# [2] make sure the write_buffer is a list or string, return error code -1 if not
			if (type(write_buffer) is not list) and (type(write_buffer) is not str):
				return -1

			# convert the list to a string (socket library requires string objects for read/write operations)
			elif type(write_buffer) is list:
				write_buffer = "".join(write_buffer)

			# [3] determine size of data to send

			# use entire list size if length not specified
			if length == None:

				# set length value
				msg_len = len(write_buffer)

			# otherwise, use length value
			else:

				# error check length value
				if ( length < 0 ) or ( length > len(write_buffer) ):
					return -1

				# set length value
				msg_len = length

			# [4] send data to socket device
			while totalsent < msg_len:

				# write data
				sent = self._port.write(write_buffer[totalsent:msg_len])

				# if no data sent, exit while statement to prevent infinite loop
				if sent == 0:
					break

				# keep track of total bytes sent
				totalsent = totalsent + sent

		else:
			raise SwiftUartHDLCError("error writing to COM{}. please open connection using connect() before attempting write.".format(self._port))

		return int(totalsent)

class SwiftUartHDLCError(RuntimeError):
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

def hdlc_encode(func):
    """
    Author: S. Alvarado
    Last Updated: 7/20/15 (SRA)
    Description: A class method decorator for encoding HDLC data.
    """
    def hdlc_encode_decorator(self, write_buffer, length = None):
    	hdlc_codec = None
    	hdlc_encoded_buffer = hdlc_codec.encode(write_buffer, length)
        return func(self, hdlc_encoded_buffer, length)

    return hdlc_encode_decorator

def hdlc_decode(func):
    """
    Author: S. Alvarado
    Last Updated: 7/20/15 (SRA)
    Description: A class method decorator for decoding HDLC data.
    """
    def hdlc_decode_decorator(self, length = 1, timeout = 1):
    	hdlc_codec = None
    	hdlc_encoded_buffer = func(self, length, timeout)
    	decoded_buffer = hdlc_codec.decode(hdlc_encoded_buffer, length)
        return func(self, encoded_buffer, length)

    return hdlc_decode_decorator
