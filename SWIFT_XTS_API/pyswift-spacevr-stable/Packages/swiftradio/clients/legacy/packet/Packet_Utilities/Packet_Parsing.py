from .. import Packet_Classes

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__status__ = "Development"
__date__ = "Late Updated: 11/14/14"
 
def rawbytelist_to_swiftpacket(buffer, buffer_size, time_stamp = None, bytelist_endianess="little"):
	"""
	Description: 
	Parameters: A bytelist or list of Byte Objects. Because the framing layer, which wraps the radio
				specific data, contains no information relevant to the parsing process (and is often subject to change),
				the input bytelist should only contain radio data starting with the escape code.
	Return: a SwiftPacket instance or a negative value indicating an invalid frame
	"""
	Packet = None
	parse_result = 0
	Packet = Packet_Classes.SwiftPacket()
	parse_result = Packet.parse_raw_frame(buffer, buffer_size, bytelist_endianess)
	
	if (parse_result != 1):
		Packet = -1

	return Packet

if __name__ == '__main__':
	pass
