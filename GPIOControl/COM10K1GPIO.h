/** 
 * @file COM10K1GPIO.h
 * @author RidgeRun, editted by Blaze Sanders SpaceVR(TM) 
 * @date 06/01/2016
 * @link http://elinux.org/Jetson/GPIO
 * @version 1.0
 *
 * @brief Low level driver for GPIO pins on COM10K1 / CCG020
 *
 * @section DESCRIPTION
 *
 * Program to configure and control the General Purpose Input / Output 
 * (GPIO) pins of the TK1 exposed through the Connect Tech CGC020 
 * breakout board connector P19 (Misc/Systtem Connector). Possible 
 * states. (Input or Output and High, Low, or Pulse Width Modulation) 
 * 
 * The GPIO pins on Connect Tech CGC020 are all 3.3V logic but 
 * can only supply a few milli-amps of current, so you can't simply 
 * attach common 3.3V logic signals or devices. One-way opto-isolated
 * level shifter are the preffered method for connecting the CGC020  
 * to external devices, since its a more rugged method. 
 * See www.sparkfun.com/products/9118 for example opto shifters.
 * 
 * Chrono timing variables will roll over at 06:28:16 UTC on 
 * Thursday, 7 February 2036. Meta data timestamps will be invalid!!!
 */
 
#ifndef COM10K1_GPIO_H
#define COM10K1_GPIO_H

#include <iostream>      //Standard input/output stream objects, needed to use cout()
#include <string.h>      //Used for strlen() function
#include <cassert>       //Used in UnitTest for functional testing

//Header files to use system close(), open() and ioctl() functions.
#include <unistd.h>  
#include <fcntl.h>
#include <sys/ioctl.h>

#include <chrono>        //High accuracy microsecond timing in unit test


#define DEBUG_STATEMENTS_ON 1   //Toggle error messages on and off

//Pin value constants
#define LOW   0   
#define HIGH  1
#define UNDEFINED -1
//TO-DO: #define PWM_TWO_PERCENT to PWM_HUNDRED_PERCENT in two percent steps

//Pin direction constants
#define INPUT_PIN 0
#define OUTPUT_PIN 1
//TO-DO: #define PWM 2


//Connect Tech CCG020 Linux refernce pin constants as defined in rc.local script on Abaco COM10K1
#define NUM_GPIO_PINS 8      //Outputs: GPO0 to GPO3 Inputs: GPI0 to GPI3
#define NUM_OUTPUT_PINS 4    //The COM10K1 has four output pins when connected to the CCG020
#define NUM_INPUT_PINS 4     //The COM10K1 has four input pins when connected to the CCG020
#define INPUT_PIN_OFFSET 160 //Offset for easier access to array element (i.e. GPIO - 160 = Array element 0)
#define GPI0 160             //CCG020 Connector P17 Pin # 17 & COM10K1 Connector J1 Pin # A93
#define GPI1 161             //CCG020 Connector P17 Pin # 19 & COM10K1 Connector J1 Pin # B54
#define GPI2 162             //CCG020 Connector P17 Pin # 18 & COM10K1 Connector J1 Pin # B57
#define GPI3 163             //CCG020 Connector P17 Pin # 20 & COM10K1 Connector J1 Pin # B63
#define GPO0 164             //CCG020 Connector P17 Pin # 9 & COM10K1 Connector J1 Pin # A54
#define GPO1 165             //CCG020 Connector P17 Pin # 11 & COM10K1 Connector J1 Pin # A63
#define GPO2 166             //CCG020 Connector P17 Pin # 13 & COM10K1 Connector J1 Pin # A67
#define GPO3 83              //CCG020 Connector P17 Pin # 15 & COM10K1 Connector J1 Pin # A85

//TO-DO??? remove these
//string  GPIO_PU0  = "gpio160";      


