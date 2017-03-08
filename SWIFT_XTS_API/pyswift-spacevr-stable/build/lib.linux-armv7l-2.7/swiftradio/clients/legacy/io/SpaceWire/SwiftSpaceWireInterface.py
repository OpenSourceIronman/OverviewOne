import traceback
if __name__ == '__main__':
	from Star_Dundee.Mk2.SpaceWire_USB_Brick import SpaceWireUSBBrickMk2
else:
	from .Star_Dundee.Mk2.SpaceWire_USB_Brick import SpaceWireUSBBrickMk2

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/07/14"

class SwiftSpaceWireInterface:
	"""
	Description:
	Parameters: 
	Return: 
	"""
	def __init__(self, identifier = 65536, rx_channel = 1, tx_channel = 1, end_of_packet = 1, mode = "interface"):
		"""
		Description:
		Parameters: device - unique identifier number corresponding to the spaceware-usb hardware brick
		Return: 
		"""
		self.spacewire_hardware = SpaceWireUSBBrickMk2(id = identifier)
		self.rx_channel = rx_channel 
		self.tx_channel = tx_channel
		self.open_channels = list()
		self.end_of_packet = end_of_packet 
		self.mode = mode
	
	def connect(self, trace=0):
		"""
		Description:
		Parameters: 
		Return: True - successful connection
				false - failed to connect
		"""
		# verify that a spacewire_hardware instance exists 
		if self.spacewire_hardware != None:		

			# attempt to open a new channel
			opened_channel = self.spacewire_hardware.open_channel(self.rx_channel)

			# verify that the channel was opened
			if opened_channel >= 0:
				self.open_channels.append(opened_channel)
				return True

		return False
		
	def close(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""
		i = 0
		channels_closed = 0
		channels_opened = len(self.open_channels)
		open_channels_list = self.open_channels

		# verify that a spacewire_hardware instance exists 
		if self.spacewire_hardware != None:

			# iterate through open channel list, and close each channel
			for channel in open_channels_list:
				closed = self.spacewire_hardware.close_channel(channel)

				# increment this counter for later comparison
				if closed == 1:
					channels_closed += 1

					# delete channel from list
					del self.open_channels[i]
				i += 1

			# verify that all channels were successfully closed, return result
			if channels_closed == channels_opened:
				return 1

		return -1
		
	def is_open(self):
		"""
		Description:
		Parameters: 
		Return: 
		"""		
		if len(self.open_channels) > 0:
			return True
		else:
			return False

	def write(self, write_buffer, length = 0, auto_lf = False):
		"""
		Description:
		Parameters: write_buffer - a list of hex objects
		Return: 
		"""
		# convert list into a string (star dundee space wire drivers require this)
		if len(write_buffer) > 0:

			# insert channel number into the list
			write_buffer.insert(0, chr(self.tx_channel))
			
			# convert list to string
			write_buffer = "".join(write_buffer)

			# write_buffer = "\x01\x31\x32\x33\x34\x35"
			length = len(write_buffer)
			
			# make sure there are open channels to write to
			if len(self.open_channels) > 0:
				open_channel = self.open_channels[0]
				result = self.spacewire_hardware.transmit_packet(write_buffer, length, channel = open_channel, 
																		end_of_packet = self.end_of_packet)
				return result

		return -1
	
	def read(self, max_length = 65535, timeout = 1):
		"""
		Description:
		Parameters:
		Return: a list of hex objects
		"""
		raw_buffer = []

		# make sure they are open channels to read from
		if len(self.open_channels) > 0:

			# get the open channel value
			open_channel = self.open_channels[0]

			# attempt to read bytes from the spacewire interface
			raw_buffer = self.spacewire_hardware.receive_packet(timeout = timeout*1000, channel = open_channel)
			
			# check if any byte were read in
			if len(raw_buffer) > 0:

				# convert the hex string into a list of hex bytes
				raw_buffer = list(raw_buffer)

			else:
				# return an empty list if an empty string was received
				raw_buffer = []

		return raw_buffer

	def __del__(self):
		"""
		Description: class destructor function
		Parameters: 
		Return: 
		"""
		if self.is_open() == True:
			self.close()


if __name__ == "__main__":
	try:
		radio_spacewire_interface = SwiftSpaceWireInterface()
		bytes = ""
		packet_data = "\x01\x04\x00\x00\x00"
		packet_len = 5
		
		radio_spacewire_interface.connect()

		# transfer_status = radio_spacewire_interface.write(packet_data, packet_len)
		while (1):
			bytes = radio_spacewire_interface.read(3)
			# print bytes.raw,

		radio_spacewire_interface.close()

	except KeyboardInterrupt:
		print "\n**Keyboard Interrupt Detected**\n"
		print "exiting program..."		
	except:
		traceback.print_exc()