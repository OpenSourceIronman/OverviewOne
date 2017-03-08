from ...utils.dataconversions import bytelist_to_uint, bytelist_to_float
from ...utils.dataconversions import float_to_bytelist, uint_to_bytelist

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 6/25/14"

def wrap_swiftmsg_data(swift_msg_buffer, framing_protocol="test"):
	"""
	Parameters:
	Returns: 
	"""
	if framing_protocol == "test":
		SYNC1 = '\x35'
		SYNC2 = '\x2E'
		SYNC3 = '\xF8'
		SYNC4 = '\x53'
		HT_OFFSET = '\x04'
		HT_ID = '\xF2'
		FRAME_BYTES = 8 	#number of frame bytes (excluding sync characters)
		frame_buffer = list()
		
		#[1] Insert Frame Sync Characters	
		frame_buffer.append(SYNC1)
		frame_buffer.append(SYNC2)
		frame_buffer.append(SYNC3)
		frame_buffer.append(SYNC4)
		#[2] Insert Frame Header Info
		frame_buffer.append(HT_OFFSET)	#payload field offset
		frame_buffer.append(HT_ID)		#unused field
		frame_size = (FRAME_BYTES + len(swift_msg_buffer))	
		frame_buffersize_list = uint_to_bytelist(frame_size, bytelist_size=2)
		frame_buffer.append(frame_buffersize_list[0])	#payload field offset
		frame_buffer.append(frame_buffersize_list[1])
		#[3] Insert Message Payload
		for i in range(len(swift_msg_buffer)):
			frame_buffer.append(swift_msg_buffer[i])
		#[4] Insert Frame Checksums (FF's for now)
		for i in range(4):
			frame_buffer.append('\xFF')
	elif framing_protocol == "UDP":
		pass
	elif framing_protocol == "TCP/IP":
		pass
	else:
		pass
	return frame_buffer	


		
if __name__ == '__main__':
	# full_frame = [0x35,0x2E,0xF8,0x53,
					# 0x04,0xF2,0x00,0x14,
					# 0xF9,0xA3,0x00,0x00,
					# 0x81,0x22,0x00,0x04,
					# 0x00,0x00,0x00,0x17,
					# 0xFF,0xFF,0xFF,0xFF]

	pass	
					