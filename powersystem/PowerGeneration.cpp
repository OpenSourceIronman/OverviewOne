#include <iostream>
#include "PowerGeneration.h"

using namespace std;

/** Default Constructor which sets powerPlan array to all TRUE / ON
 */
PowerGeneration::PowerGeneration(){
  currentOutput = 0.0;
  voltageOuput = 0.0;
  powerOutput = currentOutput * voltageOuput;
}

PowerGeneration::~PowerGeneration(){
  cout << "PowerGeneration " << partNumber << " object was deleted." << endl;
}

PowerGeneration::PowerGeneration(const char * name, double current, double voltage){
  currentOutput = current;
  voltageOuput = voltage;
  powerOutput = currentOutput * voltageOuput;
}
