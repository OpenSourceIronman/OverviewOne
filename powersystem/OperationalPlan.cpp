#include <iostream>
#include "OperationalPlan.h"

using namespace std;

/** Default Constructor which sets powerPlan array to all TRUE / ON
 */
OperationalPlan::OperationalPlan(){
  OperationalPlan(true);
}

OperationalPlan::OperationalPlan(bool powerState){
  ORBITAL_DATA_POINTS = FINAL_ORBIT*(FULL_ORBIT/ORBIT_PLANNING_RESOLUTION);
  
  currentIlluminationState = true;
  previousIlluminationState = false;
  illuminationStateChange = NO_CHANGE;

  for(int i = 0; i < ORBITAL_DATA_POINTS; i++){
    powerPlan[i] = powerState;  
  }//END FOR LOOP
}


/** Default Destructor with part number label
 */
OperationalPlan::~OperationalPlan(){
  if (DEBUG) cout << "OperationalPlan object was deleted." << endl;
}

/** Constructor to fill the powerPlan array with repeating input parameter pattern 
 * @param pattern The operation plan to repeat until final orbit
 */
OperationalPlan::OperationalPlan(bool pattern[], int arrayLength){
  ORBITAL_DATA_POINTS = FINAL_ORBIT*(FULL_ORBIT/ORBIT_PLANNING_RESOLUTION);
  
  for(int i = 0; i < ORBITAL_DATA_POINTS;  i += arrayLength){	   
	if( (i + arrayLength) <= ORBITAL_DATA_POINTS ){
      for(int j = 0; j < arrayLength; j++){ 
        powerPlan[i+j] = pattern[j]; 
	  }//END FOR LOOP
    }//END IF
    else{
	  for(int k = 0; k < ORBITAL_DATA_POINTS - i ; k++){ 
        powerPlan[i+k] = pattern[k]; 
	  }//END FOR LOOP	
	}//ENDELSE 
  }//END OUTER FOR LOOP
}

void OperationalPlan::setPowerPlan(int orbitNumber, int orbitMinute, bool powerState){
  if ( FULL_ORBIT <= orbitMinute || (0 < orbitMinute && orbitMinute < ORBIT_PLANNING_RESOLUTION) ){
    if (DEBUG) cout << "Orbital time was not between " << ORBIT_PLANNING_RESOLUTION << " and " <<  (FULL_ORBIT-1) << " inclusively" << endl;
  }
  else{
    if (!(orbitMinute % ORBIT_PLANNING_RESOLUTION == 0)){
      cout << "OperationalPlan::PowerPlan[] array index is out of bounds." << endl;	  	  
    }
    else{
	  int index = orbitNumber*(FULL_ORBIT/ORBIT_PLANNING_RESOLUTION) + (orbitMinute/ORBIT_PLANNING_RESOLUTION);
      powerPlan[index] = powerState;	 	
	} 
  }
}

bool OperationalPlan::getPowerPlan(int orbitNumber, int orbitMinute){
  if ( FULL_ORBIT <= orbitMinute || (0 < orbitMinute && orbitMinute < ORBIT_PLANNING_RESOLUTION) ){
    if (DEBUG) cout << "Orbital time was not between " << ORBIT_PLANNING_RESOLUTION << " and " <<  (FULL_ORBIT-1) << " inclusively" << endl;
  }
  else{
    if (!(orbitMinute % ORBIT_PLANNING_RESOLUTION == 0)){
      cout << "OperationalPlan::PowerPlan[] array index is out of bounds." << endl;	  
    }
    else{
	  int index = orbitNumber*(FULL_ORBIT/ORBIT_PLANNING_RESOLUTION) + (orbitMinute/ORBIT_PLANNING_RESOLUTION);
      return powerPlan[index];	 	
	} 
  }
}

void OperationalPlan::printPowerPlan(){
  for(int i = 0; i < ORBITAL_DATA_POINTS; i++){
    if (powerPlan[i] == true) cout << "1";
    else cout << "O";
  }//END FOR LOOP	
  cout << endl;
}

int OperationalPlan::getSunPosition(int orbitalTime, bool previousIlluminationState, bool currentIlluminationState){
  if (orbitalTime < HALF_ORBIT) currentIlluminationState = true;
  else if (orbitalTime >= HALF_ORBIT) currentIlluminationState = false;
      
  if (previousIlluminationState == true && currentIlluminationState == false){
    illuminationStateChange = SUNSET; 
  }
  else if (previousIlluminationState == false && currentIlluminationState == true){
    illuminationStateChange = SUNRISE;
  }
  else{
    illuminationStateChange = NO_CHANGE;  
  }	
}

