import serial
import time

__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 6/25/14"

class SwiftSerialInterface:
	def __init__(self, comport=25, baudrate=115200, timeout = 5, serial_object = None):
		self.serial_object = serial.Serial()
		self.connection_good = False
		
		if serial_object != None:
			self.serial_object = serial_object
			connection_good = True
		else:
			self.comport = comport
			self.baudrate = baudrate
			self.timeout = timeout
			com_port_nums = []
			ports_iterable = serial.tools.list_ports.comports()
			list = [i for i in ports_iterable]
			for item in list:
				com_port_nums.append(item[0])
			port_name = 'COM' + str(comport)
			port_list = com_port_nums
			port_found = 0
			for i in range(len(port_list)):
				if port_list[i] == port_name:
					port_found = 1
			if port_found != 1:
				pass
				print '\n**COM Port ' + str(comport) + ' Not Detected.**'	
			else:
				try:
					self.serial_object = serial.Serial(port=(int(comport)-1),baudrate=int(baudrate), timeout = 0)
					self.serial_object.close()
					self.connection_good = True
				except:	
					# traceback.print_exc()
					self.serial_object = None
					# print '** Could Not Connect to ' + port_name + '. Disconnect any programs/peripherals connected to COM port. **'	
					self.connection_good = False
					
	def get_connection_status(self):
		return self.connection_good
		
	def get_connection_info(self):
		info = dict()
		info["connection_type"] = "serial"
		info["port_num"] = self.comport
		info["port_baud"] = self.baudrate
		return info
		
	def write(self, buffer='', length = 0, auto_lf = False):
		if self.serial_object != None:
			if self.serial_object.isOpen():
				if auto_lf == True:
					buffer = str(buffer) + '\r'
				# if write byte length is not specified, write entire buffer
				if length == 0:	
					for c in buffer:
						time.sleep(0.1)
						self.serial_object.write(c)
				else:
					i = 0
					for i in range(length):
						time.sleep(0.1)
						self.serial_object.write(buffer[i])
			else:
				print "Failed Write. COM Port is closed."
			
	def read(self, length = 1):
		buffer = self.serial_object.read(length)
		return buffer
		
	def Flush_Buffers(self):
		self.serial_object.flushInput()
				
	def Poll(self, buffer, num = 1):
		timeout_save = self.serial_object.timeout
		self.serial_object.timeout = 0
		buffer = self.serial_object.read(num)
		self.serial_object.timeout = timeout_save
		return buffer
		
	def is_open(self):
		if self.serial_object.isOpen():
			return True
		else:
			return False
	
	def connect(self,trace = 0):
		comport = self.comport
		baudrate = self.baudrate
		timeout = self.timeout
		com_port_nums = []
		ports_iterable = serial.tools.list_ports.comports()
		list = [i for i in ports_iterable]
		for item in list:
			com_port_nums.append(item[0])
		port_name = 'COM' + str(comport)
		port_list = com_port_nums
		port_found = 0
		for i in range(len(port_list)):
			if port_list[i] == port_name:
				port_found = 1
		if (port_found != 1) and (trace > 0):
			print 'COM Port ' + str(self.comport) + ' Not Detected.'	
			passed = False
		else:
			fail_num = 0
			passed = False
			while passed == False:
				try:
					self.serial_object = serial.Serial(port=(int(comport)-1),baudrate=int(baudrate), timeout = None)
					self.connection_good = True
					passed = True
					if (fail_num > 4) and (trace != 2):
						print "COM Port " + str(comport) + " Connect Attempts: " + str(fail_num)
					if trace == 2:
						print "    Serial Connection Established on COM" + str(comport) + "."
					elif trace == 1:
						print "Serial Connection Established on COM" + str(comport) + "."	
				except serial.SerialException:	
					fail_num += 1
					time.sleep(0.05)
					self.serial_object = None
					if fail_num > 25:
						# print '** Could Not Connect to ' + port_name + '. Disconnect any programs/peripherals connected to COM port. **'	
						# traceback.print_exc()
						passed = True
					else:
						self.connection_good = False	
						passed = False
		return self.connection_good
				
	def close(self):
		if self.serial_object != None:
			if self.serial_object.isOpen():
				try:
					self.serial_object.close()
				except:
					return -1
			return 1
		else:
			return -1
	