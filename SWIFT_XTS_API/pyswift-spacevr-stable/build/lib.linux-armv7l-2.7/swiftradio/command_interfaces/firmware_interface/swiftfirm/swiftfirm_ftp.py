#!/usr/bin/env python

##
# @file swiftfirm_ftp.py
# @brief contains wrapper class for uploading/downloading firmware images to/from the radio
# @author Steve Alvarado <alvarado@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2015, Tethers Unlimited, Inc.

import sys
import os
import traceback
import time
import logging
import glob
import binascii
import hashlib

__author__ = "Steve Alvarado"
__maintainer__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__company__ = "Tethers Unlimited Inc."
__version__ = "0.1.0"
__date__ = "Created: 8/6/15"
__doc__ = ("this module contains a Swift Firmware File Transfer Protocol wrapper class for "
		  "uploading/downloading firmware images to/from the radio using the RPC command interface.")

class SwiftfirmFTP(object):
	"""
	Author: S. Alvarado
	Created: 8/6/15
	Description: Swift Firmware File Transfer Protocol wrapper for uploading/downloading firmware images to/from the radio using the
				 RPC command interface.
	Status: Under Construction
	TODO: Complete set_boot_priority_list method for uploaded images.
	"""
	def __init__(self, endianess="big"):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: General class constructor for instantiating firmware file transfer wrapper.
		Parameters: logger - logger for printout statements
					endianess - (currently unused) Endianess of the binary data that will be extracted from various files.
		"""
		# error check the archive directory given
		if ( endianess != "big" ) and ( endianess != "network" ) and ( endianess != "little" ):
			raise SwiftfirmFTPError("invalid Endianess type '{}'. Must be 'big', 'little', or 'network'.".format( endianess ) )

		self._logger = logging.getLogger( "{}.{}".format(__name__, self.__class__.__name__) )
		self._endianess = endianess

	# ===========================================================================================================================
	# 	Public Methods
	# ===========================================================================================================================
	def software_image_upload(self, archive_dir, radioclient, chunksize = 4096, default_image=False, lock=False):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: parse the software image archive directory contents and upload the application.elf file to the radio.
		Note: the application.elf file and the release.py file must be in the directory specified by the archivedir parameter.
		Parameters: archive_dir - directory containing the firmware image (.elf) and release.py files
					radioclient - SwiftRadioInterface for sending radio commands
					chunksize - size of each chunk of image data sent to the radio. must be between 1 and 10000
					default_image - make this image the primary boot image after checksum validation.
					lock - lock the image after checksum validation.
		Return: status integer
				1 - upload successful
				or
				0 - upload unsuccessful
		TODO: need a "tag" parameter to allow them to select a tag for the uploaded image?
		"""
		target = "sw"
		# error check the archive directory given
		if os.path.isdir(archive_dir) == False:
			raise SwiftfirmFTPError("The firmware image directory '{}' does not exist.".format( archive_dir ) )

		self._logger.info("starting software image upload...")
		return self._process_and_upload_firmware(archive_dir, target, chunksize, radioclient, default_image, lock)

	def hardware_image_upload( self, archive_dir, radioclient, chunksize = 4096, default_image=False, lock=False ):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: parse the hardware image archive directory contents and upload the boatload.bin file to the radio.
		Note: the boatload.bin file and the release.py file must be in the directory specified by the archivedir parameter.
		Parameters: archivedir - directory containing the firmware image (.bin) and release.py files.
					radioclient - SwiftRadioInterface for sending radio commands
					chunksize - size of each chunk of image data sent to the radio. must be between 1 and 10000
					default_image - make this image the primary boot image after checksum validation.
					lock - lock the image after checksum validation.
		Return: status integer
				1 - upload successful
				or
				0 - upload unsuccessful
		TODO: need a "tag" parameter to allow them to select a tag for the uploaded image?
		"""
		target = "hw"
		# error check the archive directory given
		if os.path.isdir(archive_dir) == False:
			raise SwiftfirmFTPError("The firmware image directory '{}' does not exist.".format( archive_dir ) )

		self._logger.info("starting hardware image upload...")
		return self._process_and_upload_firmware(archive_dir, target, chunksize, radioclient, default_image, lock)

	def get_image_inode(self, target, radioclient, size=0, fmt="default"):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: generate a firmware image inode using the mkfirm command.
		Parameters: target - [hw or sw] specifies either a hardware or software image will be uploaded.
					radioclient - SwiftRadioInterface for sending radio commands
					size - size of the firmware image that will be uploaded
					fmt - image format
		Return: inode value as a integer
		"""
		# error check target parameter
		if ( target != "hw" ) and ( target != "sw" ):
			raise SwiftfirmFTPError("Invalid image target '{}'. Must be 'sw' or 'hw'".format(target) )

		# execute mkfirm command
		self._logger.debug( "\nsize: {} \nformat: {} \ntarget: {}".format(size, fmt, target) )
		self._logger.debug( "executing mkfirm and retrieving image table inode...")
		pkts, error, etype = radioclient.execute("mkfirm -s {size} -f {fmt} {target}".format(size=size, fmt=fmt, target=target), return_error=True )

		# get inode
		inode = pkts.find_command_data_by_name("inode", "uint")
		if inode == None:
			raise SwiftfirmFTPError( "could not retrieve inode from radio. (error: {} type:{})".format( error, etype ) )
		if type( inode ) is not int:
			raise SwiftfirmFTPError("inode should be a {}. not {}".format( int, type( inode ) ) )
		self._logger.info( "success. inode {} received.".format( inode ) )

		# return inode value
		return inode

	def set_image_metadata(self, metadata, inode, radioclient):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: Set meta data via the idfirm command
		Parameters:	metadata - dictionary {"name": , "revision": , "timestamp": , "tag": , }
					inode - inode that was previously returned by radio
					radioclient - client for sending idfirm command
		Return: status integer
				1 - successful
				or
				0 - unsuccessful
		"""
		status = 0

		# error check metadata parameter and make sure the dictionary has all the required
		# entries and they are the correct data type
		metadata_params = { "name":str, "revision":int, "timestamp":int, "tag":str }
		for key, value in metadata_params.items():
			if key not in metadata:
				raise SwiftfirmFTPError( "dictionary key {} is missing." )
			if (type(metadata[key]) is not value) and (metadata[key] is not None ):
				raise SwiftfirmFTPError( "{} is type {}. must be {} or {}.".format(key, type(metadata[key]), value, None) )

		for key, value in metadata.items():
			self._logger.debug( "{}: {}".format( key, value ) )

		# set meta data via the idfirm command
		command_str = "idfirm {}".format(inode)
		if metadata["revision"] != None:
			command_str += " -r {}".format(metadata["revision"])
		if metadata["timestamp"] != None:
			command_str += " -t {}".format(metadata["timestamp"])
		if metadata["name"] != None:
			command_str += " -s {}".format(metadata["name"])
		if metadata["tag"] != None:
			command_str += " -g {}".format(metadata["tag"])

		self._logger.debug( "executing {}...".format( command_str ) )
		pkts, error, etype = radioclient.execute( command_str, return_error=True )

		if error == 0:
			self._logger.info( "success. image meta data uploaded." )
			status = 1
		else:
			self._logger.error( "**fail** failed to update metadata. (error={}, type={} )".format(error, etype) )
			status = 0

		return radioclient

	def upload_image_to_radio(self, image_data, inode, radioclient, chunksize=1024):
		"""
		Author: S. Alvarado
		Last Updated: 8/30/15 (TN)
		Description: upload firmware image data to radio using the upfirm command.
		Parameters: image - file path to .elf or .bin image file
					inode - inode of image, should have already been created
					radioclient - SwiftRadioInterface for sending radio commands
					chunksize - maximum chunk of image data to be sent to radio.
		Return: status integer
				1 - successful upload
				or
				0 - unsuccessful
		"""

		def _calculate_remaining_time(start_time, uploaded, image_size):
			"""
			Author: S. Alvarado
			Last Updated: 8/7/15
			Description: give a rough estimate of how long image upload will take.
			Parameters: start_time - time that upload began, in seconds
						uploaded - amount of image data uploaded, in bytes
						image_size - total image size
			Return: (remaining_time, upload_rate)
					remaining_time - remaining time in seconds
					upload_rate - the upload rate in bytes per second.
			"""
			# calculate the amount of time that has elapsed for current download
			current_time = time.time()
			time_elapsed =  current_time - start_time

			# calculate upload rate in bytes per second
			if time_elapsed < 1:
				return (0, 0)
			calculated_upload_rate = uploaded/time_elapsed

			# calculate remaining time left, in seconds
			estimate_upload_time = (1/calculated_upload_rate)*image_size
			remaining_time_secs = estimate_upload_time - time_elapsed
			return remaining_time_secs, calculated_upload_rate

		def _chunk_image(image, chunksize):
			"""
			Author: S. Alvarado
			Last Updated: 8/7/15
			Description: break down image data into smaller chunks that can be sent to the radio.
			Parameters: image - image file data to be chunked
						chunksize - size of each chunk
			Return: list of chunks of data each of size chunksize
			"""
			image_chunks = list()
			byte_ctr = 0

			# break up data into a list, each item will be of size chunksize
			for i in range( len(image)/chunksize ):
				image_chunks.append( image[i*chunksize:i*chunksize + chunksize] )
				byte_ctr += chunksize

			# add remaining bytes
			if byte_ctr != len( image ):
				image_chunks.append( image[byte_ctr:] )
				self._logger.debug("size of last data chunk: {} bytes".format( len(image_chunks[-1]) ) )

			return image_chunks

		image_chunks = list()
		status = 0
		self._logger.info( "file size: {} kB".format( len( image_data )/1.0e3 ) )

		# break image into smaller chunks
		image_chunks = _chunk_image(image_data, chunksize)
		self._logger.debug( "sending firmware image in {} data chunks of {} bytes.".format( len(image_chunks), chunksize) )

		if len(image_data) > 1e6:
			size_units = "MB"
			size_mod = 1e6
		elif len(image_data) > 1e3:
			size_units = "kB"
			size_mod = 1e3
		else:
			size_units = "B"
			size_mod = 1

		# send each chunk of data to radio until entire image has been sent
		start_time = time.time()
		total_bytes_uploaded = 0
		for chunk in image_chunks:
			chunk_sent_successfully = False

			# send chunk
			pkts, error, etype = radioclient.execute( "upfirm {inode} {data}".format(inode=inode, data=chunk), fail_retry=True, fail_exception=False, return_error=True, timeout=10)

			if error != 0:
				self._logger.error( "image chunk upload failed!. (error={}, type={})".format(error, etype) )
				continue

			# make sure entire chunk was written and received
			bytes_uploaded = pkts.find_command_data_by_name("chunk_size", "uint")

			# if the bytes written return value was dropped, assume all bytes were written (for now)
			if bytes_uploaded == None:
				self._logger.warn( "-verification packet dropped, cannot confirm chunk write-" )
				total_bytes_uploaded += len(chunk)

			# if the number of image data bytes received by radio differs from the number sent, raise error
			elif bytes_uploaded != len(chunk):
				self._logger.debug( "image data: {}".format( " ".join( bytestr ) ) )
				self._logger.error( "**radio only wrote {} bytes of image data to memory, but {} bytes were sent**".format(bytes_uploaded, len(chunk)) )
				bytestr = list()
				for byte in chunk:
					bytestr.append( hex( ord(byte) )[2:].zfill(2) )
				total_bytes_uploaded += bytes_uploaded
				raise SwiftfirmFTPError( "**radio only wrote {} bytes of image data to memory, but {} bytes were sent**".format( bytes_uploaded, len(chunk) ) )

			# otherwise, chunk uploaded correctly
			else:
				total_bytes_uploaded += bytes_uploaded

			# print upload progress
			estimated_time, uprate = _calculate_remaining_time( start_time, total_bytes_uploaded, len(image_data) )
			if (uprate) > (size_mod/20):
				width=".1f"
			else:
				width=".2f"

			if uprate > 1e6:
				rate_units = "MB/sec"
				rate_mod = 1e6
			else:
				rate_units = "kB/sec"
				rate_mod = 1e3

			sys.stdout.write( "uploading - {uploaded:,{width}} of {total_size:,{width}} {sizeunits} at {rate:,.1f} {rateunits} (est. {mins:02d}:{secs:02d})\r".format( uploaded=total_bytes_uploaded/size_mod, total_size = len(image_data)/size_mod, rate=uprate/rate_mod,
																														mins= int(estimated_time/60), secs = int(estimated_time%60), sizeunits=size_units, rateunits=rate_units, width=width) )

		# calculate and display the total download time
		end_time = time.time()
		elapsed_time = end_time - start_time
		self._logger.info( "\nupload complete." )
		self._logger.info( "\nelapsed time: {} mins {} seconds".format( int(elapsed_time/60), int(elapsed_time%60) ) )
		status = 1

		return status

	def validate_image_checksums(self, digest, checksum_type, inode, radioclient):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: verify the uploaded image by sending the image's MD5 checksum using ckfirm
		Parameters: digest - checksum digest as a hexidecimal string.
					checksum_type - type of checksum (i.e. MD5, crc32, fletcher16 ect.)
					inode - inode of image, should have already been created
					radioclient - SwiftRadioInterface for sending radio commands
		Return: status integer
				1 - successful upload
				or
				0 - unsuccessful
		Note: I'm not entirely sure what the 'master' and 'latest' ckfirm return values are...
		TODO: make sure the process of converting of the hex string into a binary is application to all
			  checksum types, not just MD5.
		"""
		valid_checksums = 0
		master_ck = None
		latest_ck = None
		# convert digest hex string into a binary string
		self._logger.debug( "checksum digest: {}".format( digest ) )
		checksum = binascii.unhexlify( digest )
		bytestr = list()
		for byte in checksum:
			bytestr.append( hex( ord(byte) )[2:].zfill(2) )
		self._logger.debug( "checksum binary: {}".format( " ".join( bytestr ) ) )

		pkts, error, etype = radioclient.execute("ckfirm -t {type} -i {inode} -d {digest}".format(type=checksum_type, inode=inode, digest=checksum ),
												max_retries=1,
												fail_exception=False,
												timeout=5,
												return_error=True )
		master_ck = pkts.find_command_data_by_name("master")
		latest_ck = pkts.find_command_data_by_name("latest")
		self._logger.debug( "master: {}".format( master_ck ) )
		self._logger.debug( "latest: {}".format( latest_ck ) )

		if error != 0:
			self._logger.error( "**{} checksum validation failed** \nckfirm command returned negative value {}".format(checksum_type, error ) )
			valid_checksums = 0
		else:
			self._logger.info( "successfully validated image checksums.")
			valid_checksums = 1

		return valid_checksums

	def lock_image(self, inode, radioclient):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: lock a previously uploaded (and valid) image using the lkfirm command.
		Parameters: inode - inode of image, should have already been created.
					radioclient - SwiftRadioInterface for sending radio commands.
		Return: status integer
				1 - successful
				or
				0 - unsuccessful
		"""
		status = 0

		# error check inode
		if inode < 0 or inode > 14:
			raise SwiftfirmFTPError("inode value must be between 0 and 14.".format( inode ) )

		# set boot priority list
		pkts, error, etype = radioclient.execute( "lkfirm {inode}".format(inode=inode), return_error=True )

		if error == 0:
			self._logger.info( "image successfully locked." )
			status = 1
		else:
			self._logger.error( "failed to lock image. (code: {}, type: {}) ".format(error, etype) )
			status = 0

		return status

	def set_image_boot_priority(self, radioclient, index, inode, priority = -1):
		"""
		Author: S. Alvarado
		Last Updated: 8/7/15
		Description: set the boot priority list of the image that has previously been
					uploaded to the radio using the wrbpl command.
		NOTE: Because of over-complex boot priority mechanism, assumptions:
				- hw targets are assumed to be in boottable index 0
				- sw targets are assumed to be in boottable index 1
		Parameters: radioclient - SwiftRadioInterface for sending radio commands.
					index - index of boot priority list to manipulate.
					inode - inode of image, should have already been created.
					priority - boot priority value. must be between -1 and 6. -1 places at end of list.
		Return: status integer
				1 - successful
				or
				0 - unsuccessful
		"""
		status = 0

		# error check index
		if index < 0 or index > 6:
			raise SwiftfirmFTPError( "index value must be between 0 and 6.".format( index ) )

		# error check inode
		if inode < 0 or inode > 14:
			raise SwiftfirmFTPError("inode value must be between 0 and 14.".format( inode ) )

		# error check priority parameter
		if priority < -1 or priority > 7:
			raise SwiftfirmFTPError("boot priority list parameter must be between -1 and 6.".format( priority ) )

		# debug printouts
		self._logger.debug( "index: {}".format( index ) )
		self._logger.debug( "inode: {}".format( inode ) )
		self._logger.debug( "priority: {}".format( priority ) )

		# set boot priority list
		pkts, error, etype = radioclient.execute( "wrbpl -p {prio} {list} {inode}".format(prio=priority, list=index, inode=inode), return_error=True )

		if error == 0:
			self._logger.info( "image priority successfully set." )
			status = 1
		else:
			self._logger.error( "image priority failed. (code: {}, type: {}) ".format(error, etype) )
			status = 0

		return status


	# ===========================================================================================================================
	# 	Private Methods
	# ===========================================================================================================================
	def _process_and_upload_firmware(self, archivedir, target, chunksize, radioclient, defaultimage=False, lockimage=False):
		"""
		Author: S. Alvarado
		Last Updated: 8/28/15
		Description: parse the firmware archive directory contents and upload either a hardware
					 or software image to the radio.
		Parameters: archivedir - file path the directory containing the firmware image contents and meta data.
					target - [hw or sw] specifies either a hardware or software image will be uploaded.
					chunksize - size of each chunk of image data sent to the radio. must be between 1 and 10000
					radioclient - SwiftRadioInterface for sending radio commands
		Return: status integer
				1 - upload successful
				or
				0 - upload unsuccessful
		"""
		upload_result = False

		# error check target parameter
		if ( target != "hw" ) and ( target != "sw" ):
			raise SwiftfirmFTPError( "Invalid image target '{}'. Must be 'sw' or 'hw'".format(target) )
		# error check archivedir parameter
		if os.path.isdir(archivedir) == False:
			raise SwiftfirmFTPError( "The firmware image directory '{}' does not exist.".format( archive_dir ) )
		# error check chunksize parameter
		if chunksize < 1 or chunksize > 10000:
			raise SwiftfirmFTPError( "chunksize parameter must be between 1 and 10000.".format( chunksize ) )
		# error check defaultimage parameter
		if (defaultimage is not False) and (defaultimage is not True):
			raise SwiftfirmFTPError( "default image parameter must be True or False.")
		# error check chunksize parameter
		if (lockimage is not False) and (lockimage is not True):
			raise SwiftfirmFTPError( "lock image parameter must be True or False.")

		# [1] parse image files from firmware archive
		self._logger.info("\nprocessing firmware directory...")
		image = self._parse_upload_image_files(archivedir, target)

		# [2] get image inode
		self._logger.info("\nretrieving image inode...")
		inode = self.get_image_inode(image["target"], radioclient, image["size"])

		# [3] set image metadata
		self._logger.info("\nsetting image metadata...")
		metadata = {"name": image["remote_name"], "revision": image["revision"], "timestamp": image["timestamp"], "tag": image["tag"]}
		self.set_image_metadata( metadata, inode, radioclient )

		# [4] upload firmware image
		self._logger.info("\nuploading firmware image...")
		self.upload_image_to_radio(image["data"], inode, radioclient, chunksize=chunksize)

		# [5] perform checksum validation
		self._logger.info("\nvalidating firmware image...")
		upload_result = self.validate_image_checksums( image["checksum"], image["checksum_type"], inode, radioclient )

		# lock image and configure bpl if image was validated
		if upload_result == 1:

			# [6] lock image
			if lockimage == True:
				self._logger.info("\nlocking firmware image...")
				self.lock_image( inode, radioclient )

			# [7] set boot priority
			self._logger.info("\nsetting image boot table priority...")
			# *** assumption - hardware images are in table index 0 ***
			if target == "hw":
				table_index = 0
			# *** assumption - software images are in table index 1 ***
			else:
				table_index = 1
			# if this is the default boot image, set priority to 0
			if defaultimage == True:
				priority = 0
			# if not, append to end of boot list
			else:
				priority = -1
			# set priority
			self.set_image_boot_priority( radioclient, table_index, inode, priority )

		return upload_result

	def _parse_upload_image_files(self, image_dir, target):
		"""
		Author: S. Alvarado
		Last Updated: 8/17/15
		Description: searches a directory containing either software or hardware
					 image files and gathers critical file and meta data information
					 needed to upload a set the firmware image. This information is
					 consolidated into a dictionary.
		Parameters: target - hw or sw
					image_dir - directory containing the firmware image files (.bin or /.elf)
		Return: a dictionary
				image_info = {
					"profile": , 		# make profile name
					"project": , 		# build project name
					"platform": , 		# build platform
					"hardware": ,   	# hardware platform
					"local_name": , 	# file name of the firmware image (bootload.bin or application.elf)
					"remote_name": , 	# remote server firmware image file name.
					"target": , 		# [hw or sw] specifies either a hardware or software image will be uploaded.
					"format": , 		# firmware image format (i.e. ms, elf32, srec)
					"size": , 			# size of the firmware image file, in bytes.
					"checksum": , 		# image checksum, as a string in hexidecimal characters.
					"checksum_type": , 	# image checksum format (i.e. MD5, CRC32, "Fletcher16", "sum8" ect).
					"revision": , 		# build revision number (i.e. MD5, CRC32, "Fletcher16", "sum8" ect).
					"tag": , 			# arbitrary tag assigned to image.
					"timestamp": ,  	# build timestamp (currently unavailable)
				}
		TODO: 	- where is the build timestamp retrieved? include this in return dictionary.
				- compute an MD5 from the image contents and verify against checksum value in release.py module.
		"""
		def _compute_md5(image):
			"""
			Author: S. Alvarado
			Last Updated: 8/28/15
			Description: compute the MD5 checksum of a image
			Parameters: image - image file data to be chunked
			Return: MD5 digest as a 32-character string of hex characters.
			"""
			# create a hash object and calculate the md5 digest of the image
			hash_obj = hashlib.md5(image)

			# get the md5 as a 32-character hex digest
			digest = hash_obj.hexdigest().lower()

			return digest

		image_info = dict()

		# error check target parameter
		if ( target != "hw" ) and ( target != "sw" ):
			raise SwiftfirmFTPError("Invalid image target '{}'. Must be 'sw' or 'hw'")

		# error check image_dir parameter
		if os.path.isdir(image_dir) == False:
			raise SwiftfirmFTPError("The firmware image directory '{}' does not exist.".format( image_dir ) )

		# import release.py file (should be in archive dir)
		try:
			sys.path.insert(1, image_dir)
			import release
			del sys.path[1]
		except ImportError:
			raise ImportError("could not import release.py module. this module is required to process firmware image information")

		# parse release.py contents
		try:
			# save common project information
			image_info["profile"] = release.PROFILE
			if type( image_info["profile"] ) is not str:
				raise SwiftfirmFTPError("invalid PROFILE value {} in release.py module. must be an str object".format( image_info["profile"] ) )

			image_info["project"] = release.PROJECT
			if type( image_info["project"] ) is not str:
				raise SwiftfirmFTPError("invalid PROJECT value {} in release.py module. must be an str object".format( image_info["project"] ) )

			image_info["platform"] = release.PLATFORM
			if type( image_info["platform"] ) is not str:
				raise SwiftfirmFTPError("invalid PLATFORM value {} in release.py module. must be an str object".format( image_info["platform"] ) )

			image_info["hardware"] = release.HARDWARE
			if type( image_info["hardware"] ) is not str:
				raise SwiftfirmFTPError("invalid HARDWARE value {} in release.py module. must be an str object".format( image_info["hardware"] ) )

			# save image file name (application.elf or bootload.bin)
			if target == "hw":
				image_info["local_name"] = release.HARDWARE_IMAGE_LOCAL_NAME
			else:
				image_info["local_name"] = release.SOFTWARE_IMAGE_LOCAL_NAME
			if type( image_info["local_name"] ) is not str:
				raise SwiftfirmFTPError("invalid LOCAL_NAME value {} in release.py module. LOCAL_NAME must be an str object".format( image_info["local_name"] ) )
			# make sure this file exists
			if os.path.isfile( "{}/{}".format(image_dir, image_info["local_name"] ) ) == False:
				raise SwiftfirmFTPError("cannot upload image. no image file '{}' exists.".format( image_info["local_name"] ) )
			# if it does exist, save file data
			else:
				with open("{}/{}".format(image_dir, image_info["local_name"]) , 'rb') as file_obj:
					image_info["data"] = file_obj.read()

			# save remote image name
			if target == "hw":
				image_info["remote_name"] = release.HARDWARE_IMAGE_REMOTE_NAME
			else:
				image_info["remote_name"] = release.SOFTWARE_IMAGE_REMOTE_NAME
			if type( image_info["remote_name"] ) is not str:
				raise SwiftfirmFTPError("invalid REMOTE_NAME value {} in release.py module. REMOTE_NAME must be an str object".format( image_info["remote_name"] ) )

			# save target type
			if target == "hw":
				image_info["target"] = release.HARDWARE_IMAGE_TARGET
			else:
				image_info["target"] = release.SOFTWARE_IMAGE_TARGET
			if type( image_info["target"] ) is not str:
				raise SwiftfirmFTPError("invalid TARGET value {} in release.py module. must be an str object".format( image_info["target"] ) )
			if (image_info["target"] != "hw") and (image_info["target"] != "sw"):
				raise SwiftfirmFTPError("Invalid image target '{}'. Must be 'sw' or 'hw'".format(image_info["target"]) )

			# save format
			if target == "hw":
				image_info["format"] = release.HARDWARE_IMAGE_FORMAT
			else:
				image_info["format"] = release.SOFTWARE_IMAGE_FORMAT
			if type( image_info["format"] ) is not str:
				raise SwiftfirmFTPError("invalid FORMAT value {} in release.py module. FORMAT must be an str object".format( image_info["format"] ) )
			valid_image_formats = ["default", "ms", "elf32", "srec", "6Sms"]
			if image_info["format"] not in valid_image_formats:
				raise SwiftfirmFTPError( "Invalid image FORMAT type '{}' in release.py module. Must be {}".format(", ".format( image_info["format"] ) ) )

			# save size format
			if target == "hw":
				image_info["size"] = release.HARDWARE_IMAGE_SIZE
			else:
				image_info["size"] = release.SOFTWARE_IMAGE_SIZE
			if type( image_info["size"] ) is not int:
				raise SwiftfirmFTPError("Invalid SIZE value {} in release.py module. SIZE must be an int object".format( image_info["size"] ) )
			if image_info["size"] < 0:
				raise SwiftfirmFTPError("Invalid SIZE value {} in release.py module. must be greater than or equal to 0.".format( image_info["size"] ) )
			if image_info["size"] != len(image_info["data"]):
				raise SwiftfirmFTPError("SIZE value {} in release.py module does not match the size value {} computed from reading the contents of {}.".format( image_info["size"], len(image_info["data"]), "{}/{}".format(image_dir, image_info["local_name"] ) ) )

			# save checksum type
			if target == "hw":
				image_info["checksum_type"] = release.HARDWARE_IMAGE_CHECKSUM_TYPE
			else:
				image_info["checksum_type"] = release.SOFTWARE_IMAGE_CHECKSUM_TYPE
			valid_checksum_types = ["none", "sum8", "fletcher16", "fletcher32", "crc8", "crc8ccitt", "crc16ccitt", "crc32", "md5"]
			if image_info["checksum_type"] not in valid_checksum_types:
				raise SwiftfirmFTPError("Invalid checksum format type '{}' in release.py module. Must be {}".format( image_info["checksum_type"], ", ".join( valid_checksum_types ) ) )

			# save checksum value, (note: this value will be checked against a computed checksum later)
			if target == "hw":
				image_info["checksum"] = release.HARDWARE_IMAGE_CHECKSUM
			else:
				image_info["checksum"] = release.SOFTWARE_IMAGE_CHECKSUM
			if type( image_info["checksum"] ) is not str:
				raise SwiftfirmFTPError("Invalid CHECKSUM value {} in release.py module. CHECKSUM must be an str object".format( image_info["checksum"] ) )
			# make sure the checksum value is the correct width given the checksum type
			checksums_128_bits = ["md5"]
			checksums_32_bits = ["crc32", "fletcher32"]
			checksums_16_bits = ["crc16ccitt", "fletcher16"]
			checksums_8_bits = ["sum8", "crc8", "crc8ccitt"]
			self._logger.debug("checksum length: {}".format(len(image_info["checksum"]) ) )
			if ( image_info["checksum_type"] in checksums_128_bits ) and len( image_info["checksum"] ) != ( 128/8 * 2 ):
				raise SwiftfirmFTPError("Invalid CHECKSUM value {}. CHECKSUM must be {} characters in length for {} checksum types.".format( image_info["checksum"], 128/8 * 2, image_info["checksum_type"] ) )
			elif ( image_info["checksum_type"] in checksums_32_bits ) and len( image_info["checksum"] ) != ( 32/8 * 2 ):
				raise SwiftfirmFTPError("Invalid CHECKSUM value {}. CHECKSUM must be {} characters in length for {} checksum types.".format( image_info["checksum"], 32/8 * 2, image_info["checksum_type"] ) )
			elif ( image_info["checksum_type"] in checksums_16_bits ) and len( image_info["checksum"] ) != ( 16/8 * 2 ):
				raise SwiftfirmFTPError("Invalid CHECKSUM value {}. CHECKSUM must be {} characters in length for {} checksum types.".format( image_info["checksum"], 16/8 * 2, image_info["checksum_type"] ) )
			elif ( image_info["checksum_type"] in checksums_8_bits ) and len( image_info["checksum"] ) != ( 8/8 * 2 ):
				raise SwiftfirmFTPError("Invalid CHECKSUM value {} in release.py module. CHECKSUM must be {} characters in length for {} checksum types.".format( image_info["checksum"], 8/8 * 2, image_info["checksum_type"] ) )
			# make sure the checksum can be converted into a binary string
			try:
				binascii.unhexlify( image_info["checksum"] )
			except TypeError:
				error = (traceback.format_exc()).split("TypeError: ")[1]
				raise SwiftfirmFTPError("\nInvalid CHECKSUM value {} in release.py module. could not convert to hex object for the following reason: {}.".format( image_info["checksum"], error ) )
			# cross-check checksum data
			if image_info["checksum_type"] == "md5":
				# compute the md5
				digest = _compute_md5(image_info["data"])
				self._logger.debug( "computed MD5 digest: {}".format(digest) )
				self._logger.debug( "stored MD5 digest: {}".format(image_info["checksum"]) )
				# verify stored md5 in release.py
				if digest != image_info["checksum"]:
					raise SwiftfirmFTPError( "calculated MD5 checksum {} does not match stored checksum in release.py {}.".format(digest, image_info["checksum"]) )
			else:
				self._logger.warn( "**warning: cannot cross-check stored checksum {}. only support for MD5 checksum validation**".format(image_info["checksum"]) )

			# save revision number
			if target == "hw":
				image_info["revision"] = release.HARDWARE_IMAGE_REVISION
			else:
				image_info["revision"] = release.SOFTWARE_IMAGE_REVISION
			if ( type( image_info["revision"] ) is not int ) and ( type(image_info["revision"]) is not None ):
				raise SwiftfirmFTPError("invalid REVISION number value {} in release.py module. the revision number must be an int or NoneType object".format( image_info["revision"] ) )
			if ( image_info["revision"] < 0) and ( type( image_info["revision"] ) is int ):
				raise SwiftfirmFTPError("invalid REVISION number {} in release.py module. must be greater than 0. (unless REVISION is NoneType)".format( image_info["revision"] ) )

			# save tag
			if target == "hw":
				image_info["tag"] = release.HARDWARE_IMAGE_TAG
			else:
				image_info["tag"] = release.SOFTWARE_IMAGE_TAG
			if type( image_info["tag"] ) is not str:
				raise SwiftfirmFTPError("invalid TAG value {} in release.py module. must be an str object".format( image_info["tag"] ) )

			# save time stamp of build (currently unavailable)
			image_info["timestamp"] = None

		# if one of the following attributes is missing, report error and return NoneType
		except AttributeError:
			self._logger.exception("variable missing from release.py")
			image_info = None
			return image_info

		# print the contents of dictionary for debugging
		for key, value in image_info.items():
			# don't print the file contents because it would take forever due to the large file size.
			if key != "data":
				self._logger.debug( "{}: {}".format(key, value) )

		self._logger.info( "archive directory successfully processed.")

		return image_info

class SwiftfirmFTPError(RuntimeError):
	pass
