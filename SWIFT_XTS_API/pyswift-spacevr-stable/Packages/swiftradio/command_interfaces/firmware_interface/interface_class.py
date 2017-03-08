##
# @file
# @brief
# @author Tyrel Newton <newton@tethers.com>, Tethers Unlimited, Inc.
# @attention Copyright (c) 2016, Tethers Unlimited, Inc.

__author__ = "Tyrel Newton"
__maintainer__ = "Tyrel Newton"
__email__ = "newton@tethers.com"
__company__ = "Tethers Unlimited, Inc."
__status__ = "Functional, But Still In-Development"
__date__ = "Updated: 06/02/16 (SRA)"

import os
import time
import hashlib
import json
from .. swiftcmdbase import SwiftCommandInterface

class SwiftFirmwareInterface(SwiftCommandInterface):
	NUM_INODES = 15 	# .. warning:: class variable. necessary?

	def __init__(self, radio):
		SwiftCommandInterface.__init__(self, radio)
		self._images = []
		self._unlock = False
		self._retry_count = 5

		self._radio.default_execmd_settings(fail_rpc_error=False, return_rpc_error=True, fail_retries=10)

	def _cleanup_interface(self):
		pass

	def enable_unlocking(self):
		self._unlock = True

	def cache_commands(self):
		self._radio._cache_command('lsfirm')
		self._radio._cache_command('mkfirm')
		self._radio._cache_command('ckfirm')
		self._radio._cache_command('upfirm')
		self._radio._cache_command('idfirm')
		self._radio._cache_command('rvfirm')
		self._radio._cache_command('rmfirm')
		self._radio._cache_command('lkfirm')
		self._radio._cache_command('ukfirm')

	def import_release(self, release_fname=None):
		self._radio._trace_output('importing firmware images described in: {}'.format(release_fname), msg_tracelevel=0)

		f = open(release_fname, 'r')
		release = json.load(f)
		f.close()

		for fname, image_metadata in release['images'].items():
			image_fname = os.path.join(os.path.dirname(release_fname), fname)
			image = SwiftFirmwareImage(self, image_fname, image_metadata)
			self._radio._trace_output('imported image: {} --> {} ({})'.format(image.get_local_name(), image.get_remote_name(), image.get_tag()), msg_tracelevel=0)
			self._images.append(image)

	def revert_uncommitted_changes(self):
		self._radio.execute_command('rvfirm')

	def remove_all_images(self):
		self._radio._trace_output('removing all firmware images...', msg_tracelevel=0)
		for i in range(self.NUM_INODES):
			lsfirm, error = self._radio.execute_command('lsfirm -i {}'.format(i))
			if error == 0:
				image = SwiftFirmwareImage(self, None, lsfirm)
				image.remove()

	def get_multiboot_hardware_image(self, committed=None):
		for image in self._images:
			if image.is_multiboot_hardware_image():
				if committed is None:
					return image
				
				if image.is_committed() == committed:
					return image
		
		return None
	
	def has_multiboot_hardware_image(self, committed=None):
		return this.get_multiboot_hardware_image(committed) is not None
	
	def get_hardware_image(self):
		for image in self._images:
			if image.is_hardware_image():
				return image

		return None

	def get_software_image(self):
		for image in self._images:
			if image.is_software_image():
				return image

		return None
	
