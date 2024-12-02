#include "Arduino.h"
#include "LoraTracker.h"
#include "bits/stdc++.h"
using namespace std;

LoraTracker::LoraTracker(){
  
}

void LoraTracker::init(){
  readyRX = 0;
  enSleep = 0;
  enMenu = 0;
  boundaryAlert = 0;
  cycleTime = 0;
  flagsStr = " ";
}

// Function for splitting string message from RPI (from Stack)
String LoraTracker::split(String data, char separator, int index)
{
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length()-1;

  for(int i=0; i<=maxIndex && found<=index; i++){
    if(data.charAt(i)==separator || i==maxIndex){
        found++;
        strIndex[0] = strIndex[1]+1;
        strIndex[1] = (i == maxIndex) ? i+1 : i;
    }
  }

  return found>index ? data.substring(strIndex[0], strIndex[1]) : "";
}

// Function for setting flags by converting message string to individual ints
void LoraTracker::set_flags(String message){
  flagsStr = message;

  static String f[5];
  static int flags[5];

   for (int i = 0; i <= 5; i++){
    f[i] = split(flagsStr, ',', i);
  }
  
  for (int i = 0; i <= 5; i++){
    flags[i] = f[i].toInt();
  }

  readyRX = flags[0];
  enSleep = flags[1];
  enMenu = flags[2];
  boundaryAlert = flags[3];
  cycleTime = flags[4];
}

String LoraTracker::get_flagsStr(){
  return flagsStr;
}

int LoraTracker::get_readyRX(){
  return readyRX;
}

int LoraTracker::get_enSleep(){
  return enSleep;
}

int LoraTracker::get_enMenu(){
  return enMenu;
}

int LoraTracker::get_boundaryAlert(){
  return boundaryAlert;
}

int LoraTracker::get_cycleTime(){
  return cycleTime;
}
