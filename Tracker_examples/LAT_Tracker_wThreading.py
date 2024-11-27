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
import PySimpleGUI as sg
import gui

# Threading event for counting seconds that still allows Interrupts
timing = Event()

# Set GPIO pins for TX and RX modes on SX1262 (TX mode: RXEN LOW, TXEN HIGH; RX mode: RXEN HIGH, TXEN LOW)
GPIO.setmode(GPIO.BCM)
rxPin = 5
txPin = 6
menu_pin = 16

# Switch between RX and TX modes 
def enRXMode():
    GPIO.setup(rxPin, GPIO.OUT, initial=1)
    GPIO.setup(txPin, GPIO.OUT, initial=0)
    
def enTXMode():
    GPIO.setup(rxPin, GPIO.OUT, initial=0)
    GPIO.setup(txPin, GPIO.OUT, initial=1)


# Setting up default Tracker  **Custom LoRaTracker class
Tracker = LoRaTracker.Tracker()

# Setting up gui screen tracking object
gui = gui.gui()

# Set up compass sensor
compass.initialize_sensor()

# Interrupt for enabling the user menu 
def enableMenu(channel):
    Tracker.set_enMenu(1)
    Tracker.update_flags() 
    print("\n -- MENU ENABLED - OPENING AFTER CYCLE COMPLETE -- \n")

