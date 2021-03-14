import time
import board
import busio
import digitalio
import usb_hid
import adafruit_dotstar

from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

from digitalio import DigitalInOut, Direction, Pull
cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0

# Define keyboard
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# Define i2c device
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)

# Define pixels
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, 16, brightness=0.1, auto_write=True)

# Button state storage
states = {
    "setup": [0] * 16,
    "current": [0] * 16,
    "previous": [0] * 16,
    "toggle": [0] * 16,
    "hold_time": [0] * 16
}

# Function to read button states
def button_states():
    state = [0] * 16
    with device:
        device.write(bytes([0x0]))
        result = bytearray(2)
        device.readinto(result)
        b = result[0] | result[1] << 8
        for i in range(0, 16):
            if not (1 << i) & b:
                state[i] = 1
            else:
                state[i] = 0
    return state

# Function to handle button events
# toggle: True or False, turns the button into a toggle on / off, will run pressed when on, and released when off
# hold: True or False, repeatedly runs the pressed function when held down, and runs released when released
# hold_delay: seconds, time between executions of the pressed function when held
# setup: func, runs when button is initialised, useful for setting a default colour on boot
# pressed: func, runs when pressed unless an above modifier changes functionality
# released: func, runs when released unless an above modifier changes functionality
def handle_button(button, toggle=False, hold=False, hold_delay=0, setup=None, pressed=None, released=None, tick=None):
    if states["setup"][button] == 0:
        states["setup"][button] = 1
        if setup:
            setup()

    if hold and states["current"][button] == 1:
        if pressed:
            now = time.monotonic()
            if now - states["hold_time"][button] > hold_delay:
                pressed()
                states["hold_time"][button] = now

    elif states["previous"][button] == 0 and states["current"][button] == 1:
        if toggle and states["toggle"][button] == 0:
            states["toggle"][button] = 1
            if pressed:
                pressed()
        elif toggle and states["toggle"][button] == 1:
            states["toggle"][button] = 0
            if released:
                released()
        else:
            if pressed:
                pressed()
                
    elif states["previous"][button] == 1 and states["current"][button] == 0:
        if not toggle:
            if released:
                released()
        if hold:
            states["hold_time"][button] = 0
            
    if tick:
        tick()

# Cleanly set pixel colour
def set_pixel(pixel, colour):
    pixels[pixel] = colour

# Cleanly clear pixel colour
def clear_pixel(pixel):
    pixels[pixel] = (0, 0, 0)

# Color wheel function lifted from adafruit_dotstar example
def colorwheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

# Example flash handler for button 11
# Garbage function just to demo flashing a button
flash_time = 0
flash_delay = 0.5
flash_on = 0
def flash_button_example():
    now = time.monotonic()
    global flash_time
    global flash_on
        
    if now - flash_time > flash_delay:
        if flash_on == 0:
            set_pixel(11, (255, 0, 255))
            flash_on = 1
        else:
            set_pixel(11, (0, 0, 0))
            flash_on = 0
        
        flash_time = now

# Example rainbow handler for button 11
# Garbage function just to demo cycling a button through a rainbow
rainbow_time = 0
rainbow_delay = 0
rainbow_pos = 0
def rainbow_button_example():
    now = time.monotonic()
    global rainbow_time
    global rainbow_pos
    
    if now - rainbow_time > rainbow_delay:
        set_pixel(11, colorwheel(rainbow_pos))
        rainbow_pos = (rainbow_pos + 2) if rainbow_pos < 253 else 0
        
        rainbow_time = now

# Helper function to make button programming less painful, holds information for buttons
def button_action(button, action):
    if button == 1:
        if action == "setup" or action == "released":
            set_pixel(button, (255, 102, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.MUTE)
            set_pixel(button, (255, 0, 0))

    if button == 2:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            set_pixel(button, (255, 0, 0))

    elif button == 3:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            set_pixel(button, (255, 0, 0))

    elif button == 4:
        if action == "setup" or action == "released":
            set_pixel(button, (255, 0, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.STOP)
            set_pixel(button, (255, 255, 0))

    elif button == 5:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 0, 255))
        elif action == "pressed":
            cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
            set_pixel(button, (51, 153, 255))

    elif button == 6:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.PLAY_PAUSE)
            set_pixel(button, (255, 0, 0))

    elif button == 7:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 0, 255))
        elif action == "pressed":
            cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
            set_pixel(button, (51, 153, 255))
            
    elif button == 11:
        if action == "tick":
            if states["current"][11] == 0:
                flash_button_example()
            else:
                rainbow_button_example()

    elif button == 12:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 0, 255))
            kbd.release(Keycode.SHIFT)
        elif action == "pressed":
            set_pixel(button, (51, 153, 255))
            kbd.press(Keycode.SHIFT)

    elif button == 15:
        if action == "setup" or action == "released":
            set_pixel(button, (0, 0, 255))
        elif action == "pressed":
            set_pixel(button, (255, 0, 255))
            kbd.send(Keycode.LEFT_CONTROL, Keycode.KEYPAD_PERIOD)

while True:
    # Get the state right now
    states["current"] = button_states()
    
    hold_buttons = [2, 3, 11]
    toggle_buttons = [12]  

    # Set up buttons
    # Probably a little overcomplicated, but allows a function to be mapped to button events
    for i in range(0, 16):
        handle_button(
            i,
            hold=i in hold_buttons,
            hold_delay=0.2 if i in hold_buttons else 0,
            toggle=i in toggle_buttons,
            setup=lambda: button_action(i, "setup"),
            pressed=lambda: button_action(i, "pressed"),
            released=lambda: button_action(i, "released"),
            tick=lambda: button_action(i, "tick")
        )

    # Store the state as previous ready for next loop
    states["previous"] = states["current"]

    # Prevent rapid double hits from quick presses
    time.sleep(0.02).
