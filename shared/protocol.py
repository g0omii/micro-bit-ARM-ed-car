# Radio protocol definitions for micro:bit robot car
# 12-byte binary packets @ 50Hz (20ms interval)

RADIO_GROUP = 0
RADIO_CHANNEL = 7
RADIO_POWER = 7
RADIO_DATARATE = 1_000_000  # 1Mbps

MODE_CAR = 0
MODE_ARM = 1

BTN_SPIN_CCW = 0   # P12
BTN_SPIN_CW = 1    # P13
BTN_CLAW_OPEN = 2  # P14
BTN_CLAW_CLOSE = 3 # P15

PACKET_SIZE = 12

def pack_packet(mode, joy_x, joy_y, buttons, seq):
    """Pack control data into 12-byte binary packet."""
    buf = bytearray(PACKET_SIZE)
    buf[0] = (mode & 0x01) | ((buttons & 0x0F) << 1)
    buf[1] = joy_x & 0xFF
    buf[2] = joy_y & 0xFF
    buf[3] = buttons & 0xFF
    buf[4] = seq & 0xFF
    # Simple XOR checksum
    checksum = 0
    for i in range(5):
        checksum ^= buf[i]
    buf[5] = checksum
    return bytes(buf)

def unpack_packet(data):
    """Unpack 12-byte packet. Returns (mode, joy_x, joy_y, buttons, seq, valid)."""
    if len(data) < 6:
        return None
    checksum = 0
    for i in range(5):
        checksum ^= data[i]
    if checksum != data[5]:
        return None
    mode = data[0] & 0x01
    joy_x = data[1] if data[1] < 128 else data[1] - 256
    joy_y = data[2] if data[2] < 128 else data[2] - 256
    buttons = data[3]
    seq = data[4]
    return (mode, joy_x, joy_y, buttons, seq, True)