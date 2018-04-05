/**
 * @file TX2_GPIOTestApp.c
 * @author Blaze Sanders  ROBO BEV (TM)
 * @email blaze@robobev.com
 * @date  05 APR 2018
 * @version 1.0
 *
 * @brief An example main driver program to excerise TX2GPIO.c
 *
 * @link http://www.jetsonhacks.com/2015/12/29/gpio-interfacing-nvidia-jetson-tx1/
 *
 * @section DESCRIPTION
 *
 */

#include "TX2GPIO.h"

using namespace std;

//Compiled using command "g++ TX2_GPIOTestApp.c TX2GPIO.c -std=c++11 -o TX2_GPIOTestApp"

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

  GPIOPins_t TX2GPIO_pins;
  unsigned int initOutputPinValues[NUM_OUTPUT_PINS] = {HIGH, LOW, LOW, HIGH};

  //PUT YOUR CODE HERE//

}//END MAIN
