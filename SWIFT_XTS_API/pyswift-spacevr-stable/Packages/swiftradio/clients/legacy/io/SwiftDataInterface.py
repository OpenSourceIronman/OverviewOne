__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/07/14"

class SwiftPhysicalInterface:
	"""
	Description: base class for all derived physical interface classes. these classes representing the physical 
				connection to the swiftradio hardware and handle all the sending and receiving of data. all derived 
				classes should include the following methods for them to be used correctly by the SwiftRadioInterface class.
	"""
	def __init__(self):
		"""
		Description:
		"""
		self.name = None
		self.type = None

	# Derived Methods (should be overwritten by subclass)
	def connect(self):
		"""
		Description:
		"""
		pass
		
	def close(self):
		"""
		Description:
		"""
		pass

	def is_open(self):
		"""
		Description:
		"""		
		pass
	
	def read(self):
		"""
		Description:
		"""
		pass

	def write(self):
		"""
		Description:
		"""
		pass

	# Common Methods
	def get_name(self):
		"""
		Description:
		"""
		return self.name			

	def set_name(self, name):
		"""
		Description:
		"""
		if type(name) is str:
			self.name = name
			return 1
		else:
			return -1		

	def __del__(self):
		"""
		Description:
		"""		
		if self.is_open():
			self.close()

if __name__ == "__main__":
	pass
