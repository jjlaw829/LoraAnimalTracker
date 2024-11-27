import os, sys
from math import radians, cos, sin, asin, sqrt, atan2, degrees
from datetime import datetime, timezone
from threading import Event
import threading
sys.path.append("/home/ip/LoraAnimalTracker/lib/python3.11/site-packages/")
import LoRaTracker
from LoRaRF import SX126x
import digitalcompassTracker as compass
import RPi.GPIO as GPIO
import time
import dy880ttlTracker
import gui_scripts

# Threading event for counting seconds that still allows Interrupts
exitEvent = Event()

# Set GPIO pins for TX and RX modes on SX1262 (TX mode: RXEN LOW, TXEN HIGH; RX mode: RXEN HIGH, TXEN LOW)
GPIO.setmode(GPIO.BCM)
rxPin = 5
txPin = 6


# Switch between RX and TX modes 
def enRXMode():
    GPIO.setup(rxPin, GPIO.OUT, initial=1)
    GPIO.setup(txPin, GPIO.OUT, initial=0)
    
def enTXMode():
    GPIO.setup(rxPin, GPIO.OUT, initial=0)
    GPIO.setup(txPin, GPIO.OUT, initial=1)


# Setting up default Tracker  **Custom LoRaTracker class
Tracker = LoRaTracker.Tracker()

# Set up compass sensor
compass.initialize_sensor()

# Interrupt for enabling the user menu 
def enableMenu(channel):
    Tracker.set_enMenu(1)
    Tracker.update_flags() 
    print("\n -- MENU ENABLED - OPENING AFTER CYCLE COMPLETE -- \n")

# Sets push button on GPIO 16 to Interrupt     
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(16, GPIO.FALLING, callback=enableMenu, bouncetime=300)

# Print current settings
def currentSettings(): 
    boundaryMode = Tracker.get_boundaryMode()
    boundaryLimit = Tracker.get_boundaryLimit()
    unitLength = Tracker.get_unitLength()
    cycleTime = Tracker.get_cycleTime()
    centerLat = Tracker.get_centerLat()
    centerLon = Tracker.get_centerLon()
    
    print("\nCurrent Tracker Settings:")
    if boundaryMode == 0:
        print(f"Boundary Mode: {boundaryMode} \nMax Distance: {boundaryLimit} {unitLength} \nCycle Time: {cycleTime} seconds")
    elif boundaryMode == 1:
        print(f"Boundary Mode: {boundaryMode} \nMax Radius: {boundaryLimit} {unitLength} \nBoundary Center: {centerLat}, {centerLon} \nCycle Time: {cycleTime} seconds")

