# micro-bit-ARM-ed-car
Code for a radio controlled microbit vehicle equipped with an arm
#

#
Upload Options for micro:bit V2
Option 1: Web Editor (Easiest, No Install)
1. Go to https://python.microbit.org/
2. Click the gear icon → "Add file" → upload shared/protocol.py
3. Paste remote/main.py into the main editor
4. Connect remote micro:bit via USB
5. Click Flash (uses WebUSB) or Download → drag .hex to MICROBIT drive
6. Repeat for car: paste car/main.py + shared/protocol.py, flash to car micro:bit
Option 2: mu Editor (Desktop App)
# Install on Windows
winget install mu-editor
# Or download from https://codewith.mu/
1. Open mu → select "BBC micro:bit" mode
2. Create protocol.py in mu's file panel (drag from your project)
3. Paste main.py code, click Flash
Option 3: Command Line (uf2utils)
# Install
pip install uf2utils

# Compile + flash (requires micro:bit connected)
uf2conv.py -c -o remote.hex remote/main.py
uf2conv.py -c -o car.hex car/main.py

# Copy to micro:bit (appears as USB drive)
cp remote.hex /media/$USER/MICROBIT/
cp car.hex /media/$USER/MICROBIT/
Option 4: Direct .hex Drag-Drop (Simplest)
1. Use web editor to generate .hex files for each
2. Connect micro:bit → appears as MICROBIT drive
3. Drag .hex file onto the drive → auto-flashes
Important Notes
- Both micro:bits need shared/protocol.py - either upload it as a separate file (web editor/mu) or copy its contents into the top of each main.py
- Power separately - servos need external power, not USB
- Remote first - power on remote, then car (so car catches packets immediately)
Quick Test After Flashing
1. Remote: Shows "Calibrating joystick..." on LED matrix
2. Car: Wheels stay still until remote sends data
3. Move joystick → car moves
4. Press Button B on remote → vibration + mode switch
5. In arm mode: joystick moves base/pivot1, buttons move pivot2/claws
