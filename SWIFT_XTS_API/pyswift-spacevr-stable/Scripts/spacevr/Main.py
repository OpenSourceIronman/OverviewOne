#!/usr/bin/env python

##@package Main
# An example main driver program to excerise SWIFT radio 
#
# The UDP connection between the Beagle Bone Black (BBB) and the SWIFT-XTS
# S-Band Transmitter is done via the SpaceVR_Configuration_Connection_Telemetry.py 
# script. 
#
# The transfer of a file (.JPEG or .TXT) from BBB or mCOM10K1 memory to 
# the SWIFT-XTS memory is done via the TransferFile.py script. 
# 
# The RF transmission out of the SWIFT-XTS radio is also done via the TransferFile.py script. 
#
# @note This does not excerise the X-Band transmitter (only S-Band Tx)

__author__ =  "Blaze Sanders"
__email__ =   "blaze@spacevr.co"
__company__ = "Space Virtual Reality Corp."
__status__ =  "Development"
__date__ =    "Late Updated: 2017-03-06"
__doc__ =     "An example main driver program to excerise SWIFT radio Test Case #1"


import sys, time, traceback, argparse
from swiftradio.clients import SwiftRadioEthernet

import SpaceVR_Configuration_Connection_Telemetry
import TransferFile

FLIGHT_MODEL = "fm"             # Flight Model configuration constant
DEV_MODEL = "dev"               # Flight Model configuration constant
DEBUG_STATEMENTS_ON = True      # Toogle debug statements on and off for this python file

# Create a command line parser
parser = argparse.ArgumentParser(prog = "SpaceVR SWIFT Main Driver Program", description = __doc__, add_help=True)
parser.add_argument("-i", "--radioIP_Address", type=str, default="192.168.1.42", help="IPv4 address of the SWIFT radio.")
parser.add_argument("-c", "--computerIP_Address", type=str, default="192.168.1.50", help="IPv4 address of the computer connected to SWIFT radio. Defaults to mCOM10K1 Payload Computer")
parser.add_argument("-r", "--sRx_Socket", type=int, default=30000, help="UDP port / socket number for S-Band Receiver.")
parser.add_argument("-s", "--sTx_Socket", type=int, default=30100, help="UDP port / socket number for S-Band Transmitter.")
parser.add_argument("-x", "--xTx_Socket", type=int, default=30200, help="UDP port / socket number for X-Band Transmitter.")
parser.add_argument("-u", "--unit", type=str, default= DEV_MODEL, choices=[DEV_MODEL, FLIGHT_MODEL], help="Chooses which unit type being operated.")
parser.add_argument("-t", "--trace", type=int, default=0, help="Radio trace level.")
parser.add_argument("-f", "--filename", type=str, default="sampleData.txt", help="File to be transmitted.") #cam0.0.jpeg
parser.add_argument("-l", "--loop", type=int, default=0, help="Set to 1 to loop file.") 
args = parser.parse_args()

if __name__ == "__main__":
    
    radio = SwiftRadioEthernet(host=args.radioIP_Address)

    SpaceVR_Configuration_Connection_Telemetry.InitializeRadio(radio, args.unit, args.radioIP_Address, args.computerIP_Address, args.sRx_Socket, args.sTx_Socket, args.xTx_Socket)

    if(args.computerIP_Address == "192.168.1.70"):   #Radio is connected to the flight computer
      print "\nTrying to connect to the BBB Flight Computer" 
      TransferFile.ToSWIFT(args.radioIP_Address, args.sTx_Socket, args.filename, args.loop)
    elif(args.computerIP_Address == "192.168.1.50"): #Radio is connected to the payload computer
      print "\nTrying to connect to the mCOM10K1 Payload Computer" 
      TransferFile.ToSWIFT(args.radioIP_Address, args.sTx_Socket, args.filename, args.loop)
      #TransferFile.DownlinkToGroundStation(radio, SpaceVR_Configuration_Connection_Telemetry.STX_LINK_DEV, args.filename)
    else:
      print "\nThe SWIFT radio is not connected to the BBB FLight Computer or mCOM10K1 payload computer"
   
    #SpaceVR_Configuration_Connection_Telemetry.PrintTelemetry(radio, args.unit)
    #TransferFile.UplinkFromGroundStation(SRX_LINK_DEV, args.filename)

    #Downlink_File.ViaS_Band(filename, numOfFiles) ENGINEERING MODEL / CODE     
    #Downlink_File.ViaX_Band(filename, numOfFiles) FLIGHT CODE 
    #Uplink_File.ViaS_Band(filename, numOfFiles)   FLIGHT CODE



## Questions
#  How do I know if radio.execute_command("linkclose {}".format(link)) command failed. I added an extra letter and program throw no error