# User Menu **Finish writing menu
def userMenu():
    Tracker.set_enMenu(0)
    Tracker.update_flags()
    
    exitMenu = False
    correctOption = False
    option = ""
    option2 = ""
    option3 = ""
    value = ""
    
    #while not correctOption:
    while not exitMenu:
        print("\n -- USER MENU --")
        print("Choose an option:")
        print("1: Sleep \n2: Change Settings \n3: Return\n")
        option = input()
        
        if option == "1":
            Tracker.set_enSleep(1)
            Tracker.update_flags()
            exitMenu = True
            print("Enabling Sleep Mode")
            correctOption = True
        elif option == "2":
            correctOption = True
            changingSettings = True
            
            while changingSettings:
                currentSettings()
                print("\nWhich setting would you like to change?")
                
                if Tracker.get_boundaryMode() == 0:
                    print("1: Boundary Mode \n2: Max Distance \n3: Unit of Length \n4: Cycle Time\n5: Return")
                    option2 = input()
                    
                    if option2 == "1":
                        Tracker.set_boundaryMode(1)
                    elif option2 == "2":
                        print("Choose Max Distance: ")
                        value = input()
                        Tracker.set_boundaryLimit(float(value))
                    elif option2 == "3":
                        print("Choose a Unit (ft, mi, m, or km): ")
                        value = input()
                        Tracker.set_unitLength(str(value))
                    elif option2 == "4":
                        print("Choose Time for each GPS Cycle (seconds): ")
                        value = input()
                        Tracker.set_cycleTime(int(value))
                    elif option2 == "5":
                        changingSettings = False
                        
                elif Tracker.get_boundaryMode() == 1:
                    print("1: Boundary Mode \n2: Max Radius \n3: Unit of Length \n4: Center \n5: Cycle Time \n6: Return")
                    option2 = input()
                    
                    if option2 == "1":
                        Tracker.set_boundaryMode(0)
                    elif option2 == "2":
                        print("Choose Max Radius: ")
                        value = input()
                        Tracker.set_boundaryLimit(float(value))
                    elif option2 == "3":
                        print("Choose a Unit (ft, mi, m, or km): ")
                        value = input()
                        Tracker.set_unitLength(value)
                    elif option2 == "4":
                        print("Choose a New Center (Latitude, Longitude): ")
                        value = input()
                        center = value.split(',')
                        centerLat = float(center[0])
                        centerLon = float(center[1])
                        Tracker.set_centerLat(centerLat)
                        Tracker.set_centerLat(centerLon)
                    elif option2 == "5":
                        print("Choose Time for each GPS Cycle (seconds): ")
                        value = input()
                        Tracker.set_cycleTime(int(value))
                    elif option2 == "3":
                        changingSettings = False
                        
                print("\nWould you like to change more settings? (y/n): ")
                option3 = input()
                if option3 == "n":
                    changingSettings = False
        
        elif option == "3":
            correctOption = True
            exitMenu = True
            
            
            
    
    
# Create LoRa object
# Begin LoRa radio and set NSS, reset, busy, IRQ, txen, and rxen pin with connected Raspberry Pi gpio pins
# IRQ pin not used in this example (set to -1). Set txen and rxen pin to -1 if RF module doesn't have one
busId = 0; csId = 0
resetPin = 27; busyPin = 17; irqPin = 22; txenPin = -1; rxenPin = -1
LoRa = SX126x()

# Identify what data is sent (GPS, MSG = missed signal, CON = connected, SLP = sleeping)
def dataSent(message):
    s = message[0:3]
    return s
    
    
# Distance between coordinates (TX = 1, RX = 2)
def distance(lat1, lat2, lon1, lon2, unit = "ft"):
     
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a)) 
    
    # Radius of earth in kilometers (6371). Use 3956 for miles
    if unit == "km":
        r = 6371
    elif unit == "m":
        r = 6371 * 1000
    elif unit == "mi":
        r = 3956
    elif unit == "ft":
        r = 3956 * 5280
      
    # calculate the result
    return(c * r)
    
# Returns counter-clockwise angle between positive x-axis (North = 0) and distance vector between 2 points
def angle_between(positionRX, positionTX):
    A = positionRX
    B = positionTX
    
    rx = B[0] - A[0]
    ry = B[1] - A[1]
    angle = degrees(atan2(ry, rx))
    
    return angle % 360
        
