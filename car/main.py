# Car micro:bit receiver
# Receives radio packets, controls 4 wheel servos + 4 arm servos

from microbit import *
import radio
from shared.protocol import *

# ========== CONFIGURATION ==========
# Arm speeds (degrees per second at full joystick deflection)
ARM_BASE_SPEED = 45
ARM_PIVOT1_SPEED = 45
ARM_PIVOT2_SPEED = 30
ARM_CLAW_SPEED = 60

# Claw servo range
CLAW_MIN_ANGLE = 30
CLAW_MAX_ANGLE = 150

# Failsafe
FAILSAFE_MS = 100

# Servo PWM values (0-1023 scale, 20ms period)
WHEEL_STOP = 75      # 1.5ms
WHEEL_MIN = 50       # 1.0ms full reverse
WHEEL_MAX = 100      # 2.0ms full forward

ARM_MIN_PWM = 26     # 0.5ms = 0 deg
ARM_MAX_PWM = 128    # 2.5ms = 180 deg
ARM_MID_PWM = 77     # 1.5ms = 90 deg

LOOP_MS = 20  # 50Hz
# ===================================

# Pin setup - Wheels (360 servos)
wheel_pins = [pin0, pin1, pin2, pin8]  # FL, FR, RL, RR
for p in wheel_pins:
    p.set_analog_period(20)
    p.write_analog(WHEEL_STOP)

# Pin setup - Arm (180 servos)
arm_pins = [pin11, pin12, pin13, pin14]  # Base, Pivot1, Pivot2, Claws
for p in arm_pins:
    p.set_analog_period(20)
    p.write_analog(ARM_MID_PWM)

# Radio setup
radio.on()
radio.config(group=RADIO_GROUP, channel=RADIO_CHANNEL, power=RADIO_POWER, datarate=RADIO_DATARATE)

# Arm positions (degrees)
base_pos = 90.0
pivot1_pos = 90.0
pivot2_pos = 90.0
claw_pos = 90.0

# State
last_packet_time = 0
mode = MODE_CAR
dt = LOOP_MS / 1000.0
last_loop = running_time()

def angle_to_pwm(angle):
    return int(ARM_MIN_PWM + (angle / 180.0) * (ARM_MAX_PWM - ARM_MIN_PWM))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def map_wheel(v):
    """Map -1.0..1.0 to PWM 50..100"""
    return int(WHEEL_STOP + 25 * v)

def update_arm():
    global base_pos, pivot1_pos, pivot2_pos, claw_pos
    # Rate control from joystick (cubic for precision at center)
    rate_x = (joy_x / 128.0) ** 3 * ARM_BASE_SPEED
    rate_y = (joy_y / 128.0) ** 3 * ARM_PIVOT1_SPEED
    base_pos += rate_x * dt
    pivot1_pos += rate_y * dt

    # Buttons for pivot2 and claws
    if buttons & (1 << BTN_SPIN_CCW):  # P12
        pivot2_pos -= ARM_PIVOT2_SPEED * dt
    if buttons & (1 << BTN_SPIN_CW):   # P13
        pivot2_pos += ARM_PIVOT2_SPEED * dt
    if buttons & (1 << BTN_CLAW_OPEN):  # P14
        claw_pos += ARM_CLAW_SPEED * dt
    if buttons & (1 << BTN_CLAW_CLOSE): # P15
        claw_pos -= ARM_CLAW_SPEED * dt

    # Clamp
    base_pos = clamp(base_pos, 0, 180)
    pivot1_pos = clamp(pivot1_pos, 0, 180)
    pivot2_pos = clamp(pivot2_pos, 0, 180)
    claw_pos = clamp(claw_pos, CLAW_MIN_ANGLE, CLAW_MAX_ANGLE)

    # Write servos
    arm_pins[0].write_analog(angle_to_pwm(base_pos))
    arm_pins[1].write_analog(angle_to_pwm(pivot1_pos))
    arm_pins[2].write_analog(angle_to_pwm(pivot2_pos))
    arm_pins[3].write_analog(angle_to_pwm(claw_pos))

def update_car():
    # Mecanum mixing for X-layout: FL, FR, RL, RR
    x = joy_x / 128.0
    y = -joy_y / 128.0  # Invert: forward = positive Y
    r = 0.0
    if buttons & (1 << BTN_SPIN_CCW):
        r -= 1.0
    if buttons & (1 << BTN_SPIN_CW):
        r += 1.0

    fl =  y + x + r
    fr =  y - x - r
    rl =  y - x + r
    rr =  y + x - r

    # Normalize
    max_val = max(abs(fl), abs(fr), abs(rl), abs(rr), 1.0)
    fl /= max_val
    fr /= max_val
    rl /= max_val
    rr /= max_val

    wheel_pins[0].write_analog(map_wheel(fl))
    wheel_pins[1].write_analog(map_wheel(fr))
    wheel_pins[2].write_analog(map_wheel(rl))
    wheel_pins[3].write_analog(map_wheel(rr))

def stop_wheels():
    for p in wheel_pins:
        p.write_analog(WHEEL_STOP)

while True:
    now = running_time()
    elapsed = now - last_loop
    if elapsed < LOOP_MS:
        sleep(LOOP_MS - elapsed)
    last_loop = running_time()

    # Receive packet
    pkt = radio.receive_bytes()
    if pkt:
        result = unpack_packet(pkt)
        if result:
            mode, joy_x, joy_y, buttons, seq, valid = result
            last_packet_time = now

            if mode == MODE_CAR:
                update_car()
            else:
                update_arm()

    # Failsafe
    if now - last_packet_time > FAILSAFE_MS:
        stop_wheels()
        # Arm holds position (no update)