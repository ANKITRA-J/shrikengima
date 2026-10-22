# Quick Start Guide - Shrike Fi Enigma

## ✅ What's Already Done

All source code has been generated for:
- Python reference oracle
- FPGA Verilog modules (9 files)
- ESP32 firmware (13 files)
- Desktop GUI (6 Python files)
- Tests and documentation

## 🚀 Quick Commands

### 1. Verify Reference Oracle
```bash
cd /Users/aayush/Documents/shrikengima
python3 reference/enigma_ref.py
```
Expected output: `Reference checks passed for all 60 rotor orders`

### 2. Generate FPGA ROM
```bash
python3 tools/gen_fpga_files.py
```
This regenerates `fpga/rtl/rotor_rom.v` (already done, but you can re-run)

### 3. Check What Was Generated
```bash
# View project structure
tree -L 3

# Count lines of code
find fpga/rtl -name "*.v" | xargs wc -l
find firmware/enigma_shrike -name "*.cpp" -o -name "*.h" | xargs wc -l
find desktop -name "*.py" | xargs wc -l
```

## 📋 File Checklist

### FPGA RTL (fpga/rtl/) - 9 files ✅
- [x] helpers.v - Arithmetic
- [x] enigma_core.v - Cipher core
- [x] led_controller.v - LED pulse
- [x] uart_rx.v - UART receiver
- [x] uart_tx.v - UART transmitter
- [x] crc8.v - CRC calculator
- [x] packet_wrapper.v - Protocol handler
- [x] enigma_top.v - Top-level module
- [x] rotor_rom.v - Generated ROM

### ESP32 Firmware (firmware/enigma_shrike/) - 13 files ✅
- [x] enigma_shrike.ino - Main sketch
- [x] board_config.h - Pin definitions
- [x] fpga_loader.cpp/.h - FPGA loader
- [x] uart_protocol.cpp/.h - Internal UART
- [x] usb_protocol.cpp/.h - USB JSON API
- [x] plugboard.cpp/.h - Plugboard logic
- [x] selftest.cpp/.h - Hardware tests

### Desktop GUI (desktop/) - 6 files ✅
- [x] enigma_gui.py - Main app
- [x] main_window.py - GUI window
- [x] serial_manager.py - Serial comm
- [x] settings_manager.py - Settings
- [x] enigma_model.py - Data model
- [x] requirements.txt - Dependencies

## 🔨 Next Steps (When Hardware is Available)

### Step 1: Install FPGA Toolchain
- Download Renesas FPGA tools for Shrike Fi
- Open `fpga/project/` directory
- Import RTL files from `fpga/rtl/`
- Set constraints for ESP32-S3 pin mapping
- Run synthesis → place & route → bitstream generation
- Export as `FPGA_bitstream_MCU.bin`

### Step 2: Setup Arduino Environment
```bash
# Install Arduino IDE
# Add ESP32 board support: https://docs.espressif.com/projects/arduino-esp32/

# Install Shrike Fi loader library
# https://github.com/vicharak-in/shrike_arduino

# Open firmware/enigma_shrike/enigma_shrike.ino in Arduino IDE
# Select Board: "ESP32S3 Dev Module"
# Select Port: (your USB serial port)
```

### Step 3: Flash the Board
```bash
# 1. Upload FPGA bitstream to filesystem
# (Use Arduino IDE: Tools → ESP32 Sketch Data Upload)
# File: firmware/enigma_shrike/data/FPGA_bitstream_MCU.bin

# 2. Compile and upload firmware
# (Arduino IDE: Sketch → Upload)
```

### Step 4: Install Desktop GUI Dependencies
```bash
cd desktop
pip3 install -r requirements.txt
# Installs: PySide6, pyserial
```

### Step 5: Run the Application
```bash
cd desktop
python3 enigma_gui.py
```

### Step 6: Test Operation
1. Connect to serial port in GUI
2. Wait for "FPGA Ready" status
3. Keep default settings (I II III, AAA, AAA, no plugs)
4. Type: `AAAAA`
5. Click "Encrypt"
6. Expected result: `BDZGO`
7. Watch for FPGA LED blinking!
8. Paste `BDZGO` in input
9. Click "Decrypt"
10. Should get back: `AAAAA`

