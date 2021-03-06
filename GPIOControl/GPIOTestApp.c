/** 
 * @file GPIOTestApp.c
*  @author Blaze Sanders SpaceVR(TM) 
 * @date 02/15/2016
 * @version 1.0
 * 
 * @brief An example main driver program to excerise COM10K1.c
 * 
 * @section DESCRIPTION
 * 
 * The GPIO pins on Connect Tech CGC020 are all 3.3V logic but 
 * can only supply a few milli-amps of current, so you can't simply 
 * attach common 3.3V logic signals or devices. One-way opto-isolated
 * level shifter are the preffered method for connecting the CGC020  
 * to external devices, since its a more rugged method. 
 * See www.sparkfun.com/products/9118 for example opto shifters.
 */

#include "COM10K1GPIO.h"

using namespace std;

//Compiled using command "g++ GPIOTestApp.c COM10K1GPIO.c -std=c++11 -o GPIOTestApp"

int main(int argc, char *argv[])
{
  unsigned int unitTestNumber;

  printf("Program name: %s\n", argv[0]);
  
   if(argc == 2) unitTestNumber = atoi(argv[1]);
   else if( argc > 2 ) printf("Too many arguments supplied. Please enter only single parameter with unit test number to run.\n");
  
  switch(unitTestNumber)
  {
    case 1: UnitTest(); return 0;
    case 2: UnitTest_MET(); return 0;
    default: printf("No unit tests run. Starting your application code now!\n");
  }//END SWITCH
  
  GPIOPins_t mCOM10K1GPIO_pins;
  unsigned int initOutputPinValues[NUM_OUTPUT_PINS] = {HIGH, LOW, LOW, HIGH}; 

  //PUT YOUR CODE HERE// 
   	
}//END MAIN
