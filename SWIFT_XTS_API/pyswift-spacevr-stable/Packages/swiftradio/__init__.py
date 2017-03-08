"""
The SwiftRadio package is a python package containing python drivers and utilities for interacting \
with SWIFT-SDR units from Tethers Unlimited, Inc (c).

The aim of this package is to provide a simple and intuitive Python interface for commanding and \
controlling  SWIFT-SDRs, while also retaining the advanced capabilities of the underlying RPC protocol.

A simple SwiftRadio application may look like this:

.. code-block:: python
	:linenos:

	from swiftradio.clients import SwiftRadioEthernet

	radio = SwiftRadioEthernet("123.45.67.89")

	if radio.connect():
		sysinfo = radio.execute_command("sysinfo")
		print "You have successfully connected to radio 0x{}.".format( sysinfo["id"] )
		radio.disconnect()

In order to make the most out of SwiftRadio, please refer to the `SWIFT User's Guide \
<https://support.tethers.com/display/SWIFTUG/>`_ for more information on available radio commands. \
To begin, it may be helpful to start with the :ref:`Tutorials <tutorials>` section. Additionally, \
the :ref:`API <api>` section gives a detailed breakdown of all functions and client classes \
available to package users.

Please report any SwiftRadio bugs or issues to Steve Alvarado at alvarado@tethers.com.
"""
# package information
PROJECT = u'SwiftRadio'
COPYRIGHT = u'2016, Tethers Unlimited, Inc'
AUTHOR = u'Steve Alvarado'
VERSION = '2.0.1'
RELEASE = '2.0.1.beta'

# import new v2 radio clients
import clients

# allows users to utilize the swiftradio libraries internal data conversion functions
import tools

# legacy swift radio clients and utils for backwards compatibility
from clients import SwiftRadioInterface, SwiftRadioClient, SwiftRadioInstance
from tools import dataconversions
from tools.error import SwiftRadioError
