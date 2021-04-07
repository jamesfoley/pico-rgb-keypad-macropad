import time
import board
import digitalio
import usb_hid
import adafruit_dotstar

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Define keyboard
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# Define pixels
pixels = adafruit_dotstar.DotStar(board.GP2, board.GP3, 12, brightness=0.1, auto_write=True)

pixel_map = {
    0: 8,
    1: 4,
    2: 0,
    3: 9,
    4: 5,
    5: 1,
    6: 10,
    7: 6,
    8: 2,
    9: 11,
    10: 7,
    11: 3,
}

button_count = 12

# Button state storage
states = {
    "setup": [0] * button_count,
    "current": [0] * button_count,
    "previous": [0] * button_count,
    "toggle": [0] * button_count,
    "hold_time": [0] * button_count
}

button_gpio_map = {
    0: board.GP14,
    1: board.GP17,
    2: board.GP16,
    3: board.GP12,
    4: board.GP18,
    5: board.GP11,
    6: board.GP10,
    7: board.GP26,
    8: board.GP9,
    9: board.GP27,
    10: board.GP8,
    11: board.GP7,
}

buttons = {}

for key, value in button_gpio_map.items():
    buttons[key] = digitalio.DigitalInOut(value)
    buttons[key].switch_to_input(pull=digitalio.Pull.UP)

# Function to read button states
def button_states():
    state = [0] * button_count
    for key, value in buttons.items():
        state[key] = 0 if value.value else 1
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

# Helper function to make button programming less painful, holds information for buttons
def button_action(button, action):
    
    if button == 0:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 0, 255))
            kbd.release(Keycode.SHIFT)
            kbd.release(Keycode.W)
        elif action == "pressed":
            set_button_pixel(button, (51, 153, 255))
            kbd.press(Keycode.SHIFT)
            kbd.press(Keycode.W)

    elif button == 2:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 0, 255))
        elif action == "pressed":
            set_button_pixel(button, (255, 0, 255))
            kbd.send(Keycode.LEFT_CONTROL, Keycode.KEYPAD_PERIOD)
    
    elif button == 6:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 0, 255))
        elif action == "pressed":
            cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
            set_button_pixel(button, (51, 153, 255))

    elif button == 7:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.PLAY_PAUSE)
            set_button_pixel(button, (255, 0, 0))

    elif button == 8:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 0, 255))
        elif action == "pressed":
            cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
            set_button_pixel(button, (51, 153, 255))
    
    elif button == 9:
        if action == "setup" or action == "released":
            set_button_pixel(button, (255, 102, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.MUTE)
            set_button_pixel(button, (255, 0, 0))
    
    elif button == 10:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            set_button_pixel(button, (255, 0, 0))

    elif button == 11:
        if action == "setup" or action == "released":
            set_button_pixel(button, (0, 255, 0))
        elif action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            set_button_pixel(button, (255, 0, 0))


# Cleanly set pixel colour
def set_button_pixel(button, colour):
    pixels[pixel_map[button]] = colour

# Cleanly clear pixel colour
def clear_button_pixel(button):
    pixels[pixel_map[button]] = (0, 0, 0)
    
while True:
    # Get the state right now
    states["current"] = button_states()

    hold_buttons = [10, 11]
    toggle_buttons = [0]

    # Set up buttons
    # Probably a little overcomplicated, but allows a function to be mapped to button events
    for i in range(0, button_count):
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
    time.sleep(0.02)