# Lora set up
def loraSetup():
    print("Beginning LoRa radio")
    if not LoRa.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin) :
        raise Exception("Something wrong, can't begin LoRa radio")

    print("\nCurrent LoRa Parameters:")
    # Configure LoRa to use TCXO with DIO3 as control
    print("Set RF module to use TCXO as clock reference")
    LoRa.setDio3TcxoCtrl(LoRa.DIO3_OUTPUT_1_8, LoRa.TCXO_DELAY_10)

    # Set frequency to 915 Mhz
    print("Set frequency to 915 Mhz")
    LoRa.setFrequency(915000000)

    # Set TX power, default power for SX1262 and SX1268 are +22 dBm and for SX1261 is +14 dBm
    # This function will set PA config with optimal setting for requested TX power
    print("Set TX power to +17 dBm")
    LoRa.setTxPower(15, LoRa.TX_POWER_SX1262)                       # TX power +17 dBm using PA boost pin

    # Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
    # Receiver must have same SF and BW setting with transmitter to be able to receive LoRa packet
    print("Set modulation parameters:\n\tSpreading factor = 7\n\tBandwidth = 125 kHz\n\tCoding rate = 4/5")
    sf = 10                                                         # LoRa spreading factor: 7
    bw = 125000                                                     # Bandwidth: 125 kHz
    cr = 8                                                          # Coding rate: 4/5
    LoRa.setLoRaModulation(sf, bw, cr)

    # Configure packet parameter including header type, preamble length, payload length, and CRC type
    # The explicit packet includes header contain CR, number of byte, and CRC type
    # Receiver can receive packet with different CR and packet parameters in explicit header mode
    print("Set packet parameters:\n\tExplicit header type\n\tPreamble length = 12\n\tPayload Length = 15\n\tCRC on")
    headerType = LoRa.HEADER_EXPLICIT                               # Explicit header mode
    preambleLength = 8                                            # Set preamble length to 12
    payloadLength = 60                                             # Initialize payloadLength to 15
    crcType = True                                                  # Set CRC enable
    LoRa.setLoRaPacket(headerType, preambleLength, payloadLength, crcType)

    # Set syncronize word for public network (0x3444)
    print("Set syncronize word to 0x3444")
    LoRa.setSyncWord(0x12)

    # Set RX gain to power saving gain
    print("Set RX gain to power saving gain")
    LoRa.setRxGain(LoRa.RX_GAIN_BOOSTED)

    # Request for receiving new LoRa packet in RX continuous mode
    #LoRa.request(LoRa.RX_CONTINUOUS)
    
# Function to control system starting    
def systemBegin():
    print("\n  PRESS ENTER TO BEGIN TRACKING SYSTEM \n")
    begin = input()
        
# Transmitting flags to ESP and waiting for correct response before continuing
def collarConnect():
    enTXMode()
    collarConnected = False
    
    while not collarConnected:
        # Message to transmit
        Tracker.update_flags()
        flags = f"{Tracker.get_flagsStr()}"
        message = flags
        messageList = list(message)
        for i in range(len(messageList)) : messageList[i] = ord(messageList[i])
        counter = 0
        
        
        # Transmit message and counter
        # write() method must be placed between beginPacket() and endPacket()
        LoRa.beginPacket()
        LoRa.write(messageList, len(messageList))
        LoRa.write([counter], 1)
        LoRa.endPacket()

        # Print message and counter
        print(f"{message}  {counter}")

        # Wait until modulation process for transmitting packet finish
        LoRa.wait()

        # Print transmit time and data rate
        print("Transmit time: {0:0.2f} ms | Data rate: {1:0.2f} byte/s".format(LoRa.transmitTime(), LoRa.dataRate()))

        
        # Request for receiving new LoRa packet in RX continuous mode
        LoRa.request(LoRa.RX_CONTINUOUS)

        # Receive wake up message during 5 second cool down
        waitingForData = True
        txCooldown = True
        timer = 0
        enRXMode()
        
        # End loop if data received from esp or 5 second cool down expires
        while waitingForData and txCooldown:
            
            # Check for incoming LoRa packet
            if LoRa.available() :

                # Put received packet to message and counter variable
                message = ""
                while LoRa.available() > 1 :
                    message += chr(LoRa.read())
                counter = LoRa.read()
                
                # Check message type
                msgType = dataSent(message)
                # If sleep not enabled, look for connection message
                if Tracker.get_enSleep() == 0:
                    # Ignore stray receptions
                    if msgType == "CON":
                        
                        # Print received message and counter in serial
                        print(f"{message}  {counter}")
                        # Print packet/signal status including RSSI, SNR, and signalRSSI
                        print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB".format(LoRa.packetRssi(), LoRa.snr()))

                        # Show received status in case CRC or header error occur
                        status = LoRa.status()
                        if status == LoRa.STATUS_CRC_ERR : print("CRC error")
                        if status == LoRa.STATUS_HEADER_ERR : print("Packet header error")
                        
                        collarConnected = True
                        waitingForData = False
                        
                # If sleep enabled, look for sleeping message
                elif Tracker.get_enSleep() == 1:
                    # Ignore stray receptions
                    if msgType == "SLP":
                        
                        # Print received message and counter in serial
                        print(f"{message}  {counter}")
                        # Print packet/signal status including RSSI, SNR, and signalRSSI
                        print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB".format(LoRa.packetRssi(), LoRa.snr()))

                        # Show received status in case CRC or header error occur
                        status = LoRa.status()
                        if status == LoRa.STATUS_CRC_ERR : print("CRC error")
                        if status == LoRa.STATUS_HEADER_ERR : print("Packet header error")
                        
                        collarConnected = True
                        waitingForData = False                        
            
            # Timer, transmit again if loop ran for 5 seconds      
            timer += 1
            exitEvent.wait(1)
            if timer == 5:
                txCooldown = False