class SwiftFirmwareImage(object):
	CHECKSUM_TYPE_NONE	= ''
	CHECKSUM_TYPE_MD5	= 'md5'

	def __init__(self, iface, fname=None, meta=None):
		self._iface = iface
		self._radio = self._iface._radio
		self._retry_count = self._iface._retry_count

		self._index = -1
		self._remote_name = ''
		self._local_name = ''
		self._remote_checksum_type = self.CHECKSUM_TYPE_NONE
		self._remote_checksum = ''
		self._local_checksum_type = self.CHECKSUM_TYPE_NONE
		self._local_checksum = ''
		self._tag = ''
		self._type = ''
		self._multiboot = False
		self._locked = False
		self._real_size = -1
		self._stash_size = -1
		self._commit_size = -1
		self._revision = -1
		self._timestamp = -1

		if meta is not None:
			if 'index' in meta:
				self._index = int(meta['index'])

			if 'remote_name' in meta:
				self._remote_name = str(meta['remote_name'])
			elif 'name' in meta:
				self._remote_name = str(meta['name'])

			if 'size' in meta:
				self._real_size = int(meta['size'])
			elif 'real_size' in meta:
				self._real_size = int(meta['real_size'])
			
			if 'stash_size' in meta:
				self._stash_size = int(meta['stash_size'])
			
			if 'commit_size' in meta:
				self._commit_size = int(meta['commit_size'])
			
			if 'tag' in meta:
				self._tag = str(meta['tag'])

			if 'type' in meta:
				self._type = str(meta['type'])
			elif 'target' in meta and 'format' in meta:
				self._type = str(meta['target'])+'|'+str(meta['format'])
			elif 'target' in meta:
				self._type = str(meta['target'])

			if 'multiboot' in meta:
				self._multiboot = bool(meta['multiboot'])

			if 'revision' in meta:
				self._revision = int(meta['revision'])

			if 'timestamp' in meta:
				self._timestamp = int(meta['timestamp'])

			if 'checksum_type' in meta:
				self._local_checksum_type = str(meta['checksum_type'])

			if 'checksum' in meta:
				self._local_checksum = bytearray.fromhex(meta['checksum'])
			
			if 'immutable' in meta:
				if bool(meta['immutable']):
					self._locked = True

			if 'immovable' in meta:
				if bool(meta['immovable']):
					self._locked = True
			
		if fname is not None:
			if not os.path.exists(fname):
				raise SwiftFirmwareError('Specified firmware image filename does not exist: {}'.format(fname))

			self._local_name = fname

			md5_checksum = hashlib.md5()
			with open(self._local_name, mode = 'rb') as local_f:
				while True:
					buf = local_f.read(4096)
					if not buf:
						break
					md5_checksum.update(buf)

			if self._local_checksum_type == 'md5':
				if not md5_checksum.digest() == self._local_checksum:
					raise SwiftFirmwareError('Invalid MD5 checksum for local firmware image: {}'.format(self._local_name))
			else:
				self._local_checksum_type = self.CHECKSUM_TYPE_MD5
				self._local_checksum = md5_checksum.digest()

		if self._index < 0 and len(self._remote_name) > 0:
			lsfirm, error = self._radio.execute_command('lsfirm -s {}'.format(self._remote_name))
			if error == 0:
				if self._local_checksum == lsfirm['master_checksum']:
					self._index = lsfirm['index']
					self._remote_checksum = lsfirm['master_checksum']
					if lsfirm['immutable'] or lsfirm['immovable']:
						self._locked = True
		
	def is_software_image(self):
		if self._type.startswith('mb'):
			return True
		elif self._type.startswith('microblaze'):
			return True
		elif self._type.endswith('elf'):
			return True
		elif self._type.endswith('elf32'):
			return True
		elif self._type.endswith('elf64'):
			return True
		elif self._type.endswith('srec'):
			return True
		return False

	def is_hardware_image(self):
		return not self.is_software_image()

	def is_multiboot_hardware_image(self):
		return self.is_hardware_image() and self._multiboot
	
	def get_local_name(self):
		return self._local_name

	def get_remote_name(self):
		return self._remote_name

	def get_tag(self):
		return self._tag

	def get_real_size(self):
		return self._real_size

	def get_revision(self):
		return self._revision

	def get_timestamp(self):
		return self._timestamp
	
	def is_committed(self):
		return self._commit_size == self._real_size
	
	def is_stashed(self):
		return self._stash_size == self._real_size
	
	def lock(self, stash=False):
		"""
		Locks the image in the boot table, which makes it more difficult to remove or overwrite.

		:param bool stash: Do not commit the change to the boot table to ROM.

		Last Updated: 5/27/16 (TDN)
		"""
		if self._index < 0:
			return

		if self._locked:
			return

		if stash:
			self._radio.execute_command('lkfirm {} -h'.format(self._index))
		else:
			self._radio.execute_command('lkfirm {}'.format(self._index))
		self._radio._trace_output('...locked image in boot table index {}'.format(self._index), msg_tracelevel=0)
		self._locked = True

	def unlock(self, stash=False):
		"""
		Unlocks the image in the boot table so that it can be either removed or overwritten.

		:param bool stash: Do not commit the change to the boot table to ROM.

		Last Updated: 5/27/16 (TDN)
		"""
		if self._index < 0:
			return

		if not self._locked:
			return

		if not self._iface._unlock:
			raise SwiftFirmwareError('Image unlocking was not enable within the firmware command interface.')

		if stash:
			self._radio.execute_command('ukfirm {} -h'.format(self._index))
		else:
			self._radio.execute_command('ukfirm {}'.format(self._index))
		self._radio._trace_output('...unlocked image in boot table index {}'.format(self._index), msg_tracelevel=0)
		self._locked = False

	def remove(self, stash=False):
		"""
		Removes the image from the boot table. The image must be unlocked, or unlocking must be
		enabled within the parent command interface

		:param bool stash:

		Last Updated: 5/27/16 (TDN)
		"""
		if self._index < 0:
			return

		self.unlock()
		if stash:
			self._radio.execute_command('rmfirm {} -h'.format(self._index))
		else:
			self._radio.execute_command('rmfirm {}'.format(self._index))
		self._radio._trace_output('...removed image from boot table index {}'.format(self._index), msg_tracelevel=0)
		self._index = -1

	def allocate(self, commit=False):
		if self._index >= 0:
			return True

		# image is not currently in table
		if self._multiboot:
			# multiboot image must go at address zero
			lsfirm, error = self._radio.execute_command('lsfirm -a 0')
			if error is not None and error == 0:
				# an image already exists at address zero
				if lsfirm['immutable']:
					# image is locked
					if self._iface._unlock:
						self._index = lsfirm['index']
						self._address = lsfirm['address']
						self._alloc_size = lsfirm['alloc_size']
						self._radio.execute_command('ukfirm {} -h'.format(self._index))
						self._radio._trace_output('...unlocking and using existing boot table index {}'.format(self._index), msg_tracelevel=0)
					else:
						self._radio._trace_output('...unlocking existing image in boot table index {} is not allowed'.format(lsfirm['index']), msg_tracelevel=0)
						return False
				else:
					# image is unlocked, blow it away
					self._index = lsfirm['index']
					self._address = lsfirm['address']
					self._alloc_size = lsfirm['alloc_size']
					self._radio._trace_output('...using existing boot table index {}'.format(self._index), msg_tracelevel=0)
		else:
			# non multiboot image, search by remote name
			lsfirm, error = self._radio.execute_command('lsfirm -s {}'.format(self._remote_name))
			if error is not None and error == 0:
				# the named image already exists
				if lsfirm['immutable']:
					# image is locked
					if self._iface._unlock:
						self._index = lsfirm['index']
						self._address = lsfirm['address']
						self._alloc_size = lsfirm['alloc_size']
						self._radio.execute_command('ukfirm {} -h'.format(self._index))
						self._radio._trace_output('...unlocking and using existing boot table index {}'.format(self._index), msg_tracelevel=0)
					else:
						self._radio._trace_output('...unlocking existing image in boot table index {} is not allowed'.format(lsfirm['index']), msg_tracelevel=0)
						return False
				else:
					# image is unlocked, blow it away
					self._index = lsfirm['index']
					self._address = lsfirm['address']
					self._alloc_size = lsfirm['alloc_size']
					# self._real_size = lsfirm['real_size']
					# self._stash_size = lsfirm['statsh_size']
					# self._commit_size = lsfirm['commit_size']
					self._radio._trace_output('...using existing boot table index {}'.format(self._index), msg_tracelevel=0)

		if self._index < 0:
			mkfirm, error = self._radio.execute_command('mkfirm -h -s {} {}'.format(self._real_size, self._type))
			if error is None or not error == 0:
				return False
			self._index = mkfirm['index']
			self._address = mkfirm['address']
			self._alloc_size = mkfirm['alloc_size']
			self._radio._trace_output('...using new boot table index {}'.format(self._index), msg_tracelevel=0)

		self._radio._trace_output('...using allocated ROM segment 0x{:08X}:{:08X}'.format(self._address, self._address + self._alloc_size - 1, msg_tracelevel=0))

		return True

	def upload(self, commit=True):
		self._radio._trace_output('uploading {} --> {}...'.format(self._local_name, self._remote_name), msg_tracelevel=0)

		if self._index < 0:
			if not self.allocate(commit=False):
				return False

		# if the remote and local checksums match, then the image has already been uploaded
		if self._local_checksum == self._remote_checksum:
			self._radio._trace_output('...found matching image in boot table index {}'.format(self._index), msg_tracelevel=0)
			return True
		
		##
		# upload all available meta data for the newly created image
		#
		if self._revision > 0:
			self._radio.execute_command('idfirm {} -h -r {}'.format(self._index, self._revision))
		if self._timestamp > 0:
			self._radio.execute_command('idfirm {} -h -t {}'.format(self._index, self._timestamp))
		if len(self._remote_name) > 0:
			self._radio.execute_command('idfirm {} -h -s {}'.format(self._index, self._remote_name))
		if len(self._tag) > 0:
			self._radio.execute_command('idfirm {} -h -g {}'.format(self._index, self._tag))
		
		##
		# upload the master checksum for the image
		#
		self._radio.execute_command('ckfirm -h -i {} -t {} -d {}'.format(self._index, self._local_checksum_type, self._local_checksum))
		
		##
		# upload and stash the image in RAM
		# - the -h parameter to upfirm denotes stashing
		# - the trace level is zero'd to prevent the command line tracer from dumping raw binary to stdout
		#
		self._radio._trace_output('...uploading and stashing image in RAM', msg_tracelevel=0)
		trace_level = self._radio.set_tracelevel(0)		# force skip tracing command client messages during upload
		offset = 0
		with open(self._local_name, mode = 'rb') as f:
			while True:
				buf = f.read(512)
				if not buf:
					self._radio._trace_output('......100.000%', msg_tracelevel=0, prepend_cr=1)
					break
				
				tries = self._retry_count
				while tries > 0:
					upfirm, error = self._radio.execute_command('upfirm {} -h -o {} -d {}'.format(self._index, offset, buf))
					if error is not None and error == 0 and 'stash_size' in upfirm and 'real_size' in upfirm:
						break
					if tries == self._retry_count:
						self._radio._trace_output('', msg_tracelevel=0, radioname=0)
					self._radio._trace_output('............drop!', msg_tracelevel=0)
					tries -= 1
				
				if tries == 0:
					self._radio._trace_output('', msg_tracelevel=0, radioname=0)
					self._radio._trace_output('...failed to upload and stash image in RAM, removing partial image and aborting', msg_tracelevel=0)
					self.remove(stash=True)
					return False
				
				offset = offset + len(buf) # upfirm['stash_size']
				
				self._radio._trace_output('......{:7.3f}%'.format(100.0 * float(upfirm['stash_size']) / float(upfirm['real_size'])), msg_tracelevel=0, prepend_cr=1, newline=0)
		
		self._radio.set_tracelevel(trace_level)			# restore trace level now that upload is complete
		
		##
		# verify the stashed image in RAM against the previously uploaded checksum
		# - if the checksums do not match, remove the image and error out
		#
		tries = self._retry_count
		while tries > 0:
			ckfirm, error = self._radio.execute_command('ckfirm -i {}'.format(self._index))
			if error is not None and error == 0:
				if 'master_checksum_type' in ckfirm and 'latest_checksum_type' in ckfirm:
					if 'master_checksum' in ckfirm and 'latest_checksum' in ckfirm:
						break
			tries -= 1
		
		if tries == 0:
			self._radio._trace_output('...failed to verify stashed image in RAM, removing it and aborting', msg_tracelevel=0)
			self.remove(stash=True)
			return False
		
		self._radio._trace_output('...master {} checksum: {}'.format(ckfirm['master_checksum_type'], ''.join('{:02x}'.format(ord(c)) for c in ckfirm['master_checksum'])), msg_tracelevel=0)
		self._radio._trace_output('...latest {} checksum: {}'.format(ckfirm['latest_checksum_type'], ''.join('{:02x}'.format(ord(c)) for c in ckfirm['latest_checksum'])), msg_tracelevel=0)
		if not ckfirm['latest_checksum'] == ckfirm['master_checksum']:
			self._radio._trace_output('...stashed image in RAM is corrupt, removing it and aborting', msg_tracelevel=0)
			self.remove(stash=True)
			return False
		
		##
		# commit the stashed image to ROM
		# - the commit is done in the background and the script monitors the status via 'lsfirm'
		# - the commit is complete when the latest checksum type matches the master checksum type,
		#   which indicates the image in ROM has been verified (or invalidated)
		#
		self._radio._trace_output('...committing stashed and verified image to ROM', msg_tracelevel=0)
		
		trace_level = self._radio.set_tracelevel(0)
		
		while True:
			time.sleep(1.0)
			lsfirm, error = self._radio.execute_command('lsfirm -i {}'.format(self._index))
			if error is None or error != 0:
				self._radio._trace_output('', msg_tracelevel=0, radioname=0)
				self._radio._trace_output('.........error={}'.format(error), msg_tracelevel=0)
				self._radio.set_tracelevel(trace_level)
				self.remove()
				return False
			
			if 'commit_size' in lsfirm and 'real_size' in lsfirm:
				if lsfirm['commit_size'] == lsfirm['real_size']:
					if 'latest_checksum_type' in lsfirm and 'master_checksum_type' in lsfirm:
						if lsfirm['latest_checksum_type'] == lsfirm['master_checksum_type']:
							self._radio._trace_output('......100.000%', msg_tracelevel=0, prepend_cr=1)
							self._radio.set_tracelevel(trace_level)
							break
				
				self._radio._trace_output('......{:7.3f}%'.format(100.0 * float(lsfirm['commit_size']) / float(lsfirm['real_size'])), msg_tracelevel=0, prepend_cr=1, newline=0)
		
		##
		# verify the integrity of the committed image in ROM
		#
		tries = self._retry_count
		while tries > 0:
			lsfirm, error = self._radio.execute_command('lsfirm -i {}'.format(self._index))
			if error is not None and error == 0 and 'master_checksum' in lsfirm and 'latest_checksum' in ckfirm:
				break
			tries -= 1
		
		if tries == 0:
			self._radio._trace_output('...failed to verify stashed image in ROM, removing it and aborting', msg_tracelevel=0)
			self.remove(stash=True)
			return False
		
		if not lsfirm['latest_checksum'] == lsfirm['master_checksum']:
			self._radio._trace_output('...committed image in ROM is corrupt, removing it and aborting', msg_tracelevel=0)
			self.remove()
			return False
		
		return True
		
	# def _commit(self):
		# """
		# Commits the stashed image to ROM
		# """

		# image is not in table, so cannot be stashed
		# if self._index < 0:
			# return

		# lsfirm, error = self._radio.execute_command('lsfirm -i {}'.format(self._index))
		# if not error == 0:
			# return

		# if lsfirm['commit_size'] == lsfirm['real_size']:
			# return

		# self._radio._trace_output('...committing stashed and verified image to ROM', msg_tracelevel=0)

		# trace_level = self._radio.set_tracelevel(0)

		# while True:
			# time.sleep(1.0)
			# lsfirm, error = self._radio.execute_command('lsfirm -i {}'.format(self._index))
			# if not error == 0:
				# self._radio._trace_output(' done (error={})'.format(error), msg_tracelevel=0)
				# break

				# self._radio._trace_output('......{:7.3f}%'.format(100.0 * float(lsfirm['commit_size']) / float(lsfirm['real_size'])), msg_tracelevel=0, prepend_cr=1, newline=0)

			# if lsfirm['commit_size'] == lsfirm['real_size']:
				# if lsfirm['latest_checksum_type'] == lsfirm['master_checksum_type']:
					# self._radio._trace_output(' done'.format(error), msg_tracelevel=0)
					# break

		# self._radio.set_tracelevel(trace_level)

class SwiftFirmwareError(RuntimeError):
	pass
