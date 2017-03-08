from swiftradio.clients import SwiftRadioEthernet

radio = SwiftRadioEthernet("198.27.128.3")

if radio.connect():
  sysinfo = radio.execute_command("sysinfo")
  print "You have successfully connected to radio 0x{}.".format( sysinfo["id"] )
  radio.disconnect()