# Triggers interrupt when menu_pin flipped from low to high    
GPIO.setup(menu_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(menu_pin, GPIO.RISING, callback=enableMenu, bouncetime=300)

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
    
    gui.set_currentscreen("menu")
    gui.set_done(exitMenu)

    print("In GUI Menu")
    while not gui.done():
        gui.set_currentscreen("menu")
        timing.wait(1)
        
    bm, bl, ct, ul, cla, clo = gui.new_settings()
    Tracker.set_settings(bm, bl, ct, ul, cla, clo)
    print(Tracker.get_settings())
            
            
    
    
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
    sf = 7                                                         # LoRa spreading factor: 7
    bw = 125000                                                     # Bandwidth: 125 kHz
    cr = 5                                                          # Coding rate: 4/5
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
    gui.set_currentscreen("start")
    gui.set_done(False)
    
    print("Waiting for start from gui")
    while not gui.done():
       timing.wait(1)
        
# Transmitting flags to ESP and waiting for correct response before continuing
def collarConnect():
    if gui.currentscreen() != "sleep":
        gui.set_currentscreen("connecting")
    gui.set_done(False)
    
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
                        gui.set_done(True)
                        
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
                        gui.set_done(True)
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
            timing.wait(1)
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
        d = 0.0
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
                    gui.set_done(True)
                    
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
                    
                    # Show received status in case CRC or header error occur
                    status = LoRa.status()
                    if status == LoRa.STATUS_CRC_ERR : print("CRC error")
                    if status == LoRa.STATUS_HEADER_ERR : print("Packet header error")
           
        # Analyzing data
        
        #lora transmit
        print("\n-- Transmitting Flags Until Cycle End --\n")

        # Send flags until cycle is completed
        enTXMode()
        
        rfSleep = False
        
        while elapsedTime < cycleTime and Tracker.get_readyRX() == 1: 
            # Get time of cycle
            elapsedTime = int(datetime.now(timezone.utc).timestamp())- cycleStartTime
            print(f"Elapsed Time: {elapsedTime} seconds")           
            
            # Get RX GPS data as type dict, runs dy880ttlTracker
            gpsRX = dy880ttlTracker.main()
            
            # uses .get() function for type dict
            latRX = gpsRX.get('latitude')
            lonRX = gpsRX.get('longitude')
            posRX = (latRX, lonRX)

            # Get Distance or Radius depending on boundary mode
            if boundaryMode == 0:
                gui.set_currentscreen("gps0")
                                
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
                
                gui.set_tracker_directions(userDirection, travelDirection)
                d = dist
            # Get Radius    
            elif boundaryMode == 1:
                gui.set_currentscreen("gps1")
                
                radius = distance(latTX, centerLat, lonTX, centerLon, unitLength)
                print(f"Radius: {radius} {unitLength}")
                timing.wait(0.5)
                
                gui.set_bm1_data(boundaryLimit, centerLat, centerLon, latTX, lonTX)
                d = radius
            
            gui.set_gps_data(elapsedTime, d, unitLength)
            
            # Boundary Check
            if dist > boundaryLimit or radius > boundaryLimit:
                Tracker.set_boundaryAlert(1)
                gui.set_boundary_alert(1)
                print("ALERT: DOG IS OUTSIDE OF BOUNDARY")
            else:
                Tracker.set_boundaryAlert(0)
                gui.set_boundary_alert(0)
                
            timing.wait(0.25)
                            
                        
            ## add this in later if time permits        
            # elif msgType == "MSG":
                # # Print received message and counter in serial
                # print(f"{message}  {counter}")
                
                # # Print packet/signal status including RSSI, SNR, and signalRSSI
                # print("Packet status: RSSI = {0:0.2f} dBm | SNR = {1:0.2f} dB".format(LoRa.packetRssi(), LoRa.snr()))
                
                # waitingForData = False
                
                # print("Signal Lost. Reconnecting...")

            if not rfSleep:
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
                
                # Record time of rf out
                last_transmission = datetime.now(timezone.utc).timestamp()
                rfSleep = True
                
                # Print transmit time and data rate
                print("Transmit time: {0:0.2f} ms | Data rate: {1:0.2f} byte/s\n".format(LoRa.transmitTime(), LoRa.dataRate()))
            
            # Send transmission again if been 5 seconds
            current_time = datetime.now(timezone.utc).timestamp()
            if current_time - last_transmission == 5:
                rfSleep = False
            

# Driver loop 
# Runs in one thread while the gui is in another; screen displayed based on int from this thread
def driver():
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

def background_window():
    layout_bg = [  [sg.Text(' ')]  ] 
    window = sg.Window('Background', layout_bg, size=(1000, 1000), no_titlebar=False, finalize=True, background_color='black')
    
    event, values = window.read()
    while True:
        timing.wait(1)
    window.close()
    
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
    
    # Driver loop, running tracking system
    threading.Thread(target=driver).start()
    
    # Open black background window
    ##threading.Thread(target=background_window, daemon=True).start()
    def current():
        while True:
            print(gui.currentscreen())
            timing.wait(1)
    ##threading.Thread(target=current, daemon=True).start()
    
    # GUI loop
    while True:
        # Check which screen from driver
        currentscreen = gui.currentscreen()
        
        # Handle gui menu button interrupt
        if gui.menu_button_pressed:
            # Pull menu_pin high to trigger interrupt
            GPIO.setup(menu_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            sg.popup('MENU ENABLED. OPENING AFTER CYCLE COMPLETE')
            timing.wait(0.1)
            gui.set_menu_button_pressed(False)
            GPIO.setup(menu_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        if currentscreen == "start":
            gui.run_start()
            gui.set_done(True)
            gui.set_currentscreen("none")
        elif currentscreen == "connecting":
            gui.run_connecting()
            gui.set_currentscreen("none")
        elif currentscreen == "menu":
            bm, bl, ct, ul, cla, clo = Tracker.get_settings()
            gui.set_settings(bm, bl, ct, ul, cla, clo)
            gui.run_menu()
        elif currentscreen == "sleep":
            Tracker.set_enSleep(1)
            gui.run_sleep()
            sg.popup("System is in sleep mode. Press OK to exit")
            return 0
        elif currentscreen == "gps0":
            gui.run_gps0()
            gui.set_currentscreen("none")
        elif currentscreen == "gps1":
            gui.run_gps1()
            gui.set_currentscreen("none")
        
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
