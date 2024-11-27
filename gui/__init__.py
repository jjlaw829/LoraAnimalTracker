# Python class for gui objects

import os, sys
sys.path.append('/home/ip/LoraAnimalTracker/lib/python3.11/site-packages')
import PySimpleGUI as sg
from threading import Event

timing = Event()

sg.theme('black')

# Default screen
dflt_screen = "start"

class gui(object):
    
    def __init__(self, screen=dflt_screen):
        self.screen = screen
        self.done_task = False
        self.value = ''
        
        # Variables for gps data
        self.gps_direction = 'N'
        self.pointer_direction = 'N'
        self.elapsed_time = 0
        self.distance = 0
        self.length_unit = "ft"
        
        # for gps mode 1
        self.max_radius = 200
        self.center_lat = 34.28
        self.center_lon = -84.74
        self.collar_lat = 34.2805485
        self.collar_lon = -84.74
        
        self.boundary_alert = 0
        
        # settings from tracker object
        self.boundary_mode = self.max_radius
        self.boundary_limit = 200
        self.cycle_time = 7
        self.settings = [self.boundary_mode, self.boundary_limit, self.cycle_time, self.length_unit, self.center_lat, self.center_lon]
        
        # Bool for passing menu button interrrupt to driver
        self.menu_button_pressed = False
        
        # For buttons with typed inputs
        self.setting_changed = 0
    
    # Set current screen to be displayed: screens = [start, connecting, menu, gps0, gps1]
    def set_currentscreen(self, screen):
        self.screen= screen
    
    # Get current screen  
    def currentscreen(self):
        return self.screen
        
    # Function for tracking when current task is complete
    def set_done(self, done_task):
        self.done_task = done_task
        
    def done(self):
        return self.done_task

    # Function for getting value from GUI as a string
    def set_value(self, value):
        self.value = value
        
    def value(self):
        return self.value
   
   # Functions for setting the gps directions from the tracker
    def set_tracker_directions(self, gps, pointer):
        self.gps_direction = gps
        self.pointer_direction = pointer
        
    # Functions for setting gps data to be displayed
    def set_gps_data(self, time, distance, unit):
        self.elapsed_time = time
        self.distance = distance
        self.length_unit = unit
        
    def set_bm1_data(self, boundary_limit, center_lat, center_lon, collar_lat, collar_lon):
        self.max_radius = boundary_limit
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.collar_lat = collar_lat
        self.collar_lon = collar_lon
        
    # Set out of boundary flag for gui
    def set_boundary_alert(self, alert):
        self.boundary_alert = alert
    
    def set_menu_button_pressed(self, b):
        self.menu_button_pressed = b
    
    # Passing menu button interrupt
    def menu_button_pressed(self):
        return self.menu_button_pressed
    
    # Set settings from tracker object
    def set_settings(self, boundary_mode, boundary_limit, cycle_time, length_unit, center_lat, center_lon):
        self.boundary_mode = boundary_mode
        self.boundary_limit = boundary_limit
        self.cycle_time = cycle_time
        self.length_unit = length_unit
        self.center_lat = center_lat
        self.center_lon = center_lon
        
    # Send new settings after menu
    def new_settings(self):
        return self.boundary_mode, self.boundary_limit, self.cycle_time, self.length_unit, self.center_lat, self.center_lon
   
   
    # SCREEN SCRIPTS      
    # ** START SCREEN **

    def run_start(self):
        def make_window_startbutton():
            layout_startbutton = [  [sg.Text(text='Default Tracker Settings:')],
                                    [sg.Text(text='Tracking Mode: 0 (User-to-collar)')],
                                    [sg.Text(text='Max Distance: 200 ft')],
                                    [sg.Text(text='Cycle Time: 7s')],
                                    [sg.VPush()],
                                    [sg.Push(), sg.Text(text='PRESS BUTTON TO BEGIN', auto_size_text=True), sg.Push()],
                                    [sg.Push(), sg.Button(button_text='START', key='-START-', enable_events=True), sg.Push()],
                                    [sg.Push(), sg.Button('MENU', k='menu', enable_events=True), sg.Push()],
                                    [sg.VPush()],
                                    [sg.VPush()], ]
            window = sg.Window('LAT Start Screen', layout_startbutton, size=(480, 800), keep_on_top=True)
            return window

        window = make_window_startbutton()
        while True:
            event, values = window.read()
            if event == '-START-':
                break
            elif event == 'close' or event == sg.WIN_CLOSED:
                break
            elif event == 'menu':
                self.menu_button_pressed = True
                break

        window.close()

       
    # ** CONNECTING SCREEN **

    def run_connecting(self):
        def make_window_connecting():
            layout_connecting = [   [sg.Button(button_text='MENU', k='menu', enable_events=True)],
                                    [sg.VPush()],
                                    [sg.Push(), sg.Text(text='WAITING FOR CONNECTION WITH COLLAR', key='output'), sg.Push()],
                                    [sg.VPush()],
                                    [sg.VPush()] ]
            window = sg.Window('LAT Connecting', layout_connecting, size=(480, 800), keep_on_top=True)
            return window
        
        window = make_window_connecting()
        state = "connecting"
        while True:
            event, values = window.read(1)

            if self.done_task == True:
                if state == "connecting":
                    window['output'].update(value='CONNECTION ESTABLISHED')
                    window.refresh()
                    timing.wait(0.2)
                    
                    self.done_task = False
                    state = "waiting_gps"
                    window['output'].update(value='WAITING FOR GPS PING')
                    window.refresh()
                elif state == "waiting_gps":
                    break
            if event == 'close' or event == sg.WIN_CLOSED:
                break
            elif event == 'menu':
                self.menu_button_pressed = True
                break
        
        window.close()
        
        
    # ** CONTINUOUS TRACKER GPS MODE 0 **

    def run_gps0(self):
            
        sg.Window._move_all_windows=True

        # Data from tracking system
        gps_direction = self.gps_direction
        pointer_direction = self.pointer_direction
        elapsed_time = self.elapsed_time
        distance = self.distance
        length_unit = self.length_unit



        #images
        gps_images = dict(  GPS_N = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_N.png",
                            GPS_NE = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_NE.png",
                            GPS_E = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_E.png",
                            GPS_SE = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_SE.png",
                            GPS_S = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_S.png",
                            GPS_SW = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_SW.png",
                            GPS_W = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_W.png",
                            GPS_NW = r"/home/ip/LoraAnimalTracker/gps_bm0/gps_bm0_NW.png")

        pointer_images = dict(  pointer_N = r"/home/ip/LoraAnimalTracker/pointer/pointer_N.png",
                                pointer_NE = r"/home/ip/LoraAnimalTracker/pointer/pointer_NE.png",
                                pointer_E = r"/home/ip/LoraAnimalTracker/pointer/pointer_E.png",
                                pointer_SE = r"/home/ip/LoraAnimalTracker/pointer/pointer_SE.png",
                                pointer_S = r"/home/ip/LoraAnimalTracker/pointer/pointer_S.png",
                                pointer_SW = r"/home/ip/LoraAnimalTracker/pointer/pointer_SW.png",
                                pointer_W = r"/home/ip/LoraAnimalTracker/pointer/pointer_W.png",
                                pointer_NW = r"/home/ip/LoraAnimalTracker/pointer/pointer_NW.png")


        # Algorithm that matches travel pointer direction to new orientation of gps direction
        def rotate_pointer(gps_direction, pointer_direction):
            # Define the compass directions as a list for easy index mapping
            directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
            
            # Find the indices of gps_direction and pointer_direction
            gps_index = directions.index(gps_direction)
            pointer_index = directions.index(pointer_direction)

            # Calculate the difference in indices (i.e., rotation offset)
            rotation_offset = gps_index

            # Adjust the pointer's index by applying the same rotation offset
            new_pointer_index = (pointer_index - rotation_offset) % len(directions)

            # Return the new direction of the pointer
            return directions[new_pointer_index]


        rotated_pointer = rotate_pointer(gps_direction, pointer_direction)
        print(f"With GPS direction '{gps_direction}' and pointer direction '{pointer_direction}', the rotated pointer direction is '{rotated_pointer}'.")


        user_direction = gps_images.get('GPS_' + gps_direction)
        collar_direction = pointer_images.get('pointer_' + rotated_pointer)
        
        def make_window_gps0():
            # layout for background image with user icon and compass
            layout_gps= [   [sg.Button(button_text='MENU', k='menu', enable_events=True), sg.Text(f'Elapsed Time: {elapsed_time}s', k='time')],
                            [sg.VPush()],
                            [sg.Push(), sg.Image(source=user_direction, key='user_direction'), sg.Push()],
                            [sg.VPush()],
                            [sg.Push(), sg.Image(source=collar_direction, k='collar_direction'), sg.Push()],
                            [sg.Push(), sg.Text(f'Distance: {distance} {length_unit}', k='distance'), sg.Push()],
                            [sg.VPush()],
                            [sg.Text('** ALERT: DOG IS OUT OF BOUNDARY **', k='alert', visible=False)]   ]
            window = sg.Window('Background', layout_gps, size=(480, 800), no_titlebar=False, finalize=True)
            return window

        window = make_window_gps0()
        
        while True:
            event, values = window.read(timeout=500)
            
            window['time'].update(value=f'Elapsed Time: {self.elapsed_time}s')
            window['distance'].update(value=f'Distance: {self.distance} {self.length_unit}')
            window['user_direction'].update(source=gps_images.get('GPS_' + self.gps_direction))
            window['collar_direction'].update(source=pointer_images.get('pointer_' + rotate_pointer(self.gps_direction, self.pointer_direction)))
            
            if self.boundary_alert == 1:
                window['alert'].update(visible=True)
            else:
                window['alert'].update(visible=False)
                
            if event is None:
                break
            elif event == sg.WIN_CLOSED:
                break
            elif event == 'menu':
                self.menu_button_pressed = True
                break

        window.close()



    # ** CONTINUOUS TRACKER GPS MODE 1 **


    def run_gps1(self):
        # Tracker settings
        unit_length = self.length_unit
        max_radius = self.max_radius
        elapsed_time = self.elapsed_time

        # PySimpleGUI takes ints for custom coordinates, get int precision by changing decimal by 10^7
        float_as_int = 10000000

        # Converting between tracker length unit to decimal degrees
        def unit_to_deg(u):
            conversion = 0
            unit = str(u)
            conv = dict(ft_per_deg = 364000,
                        mi_per_deg = 69,
                        km_per_deg = 111,
                        m_per_deg=111000)

            units = list(conv.keys())
            for x in units:
                if unit in x:
                    conversion = conv.get(f'{x}')

            return conversion

        # Get the number of degrees per pixel (max radius in tracker units = screen width / 2 pixels)
        def scale_factor(width, per_deg):
            r = max_radius
            sf = r / ((width / 2) * per_deg)
            return sf

        #*** needs a function for adaptive scaling based on tracker settings
        def scale():
            per_deg = unit_to_deg(unit_length)

            # Given center point and graph size
            center_lat = self.center_lat
            center_lon = self.center_lon
            width = 480
            height = 750

            # Assuming scale factors (degrees per pixel) for latitude and longitude
            sf = scale_factor(width, per_deg)
            lat_scale_factor = sf  # Change as needed for correct scale
            lon_scale_factor = sf  # Change as needed for correct scale

            # Calculate top-right (lat, lon) coordinates
            top_right_lat = int((center_lat + (width / 2) * lat_scale_factor) * float_as_int)  # Top is above the center
            top_right_lon = int((center_lon + (height / 2) * lon_scale_factor) * float_as_int)  # Right is to the east of center

            # Calculate bottom-left (lat, lon) coordinates
            bottom_left_lat = int((center_lat - (width / 2) * lat_scale_factor) * float_as_int)   # Bottom is below the center
            bottom_left_lon = int((center_lon - (height / 2) * lon_scale_factor) * float_as_int) # Left is to the west of center

            print("Top-right coordinates: ({}, {})".format(top_right_lat, top_right_lon))
            print("Bottom-left coordinates: ({}, {})".format(bottom_left_lat, bottom_left_lon))

            # Int precision for center coordinates
            center_lat *= float_as_int
            center_lon *= float_as_int

            # Scale radius
            r = width / 2
            radius = r * sf * float_as_int

            # Scale dot size
            s = 20
            size = s * sf * float_as_int
            return (top_right_lat, top_right_lon, bottom_left_lat, bottom_left_lon, center_lat, center_lon, radius, size)

        # Get scaled values
        top_right_lat, top_right_lon, bottom_left_lat, bottom_left_lon, center_lat, center_lon, radius, size  = scale()
        
        def make_window_gps1():
            # Create graph the size of window, with top right and bottom left putting the User's Center at the center
            layout = [  [sg.Button(button_text='MENU', k='menu', enable_events=True), sg.Text(f'Elapsed Time: {elapsed_time}s', k='time'), sg.Push(), sg.Text('** ALERT: DOG IS OUT OF BOUNDARY **', k='alert', visible=False), sg.Push()],   
                        [sg.Graph(canvas_size=(480, 750), graph_top_right=(top_right_lat, top_right_lon), graph_bottom_left=(bottom_left_lat, bottom_left_lon), k='graph', background_color='black', pad=(0, 0))],
                        [sg.Push(), sg.Text(f'Distance: {self.distance} {self.length_unit}', k='distance'), sg.Push()]  ]

            # Create window for graph
            window = sg.Window('LAT BM1 Screen', layout, finalize=True, no_titlebar=False, size=(482, 800), margins=(0, 0), keep_on_top=True)
            return window

        window = make_window_gps1()
        
        # Center coordinates * 10^7
        window['graph'].draw_text(f'Center: {center_lat, center_lon}', (center_lat, center_lon), color='white')

        # Tracker max radius scaled to unit per degree 
        window['graph'].draw_circle(center_location=(center_lat, center_lon), radius=radius, line_color='white')


        while True:
            # collar coordinates from esp
            collar_lat = self.collar_lat
            collar_lon = self.collar_lon
            distance = self.distance
            
            # Collar coordinates * 10^7
            window['graph'].draw_point(point=(collar_lat * float_as_int, collar_lon * float_as_int), color='white', size=size)
            
            event, values = window.read(500)
            if event == sg.WIN_CLOSED:
                break
            elif event is None:
                break
            elif event == 'menu':
                self.menu_button_pressed = True
                break
           
            # Alert if out of boundary
            if self.boundary_alert == 1:
                window['alert'].update(visible=True)
            else:
                window['alert'].update(visible=False)
                    
            window['graph'].erase()
            # Center coordinates * 10^7
            window['graph'].draw_text(f'Center', (center_lat, center_lon), color='white')
            # Tracker max radius scaled to unit per degree 
            window['graph'].draw_circle(center_location=(center_lat, center_lon), radius=radius, line_color='white')
            window['time'].update(value=f'Elapsed Time: {self.elapsed_time}s')
            window['distance'].update(value=f'Distance: {self.distance} {self.length_unit}')

        window.close()



    # ** MENU SCREEN **


    def run_menu(self): 
        def make_window_menu():
            # layout for menu options
            layout_menu = [ [sg.Push(), sg.Text('USER MENU'), sg.Push()],
                            [sg.VPush()],
                            [sg.Push(), sg.Text('CHOOSE AN OPTION'), sg.Push()],
                            [sg.Push(), sg.Button('Sleep', k='-SLEEP-', enable_events=True), sg.Push()],
                            [sg.Push(), sg.Button('Change Settings', k='-SETTINGS-', enable_events=True), sg.Push()],
                            [sg.Push(), sg.Button('Return', k='-RETURN-', enable_events=True), sg.Push()],
                            [sg.VPush()],
                            [sg.VPush()]    ]
            window = sg.Window('LAT menu screen', layout_menu, size=(480, 800), keep_on_top=True)
            return window


        def make_window_settings():
            # layout for settings
            layout_currentsettings = [  [sg.Text('CURRENT SETTINGS')],
                                        [sg.Text(f'Boundary Mode: {self.boundary_mode}', k='bm')],
                                        [sg.Text(f'Max Distance/Radius: {self.boundary_limit}', k='bl')],
                                        [sg.Text(f'Cycle Time: {self.cycle_time}s', k='ct')],
                                        [sg.Text(f'Length Unit: {self.length_unit}', k='ul')],
                                        [sg.Text(f'Center Coordinates: {self.center_lat}, {self.center_lon}', k='center')]    ]
                                        
            layout_settingsoption = [   [sg.VPush()],
                                        [sg.Text('WHICH SETTING WOULD YOU LIKE TO CHANGE?')],
                                        [sg.Button('Boundary Mode', k='Button1')],
                                        [sg.Button('Max Distance', k='Button2')],
                                        [sg.Button('Length Unit', k='Button3')],
                                        [sg.Button('Cycle Time', k='Button4')],
                                        [sg.Button('Center Coordinates', k='Button5')],
                                        [sg.Button('Return', k='Button6')],
                                        [sg.Input(default_text='', visible=False, k='input', do_not_clear=False)],
                                        [sg.Radio('0', k='0', visible=False, group_id=0, enable_events=True), sg.Radio('1', k='1', visible=False, group_id=0, enable_events=True)],
                                        [sg.Radio('ft', k='ft', visible=False, group_id=1, enable_events=True), sg.Radio('mi', k='mi', visible=False, group_id=1, enable_events=True), sg.Radio('m', k='m', visible=False, group_id=1, enable_events=True), sg.Radio('km', k='km', visible=False, group_id=1, enable_events=True)],
                                        [sg.Button('Submit', visible=False, enable_events=True)],
                                        [sg.VPush()]    ]
            layout_settings = layout_currentsettings + layout_settingsoption
            window = sg.Window('SETTINGS', layout_settings, size=(480, 800), keep_on_top=True, finalize=True)
            return window

        window = make_window_menu()
        layout = [[]]
        current_layout = 'menu'
        while True:
            event, values = window.read()
            radios = ['0', '1']
            units = ['ft', 'mi', 'm', 'km']
            
            if current_layout == 'settings':
                # Detect if one of buttons pressed
                for i in range(1,6):
                    if event == f'Button{i}':
                        # Hide buttons other than pressed
                        for x in range(1,7):
                            if x != i:
                                    window[f'Button{x}'].update(visible=False)
                        # Boundary Mode button
                        if i == 1:
                            for i in radios:
                                window[i].update(visible=True)
                            break
                        # Type in setting buttons
                        elif i in [2,4,5]:
                            window['input'].update(visible=True)
                            window['Submit'].update(visible=True)
                            self.setting_changed = i
                            break
                        # Unit button
                        elif i == 3:
                            for i in units:
                                window[i].update(visible=True)
                            break
                # If Submit pressed, store value entered and bring back option buttons
                if event == 'Submit':
                    window['input'].update(value=values['input'])
                    new_value = values['input']
                    
                    if self.setting_changed == 2:
                        self.boundary_limit = int(new_value)
                        print(f'The new Boundary Limit is {new_value} {self.length_unit}')
                    elif self.setting_changed == 4:
                        self.cycle_time = int(new_value)
                        print(f'The new Cycle Time is {new_value} seconds')
                    elif self.setting_changed == 5:
                        center = str(new_value).split(',')
                        self.center_lat = float(center[0])
                        self.center_lon = float(center[1])
                        print(f'The new center point is ({float(center[0])}, {float(center[1])})')
                    
                    window['input'].update(visible=False)
                    window['Submit'].update(visible=False)
                    for i in range(1,7):
                        window[f'Button{i}'].update(visible=True)
                # If Boundary Mode radio, store option and bring back buttons
                elif event in radios:
                    bm_choice = event
                    self.boundary_mode = int(bm_choice)
                    for i in radios:
                        window[i].update(visible=False)
                    print(f'Boundary Mode is {bm_choice}')
                    for i in range(1,7):
                        window[f'Button{i}'].update(visible=True)
                # If Units radio, store option and bring back buttons 
                elif event in units:
                    unit_choice = event
                    self.length_unit = unit_choice
                    for i in units:
                        window[i].update(visible=False)
                    print(f'Unit for length is {unit_choice}')
                    for i in range(1,7):
                        window[f'Button{i}'].update(visible=True)
                elif event == 'Button6':
                    window.close()
                    window = make_window_menu()
                    current_layout = "menu"
                
                if current_layout == "settings":
                    window['bm'].update(value=f'Boundary Mode: {self.boundary_mode}')
                    window['bl'].update(value=f'Max Distance/Radius: {self.boundary_limit}')
                    window['ct'].update(value=f'Cycle Time: {self.cycle_time}s')
                    window['ul'].update(value=f'Length Unit: {self.length_unit}')
                    window['center'].update(value=f'Center Coordinates: {self.center_lat}, {self.center_lon}')

            if event == sg.WIN_CLOSED:
                break
            elif event == '-SLEEP-':
                self.screen = "sleep"
                current_layout = 'sleep'
                self.done_task = True
                break

            elif event == '-SETTINGS-':
                window.close()
                window = make_window_settings()
                current_layout = 'settings'
            elif event == '-RETURN-':
                self.done_task = True
                self.screen = "none"
                break
    
        window.close()


    def run_sleep(self):
        def make_window_sleep():
            # layout for enabling sleep mode
            layout_sleep = [    [sg.VPush()],
                                [sg.Push(), sg.Text('ENABLING SLEEP MODE'), sg.Push()],
                                [sg.VPush()]]
            window = sg.Window('Sleep Enabled', layout_sleep, size=(480, 800), keep_on_top=True)
            return window
            
        window = make_window_sleep()
        while True:
            event, values = window.read(500)
            
            if self.done_task:
                break
            
            if event == sg.WIN_CLOSED:
                break
                
        window.close()
