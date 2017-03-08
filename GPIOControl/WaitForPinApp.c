/** 
 * @file WaitForPinApp.c
*  @author A.P.Hurst SpaceVR(TM) 
 * @date Mar 7, 2017
 * @version 1.0
 * 
 * @brief Wait for an input pin to go high, print its number, and return.
 * 
 * @section DESCRIPTION
 * 
 * The high signal must last for a minimum of 1ms.
 */

#include "COM10K1GPIO.h"

#include <unistd.h>

int main(int argc, char *argv[])
{
    DEBUG_STATEMENTS_ON=false;

    GPIOPins_t GPIO_pins;
    unsigned int initOutputPinValues[NUM_OUTPUT_PINS] = {HIGH, HIGH, HIGH, HIGH};

    InitializePins(&GPIO_pins, initOutputPinValues);

    while(1) {
        for(int i = 0; i < NUM_INPUT_PINS; i++) {
            if (ReadInputPinState(&GPIO_pins, GPIO_pins.pinName[i]) == HIGH) {
                printf("%d\n", i);
                return 0; // success
            }
        }

        usleep(1000 /*microseconds*/);
    }

    return 1;
}
