#ifndef JETSON_I2C_H
#define JETSON_I2C_H

#include <string>

#define DEBUG 1

#define MAX_I2C_DEVICES 127      

<<<<<<< .mine
#define MAX_DATA_BYTE_LENGTH 8   //unsigned long long int 
=======
#define MAX_DATA_BYTE_LENGTH 8  //unsigned long long int
>>>>>>> .r26

#define MAX_REGISTER_ADRESS_BYTE_LENGTH 2

#define GEN1_I2C_SCL 21 //Expansion Connector J3A1 pin 21
#define GEN1_I2C_SDA 23 //Expansion Connector J3A1 pin 23

#define GEN2_I2C_SCL 18 //Expansion Connector J3A1 pin 18
#define GEN2_I2C_SDA 20 //Expansion Connector J3A1 pin 20

#define CAM_I2C_SCL 11  //Expansion Connector J3A2 pin 11
#define CAM_I2C_SDA 8   //Expansion Connector J3A2 pin 8

<<<<<<< .mine
string GEN1_I2C = "/dev/i2c-0";       //Defaults to 1.8V
string GEN2_I2C_3V3 = "/dev/i2c-1";   //Defaults to 3.3V
string CAM1_I2C_3V3 = "/dev/i2c-2";   //Defaults to 1.8V
=======
const char *GEN1_I2C = "/dev/i2c-0";
const char *GEN2_I2C_3V3 = "/dev/i2c-1";
const char *CAM1_I2C_3V3 = "/dev/i2c-2";
>>>>>>> .r26
	
/** Low level driver to control upto three TK1 I2C buses.
 * @see http://elinux.org/Interfacing_with_I2C_Devices  
 * @see http://elinux.org/Jetson/I2C
 * @see https://devtalk.nvidia.com/default/topic/770603/embedded-systems/i2c-port-name-and-i2cbus-number/post/4397340/#4397340
 * @see https://www.sparkfun.com/tutorials/215
 * @see https://learn.sparkfun.com/tutorials/i2c
 */ 
class JetsonI2C
{ 
  public: 
    JetsonI2C();
    ~JetsonI2C();
    JetsonI2C(const char *, double); 

    int SelectSlaveDevice(char); 
    int ChangeBusSpeed(unsigned int);    
    void WriteData(char, char[], char[MAX_DATA_BYTE_LENGTH], unsigned int);
    unsigned long long int ReadData(char, char[], unsigned int);
    void UnitTest();
    
  private:
    const char *busName;        //Possibly options: /dev/i2c-0, /dev/i2c-1, or /dev/i2c-2
    int fileDescriptor;         //File ID # for use with system open(), close(), and ioctl() functions 
    int operationResult;        //Result of last system call to ioctl()  
    double busVoltage;          //Units [Volts = V]
};

#endif
