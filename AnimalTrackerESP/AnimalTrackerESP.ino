// buzzer
int buzzerPin = 37;
int delayTime = 500;

// gps include
#include "Arduino.h"
#include "HT_st7735.h"
#include "HT_TinyGPS++.h"
#include <TimeLib.h>

// create TinyGPS and Heltec screen objects for GPS
TinyGPSPlus GPS;
HT_st7735 st7735; 

#define VGNSS_CTRL 3

// Tracker class
#include "LoraTracker.h"

LoraTracker Tracker;

// lora include 
#include "LoRaWan_APP.h"
#include "Arduino.h"


// Set up LoRa parameters to match receiver
#define RF_FREQUENCY                                915000000 // Hz

#define TX_OUTPUT_POWER                             15        // dBm

#define LORA_BANDWIDTH                              0         // [0: 125 kHz,
                                                              //  1: 250 kHz,
                                                              //  2: 500 kHz,
                                                              //  3: Reserved]
#define LORA_SPREADING_FACTOR                       7         // [SF7..SF12]
#define LORA_CODINGRATE                             1         // [1: 4/5,
                                                              //  2: 4/6,
                                                              //  3: 4/7,
                                                              //  4: 4/8]
#define LORA_PREAMBLE_LENGTH                        8         // Same for Tx and Rx
#define LORA_SYMBOL_TIMEOUT                         0         // Symbols
#define LORA_FIX_LENGTH_PAYLOAD_ON                  false
#define LORA_IQ_INVERSION_ON                        false


#define RX_TIMEOUT_VALUE                            1000
#define BUFFER_SIZE                                 60 // Define the payload size here

char txpacket[BUFFER_SIZE];
char rxpacket[BUFFER_SIZE];

double txNumber;

bool lora_idle=true;

static RadioEvents_t RadioEvents;
void OnTxDone( void );
void OnTxTimeout( void );

int16_t rssi,rxSize;
void OnRxDone( uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr );

// bool for interrupting lora receive
bool receivedLora;

// Function for getting GPS data and printing it to display
void GPS_read(void)
{
  pinMode(VGNSS_CTRL,OUTPUT);
  digitalWrite(VGNSS_CTRL,HIGH);
  Serial1.begin(115200,SERIAL_8N1,33,34);    
  //Serial.println("GPS_test");
  st7735.st7735_fill_screen(ST7735_BLACK);
  delay(100);
  //st7735.st7735_write_str(0, 0, (String)"GPS_test");
  

  bool GPSNotSent = true;
  while(GPSNotSent)
  {
    if(Serial1.available()>0)
    {
      if(Serial1.peek()!='\n')
      {
        GPS.encode(Serial1.read());
      }
      else
      {
        Serial1.read();
        if(GPS.time.second()==0)
        {
          continue;
        }
        st7735.st7735_fill_screen(ST7735_BLACK);
        st7735.st7735_write_str(0, 0, (String)"GPS_test");
        String time_str = (String)GPS.time.hour() + ":" + (String)GPS.time.minute() + ":" + (String)GPS.time.second()+ ":"+(String)GPS.time.centisecond();
        st7735.st7735_write_str(0, 20, time_str);
        String latitude = "LAT: " + (String)GPS.location.lat();
        st7735.st7735_write_str(0, 40, latitude);
        String longitude  = "LON: "+  (String)GPS.location.lng();
        st7735.st7735_write_str(0, 60, longitude);

        //Serial.printf("Time: %s \n%s\n%s\n", time_str, latitude, longitude);
        GPSNotSent = false;

        
        //delay(5000);
        while(Serial1.read()>0);
      }
    } 
  }  
}

void setup() {
    // buzzer
    pinMode(buzzerPin, OUTPUT);
    
    // tracker class
    Tracker.init();
    
    // gps setup
    delay(100);
    st7735.st7735_init();
    //GPS_read();

    // lora setup
    Serial.begin(115200);
    Mcu.begin(HELTEC_BOARD,SLOW_CLK_TPYE);
    
    // Common setup between reciever and transmitter
    txNumber=0;
    rssi=0;

    // Combined
    RadioEvents.TxDone = OnTxDone;
    RadioEvents.TxTimeout = OnTxTimeout;
    RadioEvents.RxDone = OnRxDone;
    
    Radio.Init( &RadioEvents );
    Radio.SetChannel( RF_FREQUENCY );

    // Transmitter
    Radio.SetTxConfig( MODEM_LORA, TX_OUTPUT_POWER, 0, LORA_BANDWIDTH,
                                   LORA_SPREADING_FACTOR, LORA_CODINGRATE,
                                   LORA_PREAMBLE_LENGTH, LORA_FIX_LENGTH_PAYLOAD_ON,
                                   true, 0, 0, LORA_IQ_INVERSION_ON, 3000 ); 

    // Receiver
    Radio.SetRxConfig( MODEM_LORA, LORA_BANDWIDTH, LORA_SPREADING_FACTOR,
                               LORA_CODINGRATE, 0, LORA_PREAMBLE_LENGTH,
                               LORA_SYMBOL_TIMEOUT, LORA_FIX_LENGTH_PAYLOAD_ON,
                               0, true, 0, 0, LORA_IQ_INVERSION_ON, true );
   
}

