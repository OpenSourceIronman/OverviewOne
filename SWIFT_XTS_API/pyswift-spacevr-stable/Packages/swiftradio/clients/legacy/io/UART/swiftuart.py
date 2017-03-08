import sys, os, time
import serial

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 5/8/15"

class SwiftRawUART():
	"""
	Author: S. Alvarado
	Created: 4/2/15
	Description: 
	"""		
	def __init__(self, port, baudrate, timeout = 1):
		"""
		Author: S. Alvarado
		Last Updated: 5/8/15 (SRA)		
		Description: Class constructor
		Parameters: port - Host COM port number, must be an integer value
					baudrate - serial data baud rate, must be an integer value
					timeout - port read/write timeout period in seconds
		"""				
		self._port = port 		# COM Port Number
		self._baudrate = baudrate 		# Baud rate
		self._connection_status = 0 	# opened/closed connection status
		self._timeout = timeout 		# default read/write timeout period in seconds

		# create a serial object
		self._port = serial.Serial( port=( int( self._port ) - 1 ), baudrate=int( baudrate ), timeout = timeout )

		# close port and don't reopen until the connect() method is called
		self._port.close()

	def connect(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/8/15 (SRA)
		Description: open a connection to device. a connection must first be 
					 opened before commands can be sent.
		Return: 0 - connection could not be opened
				1 - connection successfully opened
		"""	
		if self._connection_status == 0:		
			self._port.open()
			self._connection_status = 1
			return 1
		else:
			return 0

	def close(self):
		return self.disconnect()
				
	def disconnect(self):
		"""
		Author: S. Alvarado
		Last Updated: 5/8/15 (SRA)
		Description: close a connection to device. note that a 0 will be returned
					 if you try to close a connection that is not open.
		Return: 1  - disconnection attempt successful or connection already closed
			   	0  - disconnection attempt failed   	
		"""				
		if self._connection_status == 1:		
			self._port.close()
			self._connection_status = 0
			return 1
		else:
			return 0

	def write(self, write_buffer, length = None):
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
			raise SwiftUartError("error writing to COM{}. please open connection using connect() before attempting write.".format(self._port))

		return int(totalsent)

	def read(self, length = 1, timeout = 1):
		"""
		Author: S. Alvarado
		Updated: 5/8/15 (SRA)
		Description: read data from an opened connection
		Parameters: length - number of bytes to read, defaults to 1
					timeout - length of time, in seconds to wait for read data
		Return: read data - a list of byte objects representing the data read 
							from device. will be empty if no data was read in.
		TODO: need to implement a timeout mechanism.
		"""	
		read_buffer = list()

		# check if connection is open
		if self.open_status() == 1:

			# read data
			read_buffer = list( self._port.read(length) )

			if len(read_buffer) < 1:
				read_buffer = list()
		else:
			raise SwiftUartError("error reading from COM{}. please open connection using connect() before attempting read.".format(self._port))
		
		# return data to user			
		return read_buffer

	def readline(self, timeout=None, eol="\n"):	
		"""
		Author: Steve Alvarado
		Description: reads in data from a socket port until an end-of-line character is found or a timeout
					 period specified by user is exceeded.
		Parameters: timeout - maximum listen period, in seconds. readline will actively listen until 
							  this timeout period expires or the eol character is read. If timeout is not 
							  specified (NoneType), readline will listen indefinitely for the eol character.
					eol - end of line character. readline will actively listen until this character
						 is read or a timeout occurs.
		Return: string containing data received from socket. string will be empty if no data was read.
		"""		
		line = list()
		line_read = False
		listen_timeout = False
		current_time = time.time()
		end_time = None	

		# setup timeout time
		if timeout != None:
			end_time = current_time + int(timeout)

		# listen for response message by reading in one byte at a time stop
		# listening once the end-of-line character is read or a timeout occurs
		while (line_read == False) and (listen_timeout == False):

			# attempt to read byte from socket
			ascii_char = self.read(1)

			# check if byte was received
			if len(ascii_char) > 0:

				# append message character to response message string
				line.append( ascii_char )
				
				# check if ascii character was the end of line
				if ascii_char == eol:
					line_read = True

			# check if a timeout has occurred (only if timeout parameter is specified)
			if end_time != None:

				# update time
				current_time = time.time()

				# check if listen period has expired
				if current_time >= end_time:
					listen_timeout = True

		# return the line as a string
		return "".join(line)

	def open_status(self):
		"""
		Author: S. Alvarado
		Updated: 5/8/15 (SRA)
		Description: get the open/closed status of the connection.
		Return: 0 - connection is closed
				1 - connection is open
		"""	
		return self._connection_status

	def __del__(self):
		"""
		Description:
		"""		
		if self.open_status():
			self.disconnect()		

class SwiftUartError(RuntimeError):
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
