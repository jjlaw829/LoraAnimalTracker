# Script for GUI functions

import os, sys
sys.path.append('/home/ip/LoraAnimalTracker/lib/python3.11/site-packages')

import PySimpleGUI as sg

sg.theme('black')


# ** START SCREEN **

def run_start():
    def make_window_startbutton():
        layout_startbutton = [  [sg.Text(text='Current Tracker Settings:')],
                                [sg.Text(text='Setting 1')],
                                [sg.Text(text='Setting 2')],
                                [sg.Text(text='Setting 3')],
                                [sg.Text(text='Setting 4')],
                                [sg.Text(text='Setting 5')],
                                [sg.Text()],
                                [sg.VPush()],
                                [sg.Push(), sg.Text(text='PRESS BUTTON TO BEGIN', auto_size_text=True), sg.Push()],
                                [sg.Push(), sg.Button(button_text='START', key='-START-', enable_events=True), sg.Push()],
                                [sg.Push(), sg.Button(button_text='QUIT', key='-QUIT-', enable_events=True), sg.Push()],
                                [sg.VPush()],
                                [sg.VPush()], ]
        window = sg.Window('LAT Start Screen', layout_startbutton, size=(480, 800))
        return window

    window = make_window_startbutton()
    while True:
        event, values = window.read()
        if event == '-QUIT-':
            break
        elif event == '-START-':
            window = make_window_connecting()
        elif event == 'close' or event == sg.WIN_CLOSED:
            break

    window.close()


# ** CONNECTING SCREEN **

def run_connecting():
    def make_window_connecting():
        layout_connecting = [   [sg.VPush()],
                                [sg.Push(), sg.Text(text='WAITING FOR CONNECTION WITH COLLAR', key='-OUT-'), sg.Push()],
                                [sg.Push(), sg.Button(button_text='CONNECT', key='-CONNECT-', enable_events=True), sg.Push()],
                                [sg.VPush()] ]
        window = sg.Window('LAT Connecting', layout_connecting, size=(480, 800))
        return window
    
    window = make_window_connecting()
    
    while True:
        event, values = window.read()

        if event == '-CONNECT-':
            window['-OUT-'].update(value='CONNECTION ESTABLISHED')
            window['-CONNECT-'].update(visible=False)
        elif event == 'close' or event == sg.WIN_CLOSED:
            break
    
    window.close()
    
    
# ** CONTINUOUS TRACKER GPS MODE 0 **

def run_gps_mode0():
        
    sg.Window._move_all_windows=True

    # Data from tracking system
    gps_direction = 'N'
    pointer_direction = 'N'



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
                            pointer_NW = r"/home/ip/LoraAnimalTracker/pointerpointer_NW.png")


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
        layout_gps= [   [sg.Text('Elapsed Time: 5s')],
                                [sg.VPush()],
                                [sg.Push(), sg.Image(source=user_direction, key='-USER_DIRECTION-'), sg.Push()],
                                [sg.VPush()],
                                [sg.Push(), sg.Image(source=collar_direction), sg.Text('Distance: 200 ft'), sg.Push()],
                                [sg.VPush()] ]
        window = sg.Window('Background', layout_gps, size=(480, 800), no_titlebar=False, finalize=True)
        return window

    window = make_window_gps0()
    
    while True:
        event, values = window.read()
        print(event, values)
        if event is None:
            break

    window.close()



# ** CONTINUOUS TRACKER GPS MODE 1 **


def run_gps_mode1():
    # Tracker settings
    unit_length = "ft"
    max_radius = 200

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
        center_lat = 34.28
        center_lon = -84.74
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
        layout = [  [sg.Text('Elapsed Time: 5s')],   
                    [sg.Graph(canvas_size=(480, 750), graph_top_right=(top_right_lat, top_right_lon), graph_bottom_left=(bottom_left_lat, bottom_left_lon), k='graph', background_color='black', pad=(0, 0))]   ]

        # Create window for graph
        window = sg.Window('LAT BM1 Screen', layout, finalize=True, no_titlebar=False, size=(482, 800), margins=(0, 0))
        return window

    window = make_window_gps1()
    
    # Center coordinates * 10^7
    window['graph'].draw_text('Center', (center_lat, center_lon), color='white')

    # Tracker max radius scaled to unit per degree 
    window['graph'].draw_circle(center_location=(center_lat, center_lon), radius=radius, line_color='white')
    
    # collar coordinates from esp
    collar_lat = 34.2805485
    collar_lon = -84.74
    
    # Collar coordinates * 10^7
    window['graph'].draw_point(point=(collar_lat * float_as_int, collar_lon * float_as_int), color='white', size=size)


    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED:
            break
        elif event is None:
            break

    window.close()



