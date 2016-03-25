#include <iostream>
#include "JetsonI2C.h"
//#include "CSXUEPS381.h"	

//Header files to use system close(), open() and ioctl() functions.
#include <unistd.h> 
#include <fcntl.h>
#include <sys/ioctl.h>

//Header files to use I2C_SLAVE constant  
#include <linux/i2c-dev.h> 

using namespace std;

/**Default Constructor with error message.
 */
JetsonI2C::JetsonI2C(){
  cout << "I'm sorry Dave, I'm afraid I can't do that. K1 I2C bus was NOT created!" << endl;
}

/**Default Destructor to close I2C bus file. 
 */
JetsonI2C::~JetsonI2C(){
  if (DEBUG) cout << "I2C bus " << busName << " was deleted." << endl;
  if (fileDescriptor >= 0){
    close(fileDescriptor);
  }
}

/**Standard Constructor to create an I2C bus with specific pull-up voltage.
 * @param name Name of the I2C bus to create and open on the NVIVDA K1. 
 * @param voltage Voltage to which the I2C bus is pulled up to (1.8V or 3.3V) 
 */ 
JetsonI2C::JetsonI2C(const char *name, double voltage){
  //ADD VOLTAGE SELECTION LOGIC HERE
  if(voltage == 3.3){
  
  }else if(voltage == 1.8){
  
  }else{
	  
  } 
  
  int fileDescrip = open(name, O_RDWR);
  
  if(fileDescrip < 0){
    if(DEBUG){
      cout << "Failed to open the " << name << " I2C bus." << endl;
      cout << "Please use one of the following three bus name constants:" << endl;
      cout << "GEN1_I2C     (connected to /dev/i2c-0)" << endl;
      cout << "GEN2_I2C_3V3 (connected to /dev/i2c-1)" << endl;
      cout << "CAM1_I2C_3V3 (connected to /dev/i2c-2)" << endl;
	}
  }
  else{
    if(DEBUG) cout << "The " << name << " I2C bus was opened." << endl;
    busName = name;
    busVoltage = voltage;
    fileDescriptor = fileDescrip;
  }
}

/**Initiate communication with an I2C peripheral device. 
 * All subsequent writes and reads will be sent to this device.
 * @param devices Device 7-bit (left zero padded) addresses (i.e 0bZ0101001).
 * @return Negative integer if an error occured, 0 or greater status result otherwise.
 */ 
int JetsonI2C::SelectSlaveDevice(char deviceAddress){
  int operationResult = ioctl(fileDescriptor, I2C_SLAVE, deviceAddress);
 
  if(operationResult < 0) if (DEBUG) cout << "Failed to acquire bus access and/or talk to slave." << endl;	
 
  return operationResult;	  
}

/**Read the specified number data bytes from an I2C device. 
 * @param deviceAddress External I2C bus address of I2C device. 
 * @param registerAddress Internal register address to read from.
 * @param numOfBytes Number of bytes to attempt to read (Must is less than MAX_DATA_BYTE_LENGTH).
 * @return data (up to 64 bits) read from the I2C device.
 */ 
unsigned long long int JetsonI2C::ReadData(char deviceAddress, char registerAddress[MAX_REGISTER_ADRESS_BYTE_LENGTH], unsigned int numOfBytes){
  char buffer[MAX_DATA_BYTE_LENGTH+1] = {0x00}; //One extra bytes for left shifting
  unsigned int data = 0x00000000;
  
  SelectSlaveDevice(deviceAddress);
  
  if(write(fileDescriptor, registerAddress, 1) != 1 || (MAX_DATA_BYTE_LENGTH < numOfBytes)){
    if(DEBUG) cout << "Failed to write device register address to the i2c bus." << endl;
  }
  
  if(read(fileDescriptor, buffer, numOfBytes) != numOfBytes || (MAX_DATA_BYTE_LENGTH < numOfBytes)){
    if(DEBUG){
	  cout << "Failed to read " << numOfBytes << "bytes from the i2c bus." << endl;
	  cout << "The max data read length is " << MAX_DATA_BYTE_LENGTH  << " bytes." << endl;
	}
  }
  else{
	for(int i = 0; i < numOfBytes; i++){
      data +=  (buffer[i]&0x00FF) <<(8*i);
	}
  }
  
  return data;
}

/**Write the specified number data bytes to an I2C device. 
 * @param deviceAddress External I2C bus address of I2C device. 
 * @param registerAddress Internal register address to read from.
 * @param data[] Data byte array to write to the I2C device.
 * @param numOfBytes Number of bytes to attempt to write (Must is less than MAX_DATA_BYTE_LENGTH).
 */  
void JetsonI2C::WriteData(char deviceAddress, char registerAddress[MAX_REGISTER_ADRESS_BYTE_LENGTH], char data[MAX_DATA_BYTE_LENGTH], unsigned int numOfBytes){
   
  SelectSlaveDevice(deviceAddress);
  
  if(write(fileDescriptor, registerAddress, 1) != 1 || (MAX_DATA_BYTE_LENGTH < numOfBytes)){
    if(DEBUG) cout << "Failed to write device register address to the i2c bus." << endl;
  }
  
  for(int i = 0; i < numOfBytes; i++){
    write(fileDescriptor, &data[i], 1);
  }//END FOR LOOP
}

/** Unit Test:
 *  Test #1 - LSB first to unsigned long long int conversion 
 *  Test #2 - Create three good I2C buses and attempt to create one bad one
 */ 
void JetsonI2C::UnitTest(){

  //Make sure to run the compiled executable under admin / sudo privileges 
  
  cout << "TEST #1:" << endl;	
  char buffer[MAX_DATA_BYTE_LENGTH+1] = {0x80, 0x96, 0x98, 0x00, 0x00}; //10,000,000 = 0x989680
  int numOfBytes = 3;
  unsigned long long int data = 0;
 
  for(int i = 0; i < numOfBytes; i++){
    data +=  (buffer[i]&0x00FF) <<(8*i);
    cout << "Data during for loop #" << i << " is = " << data << endl;
  }
  
  cout << "TEST #2:" << endl;
  JetsonI2C BadI2CBus = JetsonI2C();
  JetsonI2C I2CBus1 = JetsonI2C(GEN1_I2C, 1.8); 
  JetsonI2C I2CBus2 = JetsonI2C(GEN2_I2C_3V3, 3.3); 
  JetsonI2C I2CBus3 = JetsonI2C(CAM1_I2C_3V3, 3.3); 
  
//char dataTx[MAX_DATA_BYTE_LENGTH] = {0x53, 0x50, 0x41, 0x43, 0x45, 0x56, 0x52, 0x21};
  char dataTx[MAX_DATA_BYTE_LENGTH] = {'S', 'P', 'A', 'C', 'E', 'V', 'R', '!'};
  
  char regAddress[MAX_REGISTER_ADRESS_BYTE_LENGTH] = {0x58};
  
  I2CBus2.WriteData(0x40, regAddress, dataTx, MAX_DATA_BYTE_LENGTH);
  
  data = I2CBus2.ReadData(0x40, regAddress, MAX_DATA_BYTE_LENGTH);
  
  cout << "Data read from I2C device address 0x40 was " << data << endl;
  
}
