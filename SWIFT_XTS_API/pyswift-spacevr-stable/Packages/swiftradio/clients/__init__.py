"""
imports key sub packages, classes and functions for the swiftradio package
"""

# latest radio clients
from swiftradiointerface import SwiftRadioInterfaceV2
try:
	from ethernet.ethernet_client import SwiftRadioEthernet
except ImportError:
	pass
try:
	from ethernet.swiftudp import SwiftUDPClient
except ImportError:
	pass
try:
	from rs422.swiftuarthdlc import SwiftUartHDLC
except ImportError:
	pass
try:
	from rs422.rs422_client import SwiftRadioRS422
except ImportError:
	pass

# main radio <-> PC public interface classes
# legacy swift radio rpc client for backwards compatibility
from legacy.legacy import SwiftRadioInterface, SwiftRadioClient, SwiftRadioInstance

# SwiftPacket and SwiftPacketList public interface classes
from legacy.packet.Packet_Classes import SwiftPacket, SwiftPacketList
