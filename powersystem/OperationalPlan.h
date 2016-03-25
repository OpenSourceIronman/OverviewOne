#ifndef OPERATIONAL_PLAN_H
#define OPERATIONAL_PLAN_H

#define DEBUG 1
#define HALF_ORBIT 45
#define FULL_ORBIT 90
#define FINAL_ORBIT 3 //2912 = 16 orbits a day for 182 days (~6 months)         
#define ORBIT_PLANNING_RESOLUTION 45 // Units [1
#define SUNRISE 0
#define NO_CHANGE 1
#define SUNSET 2

class OperationalPlan
{ 
  public:
    OperationalPlan();
    OperationalPlan(bool);
    ~OperationalPlan();
    OperationalPlan(bool [], int);
    bool getPowerPlan(int, int);
    void setPowerPlan(int, int, bool);
    void printPowerPlan();
    int getSunPosition(int, bool, bool);
        
  private:
    bool powerPlan[FINAL_ORBIT*(FULL_ORBIT/ORBIT_PLANNING_RESOLUTION)];
    int ORBITAL_DATA_POINTS;
    
    bool currentIlluminationState;
    bool previousIlluminationState;
    int illuminationStateChange;
};

#endif