# ** MENU SCREEN **


def run_menu(): 
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
        window = sg.Window('LAT menu screen', layout_menu, size=(480, 800))
        return window

    def make_window_sleep():
        # layout for enabling sleep mode
        layout_sleep = [    [sg.VPush()],
                            [sg.Push(), sg.Text('ENABLING SLEEP MODE'), sg.Push()],
                            [sg.VPush()]]
        window = sg.Window('Sleep Enabled', layout_sleep, size=(480, 800))
        return window

    def make_window_settings():
        # layout for settings
        layout_currentsettings = [  [sg.Text('CURRENT SETTINGS')],
                                    [sg.Text('Boundary Mode')],
                                    [sg.Text('Max Distance')],
                                    [sg.Text('Cycle Time')],
                                    [sg.Text('Length Unit')]]
                                    
        layout_settingsoption = [   [sg.VPush()],
                                    [sg.Text('WHICH SETTING WOULD YOU LIKE TO CHANGE?')],
                                    [sg.Button('Boundary Mode', k='Button1')],
                                    [sg.Button('Max Distance', k='Button2')],
                                    [sg.Button('Length Unit', k='Button3')],
                                    [sg.Button('Cycle Time', k='Button4')],
                                    [sg.Button('Return', k='Button5')],
                                    [sg.Input(default_text='', visible=False, k='input', do_not_clear=False)],
                                    [sg.Radio('0', k='0', visible=False, group_id=0, enable_events=True), sg.Radio('1', k='1', visible=False, group_id=0, enable_events=True)],
                                    [sg.Radio('ft', k='ft', visible=False, group_id=1, enable_events=True), sg.Radio('mi', k='mi', visible=False, group_id=1, enable_events=True), sg.Radio('m', k='m', visible=False, group_id=1, enable_events=True), sg.Radio('km', k='km', visible=False, group_id=1, enable_events=True)],
                                    [sg.Button('Submit', visible=False, enable_events=True)],
                                    [sg.VPush()]    ]
        layout_settings = layout_currentsettings + layout_settingsoption
        window = sg.Window('SETTINGS', layout_settings, size=(480, 800))
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
            for i in range(1,5):
                if event == f'Button{i}':
                    # Hide buttons other than pressed
                    for x in range(1,6):
                        if x != i:
                                window[f'Button{x}'].update(visible=False)
                    # Boundary Mode button
                    if i == 1:
                        for i in radios:
                            window[i].update(visible=True)
                        break
                    # Type in setting buttons
                    elif i in [2,4]:
                        window['input'].update(visible=True)
                        window['Submit'].update(visible=True)
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
                print(f'The new value is {new_value}')
                window['input'].update(visible=False)
                window['Submit'].update(visible=False)
                for i in range(1,6):
                    window[f'Button{i}'].update(visible=True)
            # If Boundary Mode radio, store option and bring back buttons
            elif event in radios:
                bm_choice = event
                for i in radios:
                    window[i].update(visible=False)
                print(f'Boundary Mode is {bm_choice}')
                for i in range(1,6):
                    window[f'Button{i}'].update(visible=True)
            # If Units radio, store option and bring back buttons 
            elif event in units:
                unit_choice = event
                for i in units:
                    window[i].update(visible=False)
                print(f'Unit for length is {unit_choice}')
                for i in range(1,6):
                    window[f'Button{i}'].update(visible=True)
            elif event == 'Button5':
                window = make_window_menu()


        if event == sg.WIN_CLOSED:
            break
        elif event == '-SLEEP-':
            window = make_window_sleep()
            current_layout = 'sleep'
            window.read(3000)
            sg.popup("System is in sleep mode. Press OK to exit")
            break

        elif event == '-SETTINGS-':
            window = make_window_settings()
            current_layout = 'settings'
        elif event == '-RETURN-':
            break

    window.close()
