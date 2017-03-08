#!/usr/bin/env python

##
# @file Scripts/common/upload_firmware.py
# @brief 
# @author Tyrel Newton <newton@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2016, Tethers Unlimited, Inc.

__author__ = "Tyrel Newton"
__maintainer__ = "Tyrel Newton"
__email__ = "newton@tethers.com"
__company__ = "Tethers Unlimited, Inc."
__status__ = "Functional, TFTP Not Supported Yet"
__date__ = "Late Updated: 6/13/16"

# system level imports that should always be available
import sys
import os
import traceback
import glob
import argparse
try:
	import serial
	no_serial = False
except ImportError:
	no_serial = True

# try very hard to import pyswift's locally installed packages
if os.path.exists(os.path.join('..', '..', '..', '..', '..', '..', '..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../../../../../../../pyswift/Packages')
elif os.path.exists(os.path.join('..', '..', '..', '..', '..', '..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../../../../../../pyswift/Packages')
elif os.path.exists(os.path.join('..', '..', '..', '..', '..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../../../../../pyswift/Packages')
elif os.path.exists(os.path.join('..', '..', '..', '..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../../../../pyswift/Packages')
elif os.path.exists(os.path.join('..', '..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../../pyswift/Packages')
elif os.path.exists(os.path.join('..', 'pyswift', 'Packages')):
	sys.path.insert(1, '../pyswift/Packages')
elif os.path.exists(os.path.join('..', '..', 'Packages')):
	sys.path.insert(1, '../../Packages')

# try very hard to import pyswift's locally installed third party packages
if os.path.exists(os.path.join('..', '..', 'pyswift', 'Thirdparty')):
	sys.path.append('../../pyswift/Thirdparty')
elif os.path.exists(os.path.join('..', '..', 'Thirdparty')):
	sys.path.append('../../Thirdparty')

# with the search patch configured, try to import everything necessary from the swiftradio package,
# if the import failes, fall back to using TFTP
try:
	import swiftradio
	from swiftradio import SwiftRadioError
	from swiftradio.clients import SwiftRadioEthernet
	from swiftradio.clients import SwiftRadioRS422
	from swiftradio.command_interfaces import SwiftFirmwareInterface
	from swiftradio.command_interfaces import SwiftFirmwareError
	use_tftp = False
except ImportError:
	sys.stdout.write("pyswift installation could not be found. Falling back to TFTP upload implementation.\n")
	
	try:
		import tftpy
		use_tftp = True
	except ImportError:
		sys.stdout.write("Failed to import TFTPy. Download and install TFTPy from http://tftpy.sourceforge.net/\n")
		sys.exit(1)

parser = argparse.ArgumentParser(prog = os.path.basename(__file__), description=__doc__, add_help=True)
parser.add_argument('-u', '--unlock', dest='unlock', action='store_true', default=False, help='True to enable unlocking of existing firmware images. Required by erase (-e).')
parser.add_argument('-e', '--erase', dest='erase', action='store_true', default=False, help='True to remove all existing firmware images before uploading new ones. Requires unlock (-u).')
parser.add_argument('--release', dest='release', type=str, default='', help='Locatin of release descriptor (release.json) file.')
parser.add_argument('--connection', dest='connection', type=str, default='', help='Method of connecting to SWIFT unit. Examples: 192.168.1.1, COM3, /dev/ttyS1.')
parser.add_argument('-t', '--trace-level', dest='trace_level', type=int, default=0, help='Trace level for SWIFT command interface.')
args = parser.parse_args()

while not os.path.exists(args.release):
	# try very hard to automatically locate the release descriptor (release.json) by searching
	# a variety of expected locations, the locations are searched in the following order
	# 		./release.json				'unzip here' to pyswift/Scripts/common
	# 		../../release.json			'unzip here' to pyswift
	# 		../../../release.json		'unzip here' alongside pyswift
	# 		./*/release.json			'unzip to' a sub-directory inside pyswift/Scripts/common
	# 		../../*/release.json		'unzip to' a sub-directory inside pyswift
	# 		../../../*/release.json		'unzip to' a sub-directory alongside pyswift
	
	# current directory
	if os.path.exists(os.path.join('.', 'release.json')):
		args.release = os.path.join('.', 'release.json')
		continue
	
	# two-back directory
	if os.path.exists(os.path.join('..', '..', 'release.json')):
		args.release = os.path.join('..', '..', 'release.json')
		continue
	
	# three-back directory
	if os.path.exists(os.path.join('..', '..', '..', 'release.json')):
		args.release = os.path.join('..', '..', '..', 'release.json')
		continue
	
	# one-up sub-directory search
	for dir in os.listdir(os.path.join('.')):
		release_dir = os.path.join('.', dir)
		if not dir == '.svn' and os.path.isdir(release_dir):
			if os.path.exists(os.path.join(release_dir, 'release.json')):
				args.release = os.path.join(os.path.join(release_dir, 'release.json'))
				break
	
	if os.path.exists(args.release):
		continue
	
	# two-back sub-directory search
	for dir in os.listdir(os.path.join('..', '..')):
		release_dir = os.path.join('..', '..', dir)
		if os.path.isdir(release_dir):
			if os.path.exists(os.path.join(release_dir, 'release.json')):
				args.release = os.path.join(os.path.join(release_dir, 'release.json'))
				break
	
	if os.path.exists(args.release):
		continue
	
	# three-back sub-directory search
	for dir in os.listdir(os.path.join('..', '..', '..')):
		release_dir = os.path.join('..', '..', '..', dir)
		if os.path.isdir(release_dir):
			if os.path.exists(os.path.join(release_dir, 'release.json')):
				args.release = os.path.join(os.path.join(release_dir, 'release.json'))
				break
	
	if os.path.exists(args.release):
		continue
	
	# ask the user or exit on keyboard interrupt
	try:
		args.release = raw_input('Where is the release descriptor (release.json) located? ')
		if os.path.exists(os.path.join(args.release, 'release.json')):
			args.release = os.path.join(args.release, 'release.json')
	except KeyboardInterrupt:
		sys.stdout.write('\nGoodbye!\n')
		sys.exit(0)

sys.stdout.write('Using release descriptor: {}\n'.format(args.release))
sys.stdout.write('......ATTENTION: If this is not the correct release descriptor, Ctrl-C exit now.\n')
sys.stdout.write('\n')

if use_tftp:
	sys.stdout.write('TFTP uploads are not supported by this script yet. Goodbye!\n')
	sys.exit(1)

while True:
	if len(args.connection) == 0:
		try:
			args.connection = raw_input('How do you want to connect to the SWIFT unit (i.e.: 192.168.1.1, COM3, /dev/ttyS1)? ')
			sys.stdout.write('\n')
		except KeyboardInterrupt:
			sys.stdout.write('\nGoodbye!\n')
			sys.exit(0)
	if '.' in args.connection:
		radio = SwiftRadioEthernet(args.connection, trace=args.trace_level)
	else:
		if not no_serial:
			if args.connection.startswith('COM'):
				args.connection = args.connection[3:]
			try:
				radio = SwiftRadioRS422(args.connection, trace=args.trace_level)
			except serial.serialutil.SerialException:
				args.connection = ''
				continue
		else:
			sys.stdout.write('\"{}\" appears to be a serial port and pyserial is not installed. Try again.\n'.format(args.connection))
			args.connection = ''
			continue
	
	if not radio.connect():
		sys.stdout.write('Failed to connect to SWIFT unit with {}. Try again.\n'.format(args.connection))
		args.connection = ''
		continue
	
	try:
		print 'connected to SWIFT unit via {}...'.format(args.connection)
		sysinfo = radio.execute_command('sysinfo')
		print '...unit ID {}'.format(sysinfo['id'])
		print '...hardware ID 0x{:08X}'.format(sysinfo['hardware_id'])
		sysstat = radio.execute_command('sysstat')
		print '...system uptime {} seconds'.format(sysstat['uptime'])
		print '...system temperature {:.2f}C'.format(sysstat['temp'])
		break
	except SwiftRadioError as e:
		print '{}'.format(e)
		radio.disconnect()
		sys.exit(1)

try:
	radio.attach_command_interface("firmware", SwiftFirmwareInterface)
	if args.unlock:
		radio.firmware.enable_unlocking()
	radio.firmware.cache_commands()
	radio.firmware.revert_uncommitted_changes()
	if args.erase:
		radio.firmware.remove_all_images()
	radio.firmware.import_release(args.release)
except:
	traceback.print_exc()
	radio.disconnect()
	sys.exit(1)

try:
	hw_image = radio.firmware.get_multiboot_hardware_image()
	if hw_image is None:
		hw_image = radio.firmware.get_hardware_image()
	
	sw_image = radio.firmware.get_software_image()
	
	if hw_image is not None:
		if not hw_image.upload():
			if sw_image is not None:
				radio.firmware.revert_uncommitted_changes()
				radio.disconnect()
				sys.exit(1)
		
		hw_image.lock()
		
	if not sw_image is None:
		if sw_image.upload():
			sw_image.lock()
except SwiftRadioError as e:
	sys.stdout.write("{}\n".format(e))
	radio.firmware.revert_uncommitted_changes()
	radio.disconnect()
	sys.exit(1)

radio.disconnect()
