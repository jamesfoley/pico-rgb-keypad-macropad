import time
import board
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Define keyboard
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

button_count = 16

# Button state storage
states = {
    "setup": [0] * button_count,
    "current": [0] * button_count,
    "previous": [0] * button_count,
    "toggle": [0] * button_count,
    "hold_time": [0] * button_count
}

button_gpio_map = {
    0: board.SW0,
    1: board.SW4,
    2: board.SW8,
    3: board.SW12,

    4: board.SW1,
    5: board.SW5,
    6: board.SW9,
    7: board.SW13,

    8: board.SW2,
    9: board.SW6,
    10: board.SW10,
    11: board.SW14,

    12: board.SW3,
    13: board.SW7,
    14: board.SW11,
    15: board.SW15,
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
            kbd.release(Keycode.SHIFT)
            kbd.release(Keycode.W)
        elif action == "pressed":
            kbd.press(Keycode.SHIFT)
            kbd.press(Keycode.W)

    elif button == 2:
        if action == "pressed":
            kbd.send(Keycode.F14)

    elif button == 3:
        if action == "pressed":
            kbd.send(Keycode.F13)

    elif button == 4:
        if action == "pressed":
            kbd.send(Keycode.B)

    elif button == 5:
        if action == "pressed":
            kbd.send(Keycode.E)

    elif button == 9:
        if action == "pressed":
            cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)

    elif button == 10:
        if action == "pressed":
            cc.send(ConsumerControlCode.PLAY_PAUSE)

    elif button == 11:
        if action == "pressed":
            cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)

    elif button == 13:
        if action == "pressed":
            cc.send(ConsumerControlCode.MUTE)

    elif button == 14:
        if action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_DECREMENT)

    elif button == 15:
        if action == "pressed":
            cc.send(ConsumerControlCode.VOLUME_INCREMENT)


while True:
    # Get the state right now
    states["current"] = button_states()

    hold_buttons = [4, 5, 14, 15]
    hold_delays = {
        14: 0.2,
        15: 0.2
    }
    toggle_buttons = [0]

    # Set up buttons
    # Probably a little overcomplicated, but allows a function to be mapped to button events
    for i in range(0, button_count):
        handle_button(
            i,
            hold=i in hold_buttons,
            hold_delay=hold_delays[i] if i in hold_delays else 0,
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