# Continuous Tracking loop
def continuousTracker():
    boundaryMode = Tracker.get_boundaryMode()
    boundaryLimit = Tracker.get_boundaryLimit()
    unitLength = Tracker.get_unitLength()
    centerLat = Tracker.get_centerLat()
    centerLon = Tracker.get_centerLon()
    cycleTime = Tracker.get_cycleTime()
    
    # Run loop while READY TO RECEIVE flag high
    while Tracker.get_readyRX() == 1:
        elapsedTime = 0
        dist = 0.0
        radius = 0
        
        LoRa.request(LoRa.RX_CONTINUOUS)
        print("\nWaiting for Collar GPS Ping")
        
        # Receive Data from ESP
        waitingForData = True
        enRXMode()

        while waitingForData :

            # Check for incoming LoRa packet
            if LoRa.available() :

                # Put received packet to message and counter variable
                message = ""
                while LoRa.available() > 1 :
                    message += chr(LoRa.read())
                counter = LoRa.read()
                
                msgType = dataSent(message)
                
                    
                #Check data sent 
                if msgType == "GPS":
                    # Print received message and counter in serial
                    print("Data Received:")
                    print(f"{message}  {counter}")
                    
                    # Print packet/signal status including RSSI, SNR, and signalRSSI
                    print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB\n".format(LoRa.packetRssi(), LoRa.snr()))
                    
                    waitingForData = False
                    
                    # List of ESP GPS data: Type, Time(UTC), Lat, Long
                    gpsTX = message.split(',')
                    #print(gpsTX)
                    
                    # Start cycle at time of GPS ping
                    cycleStartTime = int(gpsTX[1])   # Time(UTC)
                    latTX = float(gpsTX[2])          #0.02
                    lonTX = float(gpsTX[3])          # 0.02
                    posTX = (latTX, lonTX)
                    
                    # Get Distance or Radius depending on boundary mode
                    if boundaryMode == 0:
                        # Get RX GPS data as type dict, runs dy880ttlTracker
                        gpsRX = dy880ttlTracker.main()
                        
                        # uses .get() function for type dict
                        latRX = gpsRX.get('latitude')
                        lonRX = gpsRX.get('longitude')
                        posRX = (latRX, lonRX)
                        
                        dist = distance(latTX, latRX, lonTX, lonRX, unitLength)
                        print(f"Distance: {dist:.2f} {unitLength}")
                        
                        # Get digital compass data for user
                        compassData = compass.read()
                        heading = compassData[0]
                        userDirection = compassData[1]
                        print(f"User facing {heading:.2f} degrees ({userDirection})")
                        
                        # Get angle pointing toward collar
                        travelAngle = angle_between(posRX, posTX)
                        travelDirection = compass.get_direction(travelAngle)
                        print(f"Correct travel angle is {travelAngle:.2f} degrees ({travelDirection})") 
                        
                    # Get Radius    
                    elif boundaryMode == 1:
                        radius = distance(latTX, centerLat, lonTX, centerLon, unitLength)
                        print(f"Radius: {radius} {unitLength}")
                    
                    # Boundary Check
                    if dist > boundaryLimit or radius > boundaryLimit:
                        Tracker.set_boundaryAlert(1)
                        print("ALERT: DOG IS OUTSIDE OF BOUNDARY")
                        
                    
                        
                elif msgType == "MSG":
                    # Print received message and counter in serial
                    print(f"{message}  {counter}")
                    
                    # Print packet/signal status including RSSI, SNR, and signalRSSI
                    print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB".format(LoRa.packetRssi(), LoRa.snr()))
                    
                    waitingForData = False
                    
                    print("Signal Lost. Reconnecting...")


                # Show received status in case CRC or header error occur
                status = LoRa.status()
                if status == LoRa.STATUS_CRC_ERR : print("CRC error")
                if status == LoRa.STATUS_HEADER_ERR : print("Packet header error")


        #lora transmit
        print("\n-- Transmitting Flags Until Cycle End --\n")


        # Send flags until cycle is completed
        enTXMode()

        while elapsedTime < cycleTime :
            # Message to transmit
            Tracker.update_flags()
            flags = f"{Tracker.get_flagsStr()}"
            message = flags
            messageList = list(message)
            for i in range(len(messageList)) : messageList[i] = ord(messageList[i])
            counter = 0
        
            # Transmit message and counter
            # write() method must be placed between beginPacket() and endPacket()
            LoRa.beginPacket()
            LoRa.write(messageList, len(messageList))
            LoRa.write([counter], 1)
            LoRa.endPacket()

            # Print message and counter
            print(f"Elapsed Time: {elapsedTime} seconds\n")
            print("RRX, ENS, ENM, BA")
            print(f"{message}  {counter}")

            # Wait until modulation process for transmitting packet finish
            LoRa.wait()
            
            # Print transmit time and data rate
            print("Transmit time: {0:0.2f} ms | Data rate: {1:0.2f} byte/s\n".format(LoRa.transmitTime(), LoRa.dataRate()))
            
            # Update time while not overloading RF module
            timer = 0
            rfSleep = True
            while rfSleep:
                # Get time of cycle
                elapsedTime = int(datetime.now(timezone.utc).timestamp())- cycleStartTime
                print(f"Elapsed Time: {elapsedTime} seconds")
                
                if elapsedTime >= cycleTime:
                    break
                    
                timer += 1
                exitEvent.wait(1)
                if timer == 5:
                    rfSleep = False
            
            counter = (counter + 1) % 256


