/** 
 * @file COM10K1GPIO.c
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

#include "COM10K1GPIO.h"


//See COM10K1GPIO.h for further documentation on the following PUBLIC functions:

void InitializePins(GPIOPins_t *GPIOpin, unsigned int initOutputPinStates[]){
  
  bool OK = false;

  GPIOpin->pinName[0] = GPI0;
  GPIOpin->pinName[1] = GPI1;
  GPIOpin->pinName[2] = GPI2;
  GPIOpin->pinName[3] = GPI3;
  GPIOpin->pinName[4] = GPO0;
  GPIOpin->pinName[5] = GPO1;
  GPIOpin->pinName[6] = GPO2;
  GPIOpin->pinName[7] = GPO3;

  //Set pin directions as defined by Abaco COM10K1 hardware requirments
  GPIOpin->pinDirection[0] = INPUT_PIN;
  GPIOpin->pinDirection[1] = INPUT_PIN;
  GPIOpin->pinDirection[2] = INPUT_PIN;
  GPIOpin->pinDirection[3] = INPUT_PIN;
  GPIOpin->pinDirection[4] = OUTPUT_PIN;
  GPIOpin->pinDirection[5] = OUTPUT_PIN;
  GPIOpin->pinDirection[6] = OUTPUT_PIN;
  GPIOpin->pinDirection[7] = OUTPUT_PIN;
  
  OK = ReadInputPinState(GPIOpin, GPI0); 
  OK = ReadInputPinState(GPIOpin, GPI1);
  OK = ReadInputPinState(GPIOpin, GPI2);
  OK = ReadInputPinState(GPIOpin, GPI3);
  WriteOutputPinState(GPIOpin, GPO0, initOutputPinStates[0]);	     //GPIOpin->pinValue[4]
  WriteOutputPinState(GPIOpin, GPO1, initOutputPinStates[1]);
  WriteOutputPinState(GPIOpin, GPO2, initOutputPinStates[2]);
  WriteOutputPinState(GPIOpin, GPO3, initOutputPinStates[3]);

  if(!OK && DEBUG_STATEMENTS_ON) printf("InitializePins(&GPIOoin, initOutputPinStates[]) function failed. \n");
 
}


unsigned int ReadInputPinState(GPIOPins_t *GPIOpin, unsigned int name){
  
  if(DEBUG_STATEMENTS_ON) printf("Getting new gpio%d pin value. \n", name);
  
  unsigned int newpinValue = UNDEFINED;
  bool OK = false; 

  OK = gpio_get_value(name, &newpinValue);
  GPIOpin->pinValue[name-INPUT_PIN_OFFSET] = newpinValue;

  if(!OK && DEBUG_STATEMENTS_ON) printf("Private gpio_get_value(gpio%d, &value) function failed. \n", name);
  
  return newpinValue;
}


void WriteOutputPinState(GPIOPins_t *GPIOpin, unsigned int name, unsigned int newPinValue){
  if(DEBUG_STATEMENTS_ON) printf("Setting gpio%d pin to %d \n", name, newPinValue);
  
  bool OK = false; 

  OK = gpio_set_value(name, newPinValue);
  switch(name)
  {
    case GPO0: GPIOpin->pinValue[0] = newPinValue; break;
    case GPO1: GPIOpin->pinValue[1] = newPinValue; break;
    case GPO2: GPIOpin->pinValue[2] = newPinValue; break;
    case GPO3: GPIOpin->pinValue[3] = newPinValue; break;
    default: printf("Invalid output pin name used. Try something other than gpio%d \n", name);
  }//END SWITCH

  if(!OK && DEBUG_STATEMENTS_ON) printf("Private gpio_set_value(gpio%d, &value) function failed. \n", name);
}

int ChangeOutputPinToInput(unsigned int name, unsigned int direction, unsigned int initValue){
  //TO-DO??? NOTE!!! Changing the inputs to outputs may cause damage to the COM10K1.
}

void DisplayAllPins(GPIOPins_t GPIO_pins){
  printf("Input pin GPI0  = %i, Input pin GPI1  = %i, Input pin GPI2  = %i, Input pin GPI3  = %i \n", GPIO_pins.pinValue[0], GPIO_pins.pinValue[1], GPIO_pins.pinValue[2], GPIO_pins.pinValue[3]);
  printf("Output pin GPO0  = %i, Output pin GPO1  = %i, Output pin GPO2  = %i, Output pin GPO3  = %i \n" , GPIO_pins.pinValue[4], GPIO_pins.pinValue[5], GPIO_pins.pinValue[6], GPIO_pins.pinValue[7]); 
}


void UnitTest(){	
  
  
  GPIOPins_t GPIO_pins;
  unsigned int initOutputPinValues[NUM_OUTPUT_PINS] = {HIGH, HIGH, HIGH, HIGH};   //TO-DO??? NUM_OUTPUTS_PINS-1 was incorrect?
  
  printf("STARTING UNIT TEST\n");

  InitializePins(&GPIO_pins, initOutputPinValues);

  if(DEBUG_STATEMENTS_ON) printf("Pin initialization complete \n");

  if(DEBUG_STATEMENTS_ON) DisplayAllPins(GPIO_pins);
   
  char userInput = 'N';

  while(userInput != 'Y' && userInput != 'y'){    
    printf("Please connect input pins 0, 1, 2, and 3 to 0.0 Volts, then type 'Y' and hit enter to continue...\n");
    userInput = getchar();
  }//END WHILE LOOP

  
  assert(ReadInputPinState(&GPIO_pins, GPI0)); 
  assert(ReadInputPinState(&GPIO_pins, GPI1)); 
  assert(ReadInputPinState(&GPIO_pins, GPI2)); 
  assert(ReadInputPinState(&GPIO_pins, GPI3)); 
  
  
  if(DEBUG_STATEMENTS_ON) DisplayAllPins(GPIO_pins);
  assert(GPIO_pins.pinValue[0] == LOW);
  assert(GPIO_pins.pinValue[1] == LOW);
  assert(GPIO_pins.pinValue[2] == LOW);
  assert(GPIO_pins.pinValue[3] == LOW);
  assert(GPIO_pins.pinValue[4] == HIGH);
  assert(GPIO_pins.pinValue[5] == HIGH);
  assert(GPIO_pins.pinValue[6] == HIGH);
  assert(GPIO_pins.pinValue[7] == HIGH);

  while(userInput != 'Y' && userInput != 'y'){
    printf("Please connect input pins 0, 1, 2, and 3 to 3.3Volts, then type 'Y' and hit enter to continue...\n");
    userInput = getchar();
  }//END WHILE LOOP
  assert(ReadInputPinState(&GPIO_pins, GPI0)); 
  assert(ReadInputPinState(&GPIO_pins, GPI1)); 
  assert(ReadInputPinState(&GPIO_pins, GPI2)); 
  assert(ReadInputPinState(&GPIO_pins, GPI3)); 
  
  
  for(int k = NUM_GPIO_PINS/2; k < NUM_GPIO_PINS; k++){
   WriteOutputPinState(&GPIO_pins, GPIO_pins.pinName[k], LOW);        //GPIOpin->pinValue[4]
  }
  
  if(DEBUG_STATEMENTS_ON) DisplayAllPins(GPIO_pins);
  assert(GPIO_pins.pinValue[0] == HIGH);
  assert(GPIO_pins.pinValue[1] == HIGH);
  assert(GPIO_pins.pinValue[2] == HIGH);
  assert(GPIO_pins.pinValue[3] == HIGH);
  assert(GPIO_pins.pinValue[4] == LOW);
  assert(GPIO_pins.pinValue[5] == LOW);
  assert(GPIO_pins.pinValue[6] == LOW);
  assert(GPIO_pins.pinValue[7] == LOW);

  
  printf("Unit Test successful. Visit www.spacevr.co and #BeAnAstronaut today!\n");
  
}

void UnitTest_MET(){
  
  //Setup time variables to track Mission Elapsed Time (MET)
  time_t timer;
  time(&timer);                   
  struct tm MissionElapsedTime;
  int START_OF_YEAR_EPOCH = 1900; //Start of Network Time Protocol epoch. Will roll over At 06:28:16 UTC on Thursday, 7 February 2036

  auto start = std::chrono::high_resolution_clock::now(); //Time this line of code / mission started

  //TO-DO??? DO STUFF HERE

  usleep(1000000); //Delay as part of MET test

  //printf("Mission Elaspe Time (MET) rising edge TRIGGER timeStamp (i.e Year_Month_MonthDay_Hour_Minutes_MilliSeconds) = %d_%d_%d_%d_%d_", 
  //      (MissionElapsedTime.tm_year+START_OF_YEAR_EPOCH), MissionElapsedTime.tm_mon, MissionElapsedTime.tm_mday, MissionElapsedTime.tm_hour, MissionElapsedTime.tm_min);

  MissionElapsedTime = *localtime(&timer);
  auto elapsed = std::chrono::high_resolution_clock::now() - start;
  long long elapsedMircoSeconds = std::chrono::duration_cast<std::chrono::microseconds>(elapsed).count();

  printf("MET = %d microseconds. \n", std::chrono::duration_cast<std::chrono::microseconds>(elapsed).count());
}



//See COM10K1GPIO.h for further documentation on the following PRIVATE functions:

int gpio_export(unsigned int gpio){
  int fd, len;
  char buf[MAX_BUF];
  
  fd = open(SYSFS_GPIO_DIR "/export", O_WRONLY);
  
  if (fd < 0) {
    perror("gpio/export");
    return fd;
  }
 
  len = snprintf(buf, sizeof(buf), "%d", gpio);
  write(fd, buf, len);
  close(fd);
  
  return 0;
}


int gpio_unexport(unsigned int gpio){
  int fd, len;
  char buf[MAX_BUF];
  fd = open(SYSFS_GPIO_DIR "/unexport", O_WRONLY);
  
  if (fd < 0) {
	perror("gpio/export");
	return fd;
  }

  len = snprintf(buf, sizeof(buf), "%d", gpio);
  write(fd, buf, len);
  close(fd);

  return 0;
}


int gpio_set_dir(unsigned int gpio, unsigned int out_flag){
  int fd;
  char buf[MAX_BUF];
  
  if(DEBUG_STATEMENTS_ON) printf("Accessing filepath: " SYSFS_GPIO_DIR "/gpio%d/direction to set direction \n", gpio);
  snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/direction", gpio);

  fd = open(buf, O_WRONLY);

  if (fd < 0) {
	perror("gpio/direction");
	return fd;
  }

  if (out_flag == OUTPUT_PIN)
	write(fd, "out", 4);
  else
	write(fd, "in", 3);
  
  close(fd);

  return 0;
}


int gpio_set_value(unsigned int gpio, unsigned int value){
  int fd;
  char buf[MAX_BUF];
  
  if(DEBUG_STATEMENTS_ON) printf("Accessing filepath: " SYSFS_GPIO_DIR "/gpio%d/value to set value \n", gpio);
  snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
  fd = open(buf, O_WRONLY);

  if (fd < 0) {
	perror("gpio/set-value");
	return fd;
  }

  if (value==LOW)
    write(fd, "0", 2);
  else
    write(fd, "1", 2);

  close(fd);

  return 0;
}


int gpio_get_value(unsigned int gpio, unsigned int *value){
  int fd;
  char buf[MAX_BUF];
  char ch;
 
  if(DEBUG_STATEMENTS_ON) printf("Accessing filepath: " SYSFS_GPIO_DIR "/gpio%d/value to get value \n", gpio);
  snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
  fd = open(buf, O_RDONLY);

  if (fd < 0) {
	perror("gpio/get-value");
    return fd;
  }

  read(fd, &ch, 1);

  if (ch != '0') {
	*value = 1;
  } else {
	*value = 0;
  }

  close(fd);

  return 0;
}


int gpio_set_edge(unsigned int gpio, char *edge){
  int fd;
  char buf[MAX_BUF];
  
  if(DEBUG_STATEMENTS_ON) printf("Accessing filepath: " SYSFS_GPIO_DIR "/gpio%d/edge to set input edge type \n", gpio);
  snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/edge", gpio);
  fd = open(buf, O_WRONLY);

  if (fd < 0) {
    perror("gpio/set-edge");
    return fd;
  }
  
  write(fd, edge, strlen(edge) + 1);

  close(fd);

  return 0;
}


int gpio_fd_open(unsigned int gpio){
  int fd;
  char buf[MAX_BUF];

  if(DEBUG_STATEMENTS_ON) printf("Accessing filepath: " SYSFS_GPIO_DIR "/gpio%d/value to OPEN FILE TO-DO??? \n", gpio);
  snprintf(buf, sizeof(buf), SYSFS_GPIO_DIR "/gpio%d/value", gpio);
  fd = open(buf, O_RDONLY | O_NONBLOCK );

  if (fd < 0) {
    perror("gpio/fd_open"); 
  }

  return fd;
}


int gpio_fd_close(int fd){
  return close(fd);
}

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