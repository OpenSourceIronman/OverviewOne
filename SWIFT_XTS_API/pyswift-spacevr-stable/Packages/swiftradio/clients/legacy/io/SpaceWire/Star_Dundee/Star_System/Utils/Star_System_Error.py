__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 11/7/14"

class StarSystemError(RuntimeError):
	def __init__(self, error_msg):
		message = "StarDundeeError: {}".format(error_msg)
		super(StarSystemError, self).__init__(message)