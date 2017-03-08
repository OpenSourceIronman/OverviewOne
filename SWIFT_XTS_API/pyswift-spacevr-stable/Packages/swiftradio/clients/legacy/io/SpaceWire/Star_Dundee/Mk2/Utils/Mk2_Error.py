__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/7/14"

class Mk2Error(RuntimeError):
	# pass
	def __init__(self, error_msg):
		message = "StarDundeeError: {}".format(error_msg)
		super(Mk2Error, self).__init__(message)