# Remote micro:bit transmitter
# Reads joystick, buttons, sends radio packets @ 50Hz

from microbit import *
import radio
import struct
from shared.protocol import *

# ========== CONFIGURATION ==========
DEADZONE = 50
CALIBRATION_SAMPLES = 50
VIBRATE_MODE_MS = 100
VIBRATE_BUTTON_MS = 50
LOOP_MS = 20  # 50Hz
# ===================================

# Pin setup
joy_x_pin = pin1
joy_y_pin = pin2
btn_pins = [pin12, pin13, pin14, pin15]
vib_pin = pin16
mode_btn = button_b

for p in btn_pins:
    p.set_pull(pin.PULL_UP)

vib_pin.write_digital(0)

# Radio setup
radio.on()
radio.config(group=RADIO_GROUP, channel=RADIO_CHANNEL, power=RADIO_POWER, datarate=RADIO_DATARATE)

# Calibrate joystick center
print("Calibrating joystick...")
x_sum = 0
y_sum = 0
for _ in range(CALIBRATION_SAMPLES):
    x_sum += joy_x_pin.read_analog()
    y_sum += joy_y_pin.read_analog()
    sleep(2)
center_x = x_sum // CALIBRATION_SAMPLES
center_y = y_sum // CALIBRATION_SAMPLES
print("Center X:", center_x, "Y:", center_y)

# State
mode = MODE_CAR
last_mode_btn = False
mode_debounce = 0
vibrate_until = 0
seq = 0
last_loop = running_time()

def read_joystick():
    raw_x = joy_x_pin.read_analog()
    raw_y = joy_y_pin.read_analog()
    dx = raw_x - center_x
    dy = raw_y - center_y
    if abs(dx) < DEADZONE:
        dx = 0
    if abs(dy) < DEADZONE:
        dy = 0
    # Cubic curve for progressive acceleration feel
    max_val = 512 - DEADZONE
    if dx != 0:
        norm = dx / max_val
        dx = int(127 * (norm ** 3))
    if dy != 0:
        norm = dy / max_val
        dy = int(127 * (norm ** 3))
    return max(-128, min(127, dx)), max(-128, min(127, dy))

def read_buttons():
    btns = 0
    for i, p in enumerate(btn_pins):
        if p.read_digital() == 0:  # Active low
            btns |= (1 << i)
    return btns

def update_vibration():
    global vibrate_until
    now = running_time()
    if vibrate_until > now:
        vib_pin.write_digital(1)
    else:
        vib_pin.write_digital(0)

while True:
    now = running_time()
    elapsed = now - last_loop
    if elapsed < LOOP_MS:
        sleep(LOOP_MS - elapsed)
    last_loop = running_time()

    # Mode toggle (Button B) with debounce
    b_pressed = mode_btn.is_pressed()
    if b_pressed and not last_mode_btn and mode_debounce == 0:
        mode = MODE_ARM if mode == MODE_CAR else MODE_CAR
        vibrate_until = now + VIBRATE_MODE_MS
        mode_debounce = 200  # ms
    last_mode_btn = b_pressed
    if mode_debounce > 0:
        mode_debounce -= elapsed

    # Read inputs
    joy_x, joy_y = read_joystick()
    buttons = read_buttons()

    # Vibrate on button press in arm mode
    if mode == MODE_ARM and buttons:
        vibrate_until = max(vibrate_until, now + VIBRATE_BUTTON_MS)

    # Send packet
    pkt = pack_packet(mode, joy_x, joy_y, buttons, seq)
    radio.send_bytes(pkt)
    seq = (seq + 1) & 0xFF

    update_vibration()