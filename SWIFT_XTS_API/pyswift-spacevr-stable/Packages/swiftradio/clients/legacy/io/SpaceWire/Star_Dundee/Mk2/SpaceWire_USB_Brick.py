import time
import traceback
import ctypes
from ..Star_System import Star_API_Lib, RMAP_Packet_Lib, Device_Config_Lib
from .Utils.Mk2_Error import Mk2Error

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/06/14"

class SpaceWireUSBBrickMk2:
	"""
	Description:
	Parameters: 
	Return: 
	"""
	def __init__(self, id = None, maxbuffer_size = 256):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		# get star system python drivers
		self.star_api_driver = Star_API_Lib.StarApiLib(maxbuffer_size)
		self.rmap_packet_driver = RMAP_Packet_Lib.RMAPPacketLib()
		self.device_config_driver = Device_Config_Lib.DeviceConfigLib()

		# set the device ID for this Mk2 unit
		if id == None:
			self.identifier = self._identify_this_device()
		else:
			self.identifier = id

		self.maxbuffer_size = maxbuffer_size


	# ========================================================================================
	# Public Methods
	# ========================================================================================
	def close_channel(self, channel):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		# close opened channel to spacewire device
		channel_closed = self.star_api_driver.star_api_closeChannel(channel)

		# make sure channel is confirmed to be closed (0 indicates channel was not closed)
		if channel_closed == 0:
			raise Mk2Error("error in closing channel {}. channel was not open or has already been closed".format(channel))
			return -1

		return 1

	def open_channel(self, channel, direction = None, isQueued = None):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		CHANNEL_DIRECTION = {"STAR_CHANNEL_DIRECTION_IN":1, "STAR_CHANNEL_DIRECTION_OUT":2, "STAR_CHANNEL_DIRECTION_INOUT":3}
		direction = CHANNEL_DIRECTION["STAR_CHANNEL_DIRECTION_INOUT"]
		device_id = self.identifier
		channel_number = channel
		isQueued = 1
		
		# open a channel to spacewire device
		opened_channel = self.star_api_driver.star_api_openChannelToLocalDevice(device_id, direction, channel_number, isQueued)

		# make sure channel is open
		if opened_channel == 0:
			raise Mk2Error("A channel to local device could not be opened.")
			return -1

		# print "channel open: {}".format(opened_channel)
	
		return opened_channel

	def transmit_packet(self, packet, packet_size, timeout=5000, channel = 65539, end_of_packet = 1):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		EOP = {"STAR_EOP_TYPE_INVALID":0, "STAR_EOP_TYPE_EOP":1, "STAR_EOP_TYPE_EEP":2, "STAR_EOP_TYPE_NONE":3}
		TRANSFER_STATUS = {"STAR_TRANSFER_STATUS_NOT_STARTED":0, "STAR_TRANSFER_STATUS_STARTED":1, "STAR_TRANSFER_STATUS_COMPLETE":2,
							"STAR_TRANSFER_STATUS_CANCELLED":3, "STAR_TRANSFER_STATUS_ERROR":4}
		transmit_successful = False
		channel_number = channel
		
		# transmit packet
		trans_status = self.star_api_driver.star_api_transmitPacket(channel_number, packet, packet_size, end_of_packet, timeout)
		
		# return back transmission completion/failure value
		if trans_status == TRANSFER_STATUS["STAR_TRANSFER_STATUS_COMPLETE"]:
			transmit_successful = True

		return transmit_successful

	def receive_packet(self, timeout=5000, channel = 1, end_of_packet = 1):
		"""
		Description:
		Parameters: 
		Return: a tuple containing the packet data returned and the length of the data
		"""
		return_data = list()
		TRANSFER_STATUS = {"STAR_TRANSFER_STATUS_NOT_STARTED":0, "STAR_TRANSFER_STATUS_STARTED":1, "STAR_TRANSFER_STATUS_COMPLETE":2,
							"STAR_TRANSFER_STATUS_CANCELLED":3, "STAR_TRANSFER_STATUS_ERROR":4}
		channel_number = channel
		isQueued = 1

		# receive packet
		rx_status, rx_data, rx_data_len = self.star_api_driver.star_api_receivePacket(channel_number, end_of_packet, timeout)
		
		# return back transmission completion/failure value
		if rx_status == TRANSFER_STATUS["STAR_TRANSFER_STATUS_COMPLETE"]:
			if rx_data_len <= self.maxbuffer_size:
				return_data = rx_data[:rx_data_len]
			else:
				return_data = rx_data[:self.maxbuffer_size]
		else:
			return_data = []

		return return_data

	def reset(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		reset_result = None
		# reset the device
		reset_result = self.star_api_driver.star_api_resetDevice(self.identifier)
		
		return reset_result

	# ========================================================================================
	# Private Methods
	# ========================================================================================
	def _identify_this_device(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		device_id = None

		# get a device id list of all the SpaceWire Bricks on SpaceWire bus
		device_id_list = self.star_api_driver.star_api_getDeviceList()

		# find the device id for this brick
		if device_id_list != None:

			# if multiple devices are on this network, throw error.
			if len(device_id_list) > 1:
				raise Mk2Error("Multiple SpaceWire Devices detected! " + 
								"Unable to determine which to device to connect to. \n" +
								"It is recommended that the desired device's ID be passed to " + 
								"a SpaceWireUSBBrickMk2 instance to avoid multiple device conflicts.")	
			# otherwise, a single device has been detected
			else:
				# assign a device id to this hardware
				device_id = device_id_list[0]
		else:
			raise Mk2Error("unable to communicate with SpaceWire Mk2 device!")

		return device_id

	# def __del__(self):
	# 	"""
	# 	Description: class destructor function
	# 	Parameters: 
	# 	Return: 
	# 	"""
	# 	pass		


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



	