## 🧪 Run Tests (Software Only)

### Test Reference Oracle
```bash
python3 reference/enigma_ref.py
```

### Simulate FPGA Core (requires Icarus Verilog)
```bash
cd fpga/sim

# Install simulator if needed
# brew install icarus-verilog  (macOS)

# Run core testbench
iverilog -o enigma_core_tb.out \
  enigma_core_tb.v \
  ../rtl/enigma_core.v \
  ../rtl/rotor_rom.v \
  ../rtl/helpers.v

vvp enigma_core_tb.out

# Run LED testbench
iverilog -o led_controller_tb.out \
  led_controller_tb.v \
  ../rtl/led_controller.v

vvp led_controller_tb.out
```

## 📖 Key Files to Review

### Understand the Algorithm
- `reference/enigma_ref.py` - Clean Python implementation
- `docs/SPEC.md` - Complete specification

### Understand the FPGA
- `fpga/rtl/enigma_core.v` - Main cipher logic
- `fpga/rtl/packet_wrapper.v` - Protocol handler
- `fpga/rtl/enigma_top.v` - Pin mappings

### Understand the Firmware
- `firmware/enigma_shrike/enigma_shrike.ino` - Main flow
- `firmware/enigma_shrike/usb_protocol.cpp` - JSON API
- `firmware/enigma_shrike/uart_protocol.cpp` - FPGA communication

### Understand the GUI
- `desktop/main_window.py` - UI layout
- `desktop/serial_manager.py` - Board communication

## 🐛 Troubleshooting

### Oracle Test Fails
```bash
# Make sure you're in project root
cd /Users/aayush/Documents/shrikengima
python3 reference/enigma_ref.py
```

### GUI Won't Start
```bash
# Check Python version (need 3.8+)
python3 --version

# Reinstall dependencies
pip3 install --upgrade PySide6 pyserial
```

### Serial Port Not Found
- Check USB cable connection
- macOS: Look for `/dev/cu.usbserial-*` or `/dev/tty.usbserial-*`
- Check permissions: `ls -l /dev/cu.usb*`

### FPGA Not Ready
- Check firmware serial output for errors
- Verify FPGA bitstream was uploaded to filesystem
- Check GPIO pin connections in `board_config.h`

## 📚 Documentation

- `README.md` - Project overview
- `docs/SPEC.md` - Full technical specification
- `IMPLEMENTATION_COMPLETE.md` - Detailed implementation report
- `reports/` - Stage-by-stage results

## 🎯 Known Test Vectors

### Default Settings (I II III, AAA, AAA, no plugs)
- `AAAAA` → `BDZGO`
- `BDZGO` → `AAAAA`
- `HELLOWORLD` → `ILBDAAMTAZ`

### Double-Stepping Test (I II III, AAA rings, ADU windows)
After each letter, windows become:
1. `ADV` (right stepped)
2. `AEW` (middle and right stepped)
3. `BFX` (all three stepped - double step!)
4. `BFY` (right stepped)

## 💡 Tips

1. **The board never falls back to software** - If FPGA is unavailable, you get an error (by design)
2. **Encrypt and Decrypt are the same** - Enigma is reciprocal, just use same settings
3. **Final windows ≠ Decryption key** - To decrypt, use the same INITIAL settings
4. **Plugboard is optional** - Empty plugboard (no pairs) is valid
5. **Non-letters are preserved** - Spaces, numbers, punctuation pass through unchanged

## 🎉 Success Criteria

You'll know it's working when:
- ✅ Reference oracle prints "passed for all 60 rotor orders"
- ✅ GUI connects to board and shows "FPGA Ready"
- ✅ Typing AAAAA and clicking Encrypt gives BDZGO
- ✅ FPGA LED blinks when processing letters
- ✅ Decrypting BDZGO gives back AAAAA
- ✅ Hardware selftest passes

---

**Everything is ready! Just need the physical board and vendor tools to complete testing.**
