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

try:
	import pyswift_distro
except ImportError:
	traceback.print_exc()
	print "failed to import the pyswift_distro package."
	sys.exit(1)

#---------------------------------------------------------------------------------------------------
# 	Main Program
#---------------------------------------------------------------------------------------------------
if __name__ == "__main__":

	# import radio database registration modules specified in pyswift_distro
	radio_reg_modules = pyswift_distro.RADIO_REG_MODULES

	# execute network search and display discovered radio information using registered database info
	swiftradio.tools.swift_network_search( swiftradio.SwiftRadioInterface(register_file_cmds=False), pyswift_distro.RADIO_REG_MODULES )

	print("\npyswift distribution: '{}'".format(pyswift_distro.DISTRO))
