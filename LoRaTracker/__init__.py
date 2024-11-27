# Python class for LoRa Tracker 

# Default Tracker flags
dflt_readyRX = 1
dflt_enSleep = 0
dflt_enMenu = 0
dflt_boundaryAlert = 0

# Default Tracker settings
dflt_boundaryMode = 0
dflt_boundaryLimit = 200
dflt_cycleTime = 7
dflt_unitLength = "ft"

# Default circle area settings (KSU)
dflt_centerLat = 33.938075
dflt_centerLon = -84.519757

class Tracker(object):
    
    def __init__(self, readyRX=dflt_readyRX, enSleep=dflt_enSleep, enMenu=dflt_enMenu, boundaryAlert=dflt_boundaryAlert, boundaryMode=dflt_boundaryMode, boundaryLimit=dflt_boundaryLimit, cycleTime=dflt_cycleTime, unitLength=dflt_unitLength, centerLat=dflt_centerLat, centerLon=dflt_centerLon):
        self.readyRX = readyRX
        self.enSleep = enSleep
        self.enMenu = enMenu
        self.boundaryAlert = boundaryAlert
        self.boundaryMode = boundaryMode
        self.boundaryLimit = boundaryLimit
        self.cycleTime = cycleTime
        self.unitLength = unitLength
        
        self.centerLat = centerLat
        self.centerLon = centerLon
        
        self.flags = [self.readyRX, self.enSleep, self.enMenu, self.boundaryAlert]
        self.settings = [self.boundaryMode, self.boundaryLimit, self.cycleTime, self.unitLength, self.centerLat, self.centerLon]
        
    # FLAGS (if time permits write else statements)
    # Set/update flags 
    def update_flags(self):
        # Set readyRX to not ready when menu or sleep enabled
        if self.enSleep == 1 or self.enMenu == 1:
            self.readyRX = 0
        else:
            self.readyRX = 1
        self.flags = [self.readyRX, self.enSleep, self.enMenu, self.boundaryAlert]
    
    # Get flags as list    
    def get_flags(self):
        return self.flags
     
    # Get flags as string **added cycle time so esp knows timing loop   
    def get_flagsStr(self):
        f = f"{self.readyRX}, {self.enSleep}, {self.enMenu}, {self.boundaryAlert}, {self.cycleTime}\0"
        return f

    def set_readyRX(self, value):
        r = int(value)
        if r == 1 or r == 0:
            self.readyRX = r
    
    def get_readyRX(self):
        return self.readyRX

    def set_enSleep(self, value):
        s = int(value)
        if s == 1 or s == 0:
            self.enSleep = s
            
    def get_enSleep(self):
        return self.enSleep
            
    def set_enMenu(self, value):
        m = int(value)
        if m == 1 or m == 0:
            self.enMenu = m
            
    def get_enMenu(self):
        return self.enMenu
   
    def set_boundaryAlert(self, value):
        b = int(value)
        if b == 1 or b == 0:
            self.boundaryAlert = b
    
    # SETTINGS (if time permits write else statements)
    # set settings
    def set_settings(self, boundaryMode, boundaryLimit, cycleTime, unitLength, centerLat, centerLon):
        self.boundaryMode = boundaryMode
        self.boundaryLimit = boundaryLimit
        self.cycleTime = cycleTime
        self.unitLength = unitLength
        self.centerLat = centerLat
        self.centerLon = centerLon
        
    # update settings 
    def update_settings(self):
        self.settings = [self.boundaryMode, self.boundaryLimit, self.cycleTime, self.unitLength, self.centerLat, self.centerLon]
    
    # Return settings as list
    def get_settings(self):
        return self.boundaryMode, self.boundaryLimit, self.cycleTime, self.unitLength, self.centerLat, self.centerLon
        
    def set_boundaryMode(self, value):
        b = int(value)
        if b == 1 or b == 0:
            self.boundaryMode = b
    
    def get_boundaryMode(self):
        return self.boundaryMode
        
    def set_boundaryLimit(self, value):
        self.boundaryLimit = float(value)
        
    def get_boundaryLimit(self):
        return self.boundaryLimit
        
    def set_cycleTime(self, value):
        t = int(value)
        if t > 3:
            self.cycleTime = t
            
    def get_cycleTime(self):
        return self.cycleTime
        
    def set_unitLength(self, value):
        l = str(value)
        if l == "ft" or l == "mi" or l == "m" or l == "km":
            self.unitLength = l
            
    def get_unitLength(self):
        return self.unitLength
    
    def set_centerLat(self, value):
        self.centerLat = float(value)
    
    def get_centerLat(self):
        return self.centerLat
        
    def set_centerLon(self, value):
        self.centerLon = float(value)
        
    def get_centerLon(self):
        return self.centerLon
        

    
    
    
    
    
    
    
    
    
    
    
    
    
    
