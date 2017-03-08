__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 1/9/15"

class SwiftRadioError(RuntimeError):
	def __init__(self, error_msg):
		self.arg = error_msg
		super(SwiftRadioError, self).__init__(self.arg)