/** Copy of rc.local.sh file at filepath /etc/rc.local
  #disable pause frame support
  ethtool -A eth0 autoneg off rx off tx off
  #reset link to promote auto negotiation.
  ethtool -r eth0
  echo "MC10K1 - rc.local: Disabled pause frame support and reset eth0" > /dev/kmsg
  echo 160 > /sys/class/gpio/export
  echo 161 > /sys/class/gpio/export
  echo 162 > /sys/class/gpio/export
  echo 163 > /sys/class/gpio/export
  echo 164 > /sys/class/gpio/export
  echo 165 > /sys/class/gpio/export
  echo 166 > /sys/class/gpio/export
  echo 83 > /sys/class/gpio/export
  echo out > /sys/class/gpio/gpio164/direction
  echo out > /sys/class/gpio/gpio165/direction
  echo out > /sys/class/gpio/gpio166/direction
  echo out > /sys/class/gpio/gpio83/direction
  chmod a+rw /sys/class/gpio/gpio160/value
  chmod a+rw /sys/class/gpio/gpio161/value
  chmod a+rw /sys/class/gpio/gpio162/value
  chmod a+rw /sys/class/gpio/gpio163/value
  chmod a+rw /sys/class/gpio/gpio164/value
  chmod a+rw /sys/class/gpio/gpio165/value
  chmod a+rw /sys/class/gpio/gpio166/value
  chmod a+rw /sys/class/gpio/gpio83/value
  chmod a+rw /sys/class/gpio/gpio160/edge
  chmod a+rw /sys/class/gpio/gpio161/edge
  chmod a+rw /sys/class/gpio/gpio162/edge
  chmod a+rw /sys/class/gpio/gpio163/edge
*/


#define SYSFS_GPIO_DIR "/sys/class/gpio"    //Base filepath for GPIO control
#define POLL_TIMEOUT 3000                   //3000 milliseconds = 3 seconds 
#define MAX_BUF 64                          //Used in private functions to store file descriptor data TO-DO???
	 
typedef struct gpioPin
{
  unsigned int pinName[NUM_GPIO_PINS];      //Eight Connect Tech CCG020 pin names (i.e. GPI0, GPO3, etc.)
  unsigned int pinDirection[NUM_GPIO_PINS]; //Direction on the eight GPIO pins (i.e. Input or Output)
  int pinValue[NUM_GPIO_PINS];              //Current state of the eight input or output pins (i.e. High or Low)
  //TO-DO??? REMOVE int fileDescriptor;       //File ID # for use with system open(), close(), and ioctl() functions 
  //TO-DO??? REMOVE int fdArray[[NUM_GPIO_PINS-1]];  //Array to store all file descriptors for the COM10K1 
} GPIOPins_t;
 

//Public Function Prototypes with system calls to get, set, and test GPIO pin logic levels

 /**
  * @breif Configure the COM10K1GPIO.h struct to match the hardware requirments on the Abaco COM10K1
  *
  * @section DESCRIPTION
  *
  * Outputs pins default to LOW and input default to an UNDEFINED state.
  *
  * @param GPIOpin Pointer to struct holding array of eight (NUM_GPIO_PINS) elements
  * @param initOutputPinValues Initial logic levels (HIGH or LOW) for the four output pins on the CCG020
  *
  * @see Input pins default to LOW before first attempted read state
  *
  * @return NOTHING 
  */ 
void InitializePins(GPIOPins_t *GPIOpin, unsigned int initOutputPinValues[]);

/**
 * @brief Read the currect logic level (HIGH or LOW) on an input pin.
 *
 * @param GPIOpin Pointer to struct holding array of eight (NUM_GPIO_PINS) elements
 * @param name Connect Tech CCG020 pin name (i.e. GPI0, GPO3, etc.)
 * 
 * @return Logic level on input pin (1 = HIGH and 0 = LOW)
 */
unsigned int ReadInputPinState(GPIOPins_t *GPIOpin, unsigned int name);

/**
 * @brief Write logic level (HIGH or LOW) to an output pin.
 *
 * @param GPIOpin Pointer to struct holding array of eight (NUM_GPIO_PINS) elements
 * @param name Connect Tech CCG020 pin name (i.e. GPI0, GPO3, etc.)
 * @param newPinValue Logic level to output on GPIO pin
 *
 * @return NOTHING
 */
void WriteOutputPinState(GPIOPins_t *GPIOpin, unsigned int name, unsigned int newPinValue); 

