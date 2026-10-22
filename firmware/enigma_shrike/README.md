# Shrike Fi Enigma - ESP32-S3 Firmware

## Overview

This firmware runs on the ESP32-S3 microcontroller on the Shrike Fi board. It handles:
- FPGA bitstream loading
- UART protocol communication with FPGA
- Plugboard letter substitution
- USB serial interface to desktop GUI
- Hardware selftest with known vectors

## Hardware Requirements

- **Board**: Shrike Fi with ESP32-S3
- **FPGA**: Renesas FPGA with Enigma core (from Stage 3)
- **Connections**:
  - GPIO11 (RX) ← FPGA Pin 6 (TX)
  - GPIO13 (TX) → FPGA Pin 5 (RX)
  - USB: Host computer connection

## Software Requirements

### Arduino IDE

- **Version**: 2.x or later
- **Board Package**: ESP32 by Espressif Systems (v2.0.0+)
- **Libraries**:
  - ArduinoJson (v6.21.0+)
  - Arduino FPGA (pending ESP32-S3 support verification)
  - SPIFFS (included with ESP32 package)

### Installation

1. **Install Arduino IDE**
   ```bash
   # Download from https://www.arduino.cc/en/software
   ```

2. **Add ESP32 Board Support**
   - File → Preferences
   - Add to "Additional Board Manager URLs":
     ```
     https://espressif.github.io/arduino-esp32/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager
   - Search for "ESP32" and install

3. **Install Libraries**
   - Tools → Manage Libraries
   - Search and install:
     - ArduinoJson by Benoit Blanchon
   - Arduino FPGA library: **verify ESP32-S3 support before using**

## Building

### Arduino IDE

1. Open `enigma_shrike.ino`
2. Select board:
   - Tools → Board → ESP32 Arduino → ESP32S3 Dev Module
3. Configure settings:
   - Upload Speed: 921600
   - Flash Size: (auto-detected or match your board)
   - Partition Scheme: Default 4MB with spiffs
   - Core Debug Level: None (or "Info" for debugging)
4. Sketch → Verify/Compile

### Arduino CLI (Alternative)

```bash
# Compile
arduino-cli compile --fqbn esp32:esp32:esp32s3 firmware/enigma_shrike

# Upload
arduino-cli upload -p /dev/cu.usbserial-* --fqbn esp32:esp32:esp32s3 firmware/enigma_shrike
```

### PlatformIO (Alternative)

Create `platformio.ini`:
```ini
[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
lib_deps = 
    bblanchon/ArduinoJson@^6.21.0
monitor_speed = 115200
```

Then:
```bash
pio run
pio run -t upload
```

## Uploading

### Firmware Upload

1. Connect ESP32-S3 via USB
2. Tools → Port → (select your port)
3. Sketch → Upload
4. Monitor: Tools → Serial Monitor (115200 baud)

### Filesystem Upload (FPGA Bitstream)

1. Place `fpga_bitstream.bin` in `data/` directory
2. Tools → ESP32 Sketch Data Upload
3. Wait for upload to complete

**Note**: FPGA bitstream file is a placeholder until actual synthesis is complete (Stage 3 pending).

## Configuration

### Pin Mappings (board_config.h)

- `FPGA_UART_RX`: GPIO11
- `FPGA_UART_TX`: GPIO13
- `FPGA_UART_BAUD`: 115200
- `STATUS_LED_PIN`: Built-in LED

Verify these match your physical board before uploading.

### Debug Output

Enable/disable in `board_config.h`:
```cpp
#define ENABLE_SERIAL_DEBUG 1  // Set to 0 to disable
```

Debug output appears on USB serial at 115200 baud.

## USB Protocol

### Command Format (JSON)

Commands are sent as JSON over USB serial (115200 baud):

```json
{"cmd": "ping"}
{"cmd": "config", "rotors": [0,1,2], "windows": [0,0,0], "rings": [0,0,0], "plugboard": ["AB", "CD"]}
{"cmd": "encrypt", "message": "HELLO"}
{"cmd": "decrypt", "message": "ILBDA"}
{"cmd": "reset"}
{"cmd": "status"}
```

### Response Format

```json
{"status": "ok", "result": "ILBDA", "windows": [0,0,4]}
{"status": "error", "error": "FPGA timeout"}
```

## Selftest

On boot, the firmware runs a hardware selftest (if `ENABLE_SELFTEST` is enabled):

1. **PING**: Verify FPGA communication
2. **Basic Vector**: AAAAA → BDZGO (rotors I II III, AAA)
3. **HELLOWORLD**: HELLOWORLD → ILBDAAMTAZ
4. **Double Stepping**: ADU → ADV → AEW → BFX → BFY
5. **State Readback**: Configuration verification

**If any test fails, the board remains in error state (rapid LED blink).**

## Troubleshooting

### Compilation Errors

- **"WiFi.h not found"**: Ensure ESP32 board package is installed
- **"ArduinoJson.h not found"**: Install ArduinoJson library
- **"FPGA.h not found"**: Arduino FPGA library pending - see placeholder code

### Upload Errors

- **Port not found**: Check USB connection, install CH340/CP2102 drivers if needed
- **Upload timeout**: Hold BOOT button during upload
- **Partition error**: Select correct partition scheme for your flash size

### Runtime Errors

- **"FPGA loader init failed"**: Filesystem not formatted - try data upload
- **"FPGA load failed"**: Bitstream missing or corrupt
- **"Selftest failed"**: FPGA not responding or incorrect wiring
- **"State uncertain"**: UART timeout - reset board and reconfigure

## Current Limitations

1. **FPGA Loader**: Arduino FPGA library ESP32-S3 support not verified
   - Placeholder code included for compilation
   - Requires library source inspection and potential adaptation
   - See comments in `fpga_loader.cpp`

2. **FPGA Bitstream**: Pending synthesis completion (Stage 3)
   - Placeholder file in `data/` directory
   - Replace with actual bitstream from vendor tools

3. **Hardware Testing**: Requires physical board
   - Selftest currently skipped (FPGA not loaded)
   - Enable when hardware is available

## File Structure

```
firmware/enigma_shrike/
├── enigma_shrike.ino      # Main sketch
├── board_config.h         # Pin definitions and constants
├── fpga_loader.h/cpp      # FPGA bitstream loading
├── uart_protocol.h/cpp    # FPGA communication protocol
├── plugboard.h/cpp        # Letter substitution
├── usb_protocol.h/cpp     # USB JSON commands
├── selftest.h/cpp         # Hardware verification
├── README.md              # This file
└── data/
    └── fpga_bitstream.bin # FPGA image (placeholder)
```

## Next Steps (Stage 5)

After firmware is uploaded and tested:
1. Develop desktop GUI (Python + PySide6)
2. Test full system integration
3. Document hardware demonstration
4. Create end-user setup instructions

## References

- ESP32-S3 Datasheet: https://www.espressif.com/en/products/socs/esp32-s3
- Arduino ESP32 Core: https://github.com/espressif/arduino-esp32
- ArduinoJson Documentation: https://arduinojson.org/
- Shrike Fi Specification: `../../docs/SPEC.md`

## License

See project root LICENSE file.
