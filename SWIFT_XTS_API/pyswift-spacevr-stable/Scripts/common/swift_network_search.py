#!/usr/bin/env python
##
# @file swift_network_search.py
# @brief search network for SWIFT-SDR devices and display information to console.
# @author Steve Alvarado <alvarado@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2015, Tethers Unlimited, Inc.

__author__ = "Steve Alvarado"
__maintainer__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__date__ = "Late Updated: 12/3/15"
__doc__ = ("search network for SWIFT-SDR devices and display information to console.")

#-------------------------------------------------------------------------------------------------------------
# 	Imports
#-------------------------------------------------------------------------------------------------------------
import sys
import traceback
sys.path.insert(1, "../../Packages")
import swiftradio

sys.path.insert(1, "./info")
try:
	import radios_distro
except ImportError:
	print "this script requires a radios_distro.py file."
	sys.exit(1)

#---------------------------------------------------------------------------------------------------
# 	Main Program
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":

	# import radio database registration modules specified by radios_distro.py
	radio_reg_modules = list()
	sys.path.insert(1, "db/radios")
	for file_name in radios_distro.RADIO_REG_MODULES:
		try:
			module = __import__(file_name)
			radio_reg_modules.append(module)
		except:
			print "Warning: radio registration file db/radios/{}.py does not exist.".format( file_name )

	# execute network search and display discovered radio information using registered database info
	swiftradio.tools.swift_network_search( swiftradio.SwiftRadioInterface(register_file_cmds=False), radio_reg_modules )