void loop() {
  // continuous receiver: lora receive until flags sent from RPI 
  receivedLora = false;
  while(receivedLora == false)
  {
    // lora receive
    if(lora_idle)
    {
      lora_idle = false;
      Serial.println("into RX mode");
      Radio.Rx(0);
    }
    Radio.IrqProcess( );
  }

    // lora transmit con
  if(lora_idle == true)
  {
    delay(1000);
    //txNumber += 0.01;
    sprintf(txpacket,"CON \0");  //start a package
   
    Serial.printf("\r\nsending packet \"%s\" , length %d\r\n",txpacket, strlen(txpacket));
    Radio.Send( (uint8_t *)txpacket, strlen(txpacket) ); //send the package out 
    lora_idle = false;
  }
  Radio.IrqProcess( );

  while(lora_idle == false){
    
  }
  delay(1000);
  // run loop while the RPI readyRX flag is high
  bool sysReady = true;
  while(sysReady)
  {
    // Check/update flags
    int readyRX = Tracker.get_readyRX();
    int enSleep = Tracker.get_enSleep();
    int enMenu = Tracker.get_enMenu();
    int boundaryAlert = Tracker.get_boundaryAlert();
    int cycleTime = Tracker.get_cycleTime();
    int cycleStartTime = 0;
    int elapsedTime;
    

    // if menu flag high, exit loop and return to continuous receive 
    if(enMenu == 1){
      sysReady = false;
    }
    // else if sleep flag high, put in sleep mode (TBD: for now sleep = continuous receiver)
    else if(enSleep == 1){
      sysReady = false;
      // send sleeping flag back
      // lora transmit slp
      if(lora_idle == true)
      {
        delay(1000);
        //txNumber += 0.01;
        sprintf(txpacket,"SLP \0");  //start a package
       
        Serial.printf("\r\nsending packet \"%s\" , length %d\r\n",txpacket, strlen(txpacket));
    
        Radio.Send( (uint8_t *)txpacket, strlen(txpacket) ); //send the package out 
        lora_idle = false;
      }
      Radio.IrqProcess( );      
    }
    // else if readyRX flag, send GPS data (eventually adjust to only send if coordinates > 0)
    else{
      while(lora_idle == false){
        
      }
      
      // Get GPS data
      //while(GPS.location.lat() == 0.0){
      delay(1000);
      GPS_read();
      delay(100);
      //}
     
      // lora transmit GPS data
      if(lora_idle == true)
    {
      // GPS coord string to 7 decimal points
      String latitude = String(GPS.location.lat(), 7);
      String longitude  = String(GPS.location.lng(), 7);
      
      //GPS time and date array
      //Time[] = {hr, min, sec, day, month, yr}
      int Time[6] = {GPS.time.hour(), GPS.time.minute(), GPS.time.second(), GPS.date.day(), GPS.date.month(), GPS.date.year()};
      Serial.printf("GPS time: HR:%d MIN:%d SEC:%d DAY:%d MON:%d YEAR:%d", Time[0],Time[1],Time[2],Time[3],Time[4],Time[5]);

      //GPS time to UTC (+1 second to account for delay)
      setTime(Time[0], Time[1], Time[2], Time[3], Time[4], Time[5]);
      int lastStart = cycleStartTime;
      cycleStartTime = now();

      // fix only adding 2 second btwn cycles error:
      /*
      int timeBtwnCycles = cycleStartTime - lastStart;
      if(timeBtwnCycles != cycleTime && txNumber != 0.00){
        int offset = cycleTime - timeBtwnCycles;
        Time[2] += offset;
        setTime(Time[0], Time[1], Time[2], Time[3], Time[4], Time[5]);
        cycleStartTime = now();
      }*/
      Serial.printf("Cycle Start: %d",cycleStartTime);
      
      elapsedTime = 0;
      String time_str = (String)cycleStartTime; 
      
      //delay(1000);
      txNumber += 0.01;
      sprintf(txpacket,"GPS %0.02f, %s, %s, %s \0",txNumber, time_str, latitude, longitude);  //start a package 
     
      Serial.printf("\r\nsending packet \"%s\" , length %d\r\n",txpacket, strlen(txpacket));
      Radio.Send( (uint8_t *)txpacket, strlen(txpacket) ); //send the package out 
      lora_idle = false;
    }
    Radio.IrqProcess( );
  
      
    
      // enter rx mode until elapsedTime = cycleTime
      receivedLora = false;
      while(elapsedTime < cycleTime){
        elapsedTime = now() - cycleStartTime;

        // lora receive until cycleTime
        if(lora_idle && receivedLora == false)
        {
          //buzzer while out of bounds
          if(Tracker.get_boundaryAlert() == 1){
            tone(buzzerPin, 300);
          }
          else{
            noTone(buzzerPin);
          }
          lora_idle = false;
          Serial.println("into RX mode");
          int lora_timeout = cycleTime * 1000;
          Radio.Rx(0);
        }
        Radio.IrqProcess( );
        
        // if lora received, update flags and set received to true
        // if lora not received, keep received false
          // send missed signal flag to RPI (for now this missed signal will assume that the RPI missed the GPS ping, ignoring ESP missing RPI flags)
          // loops back to sending GPS data
        }
        noTone(buzzerPin);
    }
  }
}  

void OnRxDone( uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr )
{
    rssi=rssi;
    rxSize=size;
    memcpy(rxpacket, payload, size );
    rxpacket[size]='\0';
    Radio.Sleep( );

    // Update flags each receive
    Tracker.set_flags(rxpacket);
    String message = Tracker.get_flagsStr();
    Serial.printf("\r\nreceived packet \"%s\" with rssi %d , length %d\r\n",message,rssi,rxSize);
    lora_idle = true;

    // raise received flag high
    receivedLora = true;
}

void OnTxDone( void )
{
  Serial.println("TX done......");
  lora_idle = true;
}

void OnTxTimeout( void )
{
    Radio.Sleep( );
    Serial.println("TX Timeout......");
    lora_idle = true;
}
