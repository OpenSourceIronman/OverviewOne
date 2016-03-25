#ifndef CSXUEPS381_H
#define CSXUEPS381_H

#define DEBUG 1

#define EPS1_DEVICE_ADDRESS 0x2B
#define EPS2_DEVICE_ADDRESS 0x2C

Class CSXUEPS381
{
  public: 
    /** Commands aviable to the CSiXUEPS-381 EPS
     * @see http://www.clyde-space.com/documents/712/712.pdf page 37
     */ 
    enum EPS_COMMANDS{
	  GET_BOARD_STATUS = 0x01,
	  SET_PCM_RESET = 0x02	
	};
  
  private:

};

/** Unit Test
 * 
 */ 
int unitTest(){
 
 	
 return 0;
}

#endif