def main(args):
    # Settings
    boundaryMode = Tracker.get_boundaryMode()
    boundaryLimit = Tracker.get_boundaryLimit()
    unitLength = Tracker.get_unitLength()
    cycleTime = Tracker.get_cycleTime()
    centerLat = Tracker.get_centerLat()
    centerLon = Tracker.get_centerLon()
    
    # Flags
    flags = Tracker.get_flags()
    readyRX = flags[0]
    enSleep = flags[1]
    enMenu = flags[2]
    boundaryAlert = flags[3]
    
    
    # Setup Lora Transmission
    loraSetup()
    
    # Print current settings
    currentSettings()
    
    # Driver loop ** Needs to be gui loop that refreshes every second
    while True:
        # Open menu if enMenu flag thrown
        if Tracker.get_enMenu() == 1:
            userMenu()
        
        # Tell collar to sleep if enSleep flag thrown
        if Tracker.get_enSleep() == 1:
                collarConnect()
                exit()
        
        # wait for user start
        #* run gui_startscreen, run system begin as threading event that takes in bool instead of input, gui return bool
        systemBegin()                
        
        if Tracker.get_readyRX() == 1:        
            # Check if collar in sleep mode/ ready to transmit    
            print("\n-- Waiting for Connection with Collar --")
            collarConnect()
            print("Connection Established")
            continuousTracker()
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
