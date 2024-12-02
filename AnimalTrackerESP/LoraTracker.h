#ifndef Lora_Tracker
#define Lora_Tracker


#include "Arduino.h"


class LoraTracker{

  public:
  LoraTracker();
  void init();
  String split(String data, char separator, int index);
  void set_flags(String message);
  String get_flagsStr();
  int get_readyRX();
  int get_enSleep();
  int get_enMenu();
  int get_boundaryAlert();
  int get_cycleTime(); 


  private:
  int readyRX;
  int enSleep;
  int enMenu;
  int boundaryAlert;
  int cycleTime;
  String flagsStr;
};

#endif
