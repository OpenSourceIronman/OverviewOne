import time
import ctypes
import os
from .Utils.Star_System_Error import StarSystemError
from .Utils import User_Platform
from ctypes import cdll, create_string_buffer
from ctypes import byref, c_char_p, c_uint, c_void_p, c_int, c_ubyte

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/06/14"

class StarApiLib:
	"""
	Description: 
	Parameters: 
	Return: 
	"""
	def __init__(self, max_buffer):
		"""
		Description: 
		Parameters: 
		Return: 
		"""
		# binary executable name
		self.bin_lib_name = "star-api"

		# find binary executable and load it into python module
		self.star_api_python = self._load_binary_executable(self.bin_lib_name)

		# receive buffer to store incoming information
		self.rx_buffer = ctypes.create_string_buffer(100)
	
	# ========================================================================================
	# Public Methods
	# ========================================================================================
	def star_api_transmitPacket(self, channelId, pPacketData, packetLength, eopType, timeout):
		"""
		Description: uses SpaceWire Brick's api drivers to transmit a packet of data
		Parameters: channelId -	The identifier of a previously opened channel. The channel must have 
								been opened as an out or in/out channel
					pPacketData - A pointer to a previously allocated buffer which should contain the 
									packet to be transmitted
					packetLength - The length of the buffer, and therefore the length of the packet
					eopType	- The end of packet marker type to be added to the end of the packet
					timeout - The maximum time in milliseconds to wait for the packet to be transmitted, or -1 to wait indefinitely
		Return: transfer status
				0 - STAR_TRANSFER_STATUS_NOT_STARTED 
				1 - STAR_TRANSFER_STATUS_STARTED
				2 - STAR_TRANSFER_STATUS_COMPLETE 
				3 - STAR_TRANSFER_STATUS_CANCELLED 
				4 - STAR_TRANSFER_STATUS_ERROR
		"""
		# load the transmit function from the dll
		tx_packet_fct = self.star_api_python.STAR_transmitPacket

		# now define the function's parameters (which will be c types)
		tx_packet_fct.argtype = [c_uint, c_void_p, c_uint, c_uint, c_uint]

		# define the function return value ()
		tx_packet_fct.restype = c_int

		# call the function to transmit the packet
		ret = tx_packet_fct(channelId, pPacketData, packetLength, eopType, timeout)

		return ret

	def star_api_receivePacket(self, channelId, pEopType = 1, timeout = 5000):
		"""
		Description: uses SpaceWire Brick's api drivers to Receive a single packet on a previously 
					 opened channel
		Parameters: channelId -	The identifier of a previously opened channel. The channel must have 
								been opened as an out or in/out channel
					pPacketData	- Pointer to a previously allocated buffer which will be updated to contain the received packet
					pPacketLength - Pointer to a variable which should contain the length of the buffer, and which will be updated to contain the length of the packet
					pEopType - Pointer to a variable which will be updated to contain the end of packet marker type of the packet
					timeout	- The maximum time in milliseconds to wait for the packet to be received, or -1 to wait indefinitely
		Return: status
				0 - STAR_TRANSFER_STATUS_NOT_STARTED 
				1 - STAR_TRANSFER_STATUS_STARTED
				2 - STAR_TRANSFER_STATUS_COMPLETE 
				3 - STAR_TRANSFER_STATUS_CANCELLED 
				4 - STAR_TRANSFER_STATUS_ERROR
		"""
		# rx_buffer = ctypes.create_string_buffer(10)
		length = len(self.rx_buffer)
		packet_length = c_uint(length)

		# [1] load the receive function from the dll
		rx_packet_fct = self.star_api_python.STAR_receivePacket

		# [2] define the function's parameters (channel, packet, packet len, eop, timeout)
		rx_packet_fct.argtype = [c_uint, c_void_p, c_void_p, ctypes.POINTER(c_uint), c_uint]

		# [3] define the function return value (status integer)
		rx_packet_fct.restype = c_uint

		# call the function 
		ret = rx_packet_fct(channelId, self.rx_buffer, byref(packet_length), byref(c_uint(pEopType)), timeout)

		return ret, self.rx_buffer.raw, packet_length.value

	def star_api_openChannelToLocalDevice(self, device, direction, channelNumber, isQueued):
		"""
		Description: Open a channel to a device on the specified channel number.
		Parameters: device - the device to attach to
					direction - whether this channel is for transmitting data from this application 
								or receiving data into it, or both. 
					channelNumber - the channel number on the device to attach to
					isQueued - whether traffic received on this channel should be buffered if there is no 
								receive op waiting to receive it
		Return: Channel identifier of new channel or 0 if an error occurred
		"""
		# CHANNEL_DIRECTION = {"STAR_CHANNEL_DIRECTION_IN":1, "STAR_CHANNEL_DIRECTION_OUT":2, "STAR_CHANNEL_DIRECTION_INOUT":3}

		# load the function from the dll
		open_device_channel = self.star_api_python.STAR_openChannelToLocalDevice

		# now define the function's parameters (which will be c types)
		open_device_channel.argtype = [c_uint, c_uint, c_ubyte, c_uint]

		# define the function return value (again, ctype)
		open_device_channel.restype = c_uint

		# call the function to execute
		ret_channel_id = open_device_channel(device, direction, channelNumber, isQueued)	

		return ret_channel_id

	def star_api_closeChannel(self, channelid):
		"""
		Description: Close a previously opened channel.
		Parameters: channelid - Channel to close
		Return: close channel status
				1 - channel was successfully closes
				0 - channel could not be closed (it was not open or has already been closed)
		"""
		# load the function from the dll
		close_device_channel = self.star_api_python.STAR_closeChannel

		# now define the function's parameters (which will be c types)
		close_device_channel.argtype = [c_int]

		# define the function return value (again, ctype)
		close_device_channel.restype = c_int

		# call the function to execute
		ret = close_device_channel(channelid)

		return ret		

	def star_api_getDeviceList(self):
		"""
		Description: Gets a list containing the device id's for all space wire devices present 
		Parameters: 
		Return: Array of identifiers for all devices present.
		Note: 	This function returns a snapshot of the current state of the system and is not automatically 
				updated. This array must be freed using STAR_destroyDeviceList when no longer required.
		"""
		count = c_int()
		ret_device_id_list = list()
		device_list = ctypes.POINTER(c_int)
		
		# load the function from the dll
		get_device_list_fct = self.star_api_python.STAR_getDeviceList

		# now define the function's parameters (which will be c types)
		get_device_list_fct.argtype = [c_void_p]

		# define the function return value (again, ctype)
		get_device_list_fct.restype = ctypes.POINTER(c_int)

		# get devices (note: this will be multiple void pointers)
		device_list = get_device_list_fct(byref(count))
		
		if device_list != None:
			# deference void pointers and store values in list
			for i in range(count.value):
				ret_device_id_list.append(device_list[i])

			# *** NOTE: this device id void array must be destroyed. this procedure is done at this level 
			# using the star_api_destroyDeviceList function to avoid higher level wrappers having to deal 
			# with low level data types (i.e. c_type void pointers) and memory management ****
			destroy_device_list_fct = self.star_api_python.STAR_destroyDeviceList
			destroy_device_list_fct.argtype = [ctypes.POINTER(c_int)]
			destroy_device_list_fct(device_list)
		else:
			ret_device_id_list = None

		# print ret_device_id_list
		return ret_device_id_list

	def star_api_destroyDeviceList(self, pDeviceList):
		"""
		Description: Frees a device list previously created by a call to STAR_getDeviceList or STAR_getDeviceListForDriver
		Parameters: pDeviceList	- the device list to be freed
		Return: 
		"""
		# load the function from the dll
		destroy_device_list_fct = self.star_api_python.STAR_destroyDeviceList

		# now define the parameters (which will be c types)
		destroy_device_list_fct.argtype = [c_void_p]

		# destroy devices 
		destroy_device_list_fct(pDeviceList)

	def star_api_resetDevice(self, deviceId):
		"""
		Description: resets the device
		Parameters: deviceId - Device to be reset
		Return: 1 if the device was successfully reset, else 0
		"""
		reset_result = None

		# load the function from the dll
		reset_device_fct = self.star_api_python.STAR_resetDevice

		# define the parameters
		reset_device_fct.argtype = [c_int]

		# reset devices 
		reset_result = reset_device_fct(deviceId)

		return reset_result

	# ========================================================================================
	# Private Methods
	# ========================================================================================
	def _load_binary_executable(self, bin_lib_name):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		# get path to the correct binary (note: this will differ depending on OS)
		bin_lib_path = User_Platform.get_starsystem_bin_lib_path(current_dir = os.path.dirname(os.path.realpath(__file__)), bin_name = bin_lib_name)

		# if binary could not be located, raise error
		if bin_lib_path == None:
			raise StarSystemError("error finding binary path for {}".format(bin_lib_name))

		# load binary executable library into python module
		python_lib_module = cdll.LoadLibrary(bin_lib_path)	

		return python_lib_module


if __name__ == "__main__":
	api_wrapper = StarApiLib()
	channel = 1
	packet_data = create_string_buffer("\x01\x04\x00\x00\x00", 5)
	packet_len = 5
	eop_type = 3
	timeout_ms = 5000

	transfer_status = api_wrapper.transmit_packet(channel, packet_data, packet_len, eop_type, timeout_ms)

	# print transfer_status

	#goodbye !
	raw_input("press enter to continue")



	