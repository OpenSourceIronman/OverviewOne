__author__ = "Steve Alvarado"
__email__ = "alvarado@tethers.com"
__status__ = "Development"
__date__ = "Late Updated: 7/9/14"

def fletcher16(s):
    a = 0		# lower byte
    b = 0  		# upper byte
    
    for letter in s:
        # ord returns the ASCII code for a single-character string
        a = (a + ord(letter)) % 255
        b = (b + a) % 255

    return (b * 256) + a

if __name__ == '__main__':
	s = raw_input("enter name to hash: ")
	print fletcher16("bintest")
	raw_input("press enter to continue...")