/**
 * @brief Convert an output pin on CCG020 to an input pin.
 * 
 * @section DESCRIPTION
 *
 * Public function to TO-DO??? NOTE!!! Changing the inputs to outputs may cause damage to the COM10K1.
 *
 * TO-DO??? @param name Connect Tech CCG020 pin name (i.e. GPI0, GPO3, etc.)
 * @param direction New direction of the GPIO pin (i.e. Input or Output)
 * TO-DO??? @param initValue Initalize value to set an output pin to (N/A for input pins).
 *
 * @return FALSE = 0 if successful, TRUE = 1 otherwise 
 */
unsigned int ChangeOutputPinToInput(unsigned int name, unsigned int direction, unsigned int initValue);

/**
 * @brief Print the logic levels of all eight GPIO pins
 * 
 * @param C Struct with GPIO pin variables (pinName, pinValue, pinDirection)
 * 
 * @return NOTHING
 */
void DisplayAllPins(GPIOPins_t GPIO_pins);

/**
 * @brief Test GPIO pin using assertions, two hardware configurations, and user input.
 *
 * @param NONE
 *
 * @return NOTHING
 */
void UnitTest();

/**
 * @brief Test high accuracy (microsecond) timing of Mission Elaspe Time (MET) pin state toggling.
 *
 * @param NONE
 *
 * @return NOTHING
 */
void UnitTest_MET();


//Private Function Prototypes with system calls to get and set low level GPIO pin configuration

/**
 * @brief Add a GPIO pin to /sys/kernel/debug/gpio table
 * 
 * @section DESCRIPTION
 *
 * This function should NEVER be called but has been added for completion. On boot the
 * Abaco COM10K1 runs a script "rc.local" in the "???"" directory that performs this task.
 *
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example 
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */ 
static int gpio_export(unsigned int gpio);


/**
 * @brief Remove GPIO pin to /sys/kernel/debug/gpio table.
 * 
* @section DESCRIPTION
 *
 * TO-DO???
 *
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example 

 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */ 
static int gpio_unexport(unsigned int gpio);


/**
 * @brief Set direction of GPIO output pin (i.e INPUT_PIN or OUTPUT_PIN)
 *
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 * @param out_flag Desired direction of pin (INPUT_PIN  = 0 or OUTPUT_PIN = 1)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example 
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */ 
static int gpio_set_dir(unsigned int gpio, unsigned int out_flag);


/**
 * @brief Set value of GPIO output pin (i.e LOW, HIGH, or TO-DO??? PWM)
 *
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 * @param value Desired value/state of pin (LOW  = 0, HIGH = 1, or TO-DO??? TWO_PERCENT = 2)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example 
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */
static int gpio_set_value(unsigned int gpio, unsigned int value);


/**
 * @brief Get value of GPIO input pin (i.e LOW or HIGH)
 * 
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 * @param value Current value/state of pin (LOW  = 0 or HIGH = 1)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example 
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */
static int gpio_get_value(unsigned int gpio, unsigned int *value);


/**
 * @brief TO-DO???
 *
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 * @param edge TO-DO???

 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example ???
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */
static int gpio_set_edge(unsigned int gpio, char *edge);


/**
 * @brief Open file and create File Descriptor ID to control a GPIO pin
 * 
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example ???
 *
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */
static int gpio_fd_open(unsigned int gpio);


/**
 * @brief Close the file controlling a GPIO pin
 * 
 * @param gpio Name of the GPIO pin to open on the COM10K1 (i.e. GPI0, GPO3, etc.)
 *
 * @link https://github.com/derekmolloy/boneDeviceTree/tree/master/gpio
 * @see GPIOSetup.sh file for command line example ???
 * 
 * @return FALSE = 0 if no errors, TRUE = 1 otherwise
 */
static int gpio_fd_close(int fd);

#endif //COM10K1_GPIO_H


/* Copyright Derek Molloy, School of Electronic Engineering, Dublin City University
 * www.derekmolloy.ie
 *
 * Based on Software by RidgeRun
 * Copyright (c) 2011, RidgeRun
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *    This product includes software developed by the RidgeRun.
 * 4. Neither the name of the RidgeRun nor the
 *    names of its contributors may be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY RIDGERUN ''AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL RIDGERUN BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
