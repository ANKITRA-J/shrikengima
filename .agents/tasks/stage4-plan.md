# Stage 4 Implementation Plan: ESP32 Firmware Integration

## Overview

Stage 4 implements the ESP32-S3 firmware that bridges the FPGA cipher core to the desktop GUI. The firmware handles FPGA bitstream loading, internal UART protocol, plugboard substitution, and USB serial communication.

**Dependencies:** Stage 3 complete (FPGA with UART protocol and packet wrapper verified)

**Key Design Decisions:**
- **Platform**: Arduino framework for ESP32-S3 on Shrike Fi board
- **FPGA Loader**: Use official Arduino FPGA library (confirm ESP32-S3 support)
- **UART**: Hardware Serial2 (GPIO11 RX, GPIO13 TX) at 115200 baud
- **USB Protocol**: JSON commands over USB CDC serial
- **Plugboard**: 26-byte array with bidirectional swaps
- **Storage**: SPIFFS/LittleFS for FPGA bitstream and metadata
- **No wireless**: WiFi/Bluetooth disabled for security

## Implementation Plan

- [ ] 1. **Create Arduino project structure**
      
      Set up the firmware directory with proper Arduino sketch structure and module organization.
      
      **Directory Structure:**
      ```
      firmware/enigma_shrike/
      ├── enigma_shrike.ino       # Main sketch
      ├── board_config.h          # Pin definitions and board settings
      ├── fpga_loader.h/cpp       # FPGA bitstream loading
      ├── uart_protocol.h/cpp     # Internal UART to FPGA
      ├── plugboard.h/cpp         # Letter substitution
      ├── usb_protocol.h/cpp      # JSON commands from GUI
      └── selftest.h/cpp          # Board verification
      firmware/enigma_shrike/data/
      └── fpga_bitstream.bin      # FPGA image (placeholder)
      ```
      
      **Files:**
      - firmware/enigma_shrike/enigma_shrike.ino
      - firmware/enigma_shrike/board_config.h
      - firmware/enigma_shrike/README.md
      
      **Verify:**
      - Directory structure matches specification Section 8
      - README documents build requirements and dependencies

---

- [ ] 2. **Implement board configuration (board_config.h)**
      
      Define all pin mappings, hardware settings, and constants for the Shrike Fi board.
      
      **Pin Definitions (from spec Section 2):**
      - UART to FPGA: GPIO11 (RX from FPGA Pin 6), GPIO13 (TX to FPGA Pin 5)
      - FPGA loading pins: per Arduino FPGA library
      - Status LED: TBD (board-specific)
      
      **Constants:**
      - UART baud: 115200
      - Packet timeout: 100ms
      - Max payload: 9 bytes
      - CRC polynomial: 0x07
      
      **Board Detection:**
      - Flash size detection (do not assume 8MB)
      - Board revision identification
      - PSRAM detection (do not enable if absent)
      
      **Files:**
      - firmware/enigma_shrike/board_config.h
      
      **Verify:**
      - Compiles without errors
      - Pin numbers match FPGA constraints.pcf mappings
      - No hardcoded 8MB flash or PSRAM assumptions

---

- [ ] 3. **Implement FPGA loader module (fpga_loader.h/cpp)**
      
      Load FPGA bitstream from flash storage, manage configuration pins, verify loader compatibility.
      
      **Requirements:**
      - Use Arduino FPGA library (verify ESP32-S3 support in actual source)
      - Load from SPIFFS/LittleFS at boot
      - Detect and validate bitstream metadata
      - Release configuration pins after successful load
      - Provide load status (success/failure)
      
      **Interface:**
      ```cpp
      bool FPGA_init();
      bool FPGA_loadBitstream(const char* path);
      bool FPGA_isConfigured();
      void FPGA_releaseConfigPins();
      ```
      
      **Error Handling:**
      - Missing bitstream file
      - Corrupt or invalid bitstream
      - Configuration timeout
      - Flash read errors
      
      **Files:**
      - firmware/enigma_shrike/fpga_loader.h
      - firmware/enigma_shrike/fpga_loader.cpp
      
      **Verify:**
      - Compiles with Arduino FPGA library
      - Does not assume RP2040 defaults (check actual ESP32-S3 support)
      - Detects flash capacity before partition selection
      - Records loader version and settings

---

- [ ] 4. **Implement UART protocol module (uart_protocol.h/cpp)**
      
      Handle packet formatting, CRC calculation, sequence numbers, and communication with FPGA.
      
      **Protocol (from spec Section 5):**
      - Request: A5 version(01) seq opcode length payload CRC
      - Response: 5A version(01) seq opcode|80 length status data CRC
      - Commands: PING(01), CONFIG(02), TRANSFORM(03), READ_STATE(04), RESET(05)
      
      **CRC-8:**
      - Polynomial: 0x07, init: 0x00
      - Check value: 0xF4 for "123456789"
      - Excludes marker byte and CRC itself
      
      **Timeout:**
      - 100ms per transaction (spec requirement)
      - On timeout: mark rotor state uncertain, require reinitialization
      
      **Sequence Management:**
      - 8-bit incrementing sequence numbers
      - Verify response matches request sequence
      
      **Interface:**
      ```cpp
      void UART_init();
      bool UART_ping(uint8_t* version);
      bool UART_config(uint8_t rotors[3], uint8_t windows[3], uint8_t rings[3]);
      bool UART_transform(uint8_t contact, uint8_t* result, uint8_t windows[3]);
      bool UART_readState(uint8_t windows[3]);
      bool UART_reset();
      uint8_t CRC8_update(uint8_t crc, uint8_t byte);
      ```
      
      **Error Handling:**
      - Invalid CRC: abort, do not retry automatically
      - Mismatched sequence: abort
      - Timeout: mark state uncertain
      - Invalid status code: report to USB layer
      
      **Files:**
      - firmware/enigma_shrike/uart_protocol.h
      - firmware/enigma_shrike/uart_protocol.cpp
      
      **Verify:**
      - CRC check value 0xF4 for ASCII "123456789"
      - Timeout behavior prevents infinite hangs
      - Does not automatically replay on error (FPGA may have stepped)
      - Honors 100ms deadline per specification

---

- [ ] 5. **Implement plugboard module (plugboard.h/cpp)**
      
      26-element array for letter pair swaps, applied before FPGA input and after FPGA output.
      
      **Plugboard Rules:**
      - Identity by default (A→A, B→B, etc.)
      - Each pair swaps both directions (AB means A↔B)
      - Validate: disjoint letters, no self-connections (AA invalid)
      - Reject: AB plus AC (overlapping), AB plus BA (redundant)
      - Maximum 13 pairs (26 letters / 2)
      
      **Interface:**
      ```cpp
      void Plugboard_init();
      bool Plugboard_setPair(char a, char b);
      void Plugboard_clear();
      char Plugboard_map(char letter);
      bool Plugboard_isValid();
      ```
      
      **Validation:**
      - Letters A-Z only (case-insensitive)
      - No letter appears in multiple pairs
      - No self-connections
      - Store normalized uppercase
      
      **Application:**
      - Input: GUI → Plugboard → FPGA (contact 0-25)
      - Output: FPGA (contact 0-25) → Plugboard → GUI
      
      **Files:**
      - firmware/enigma_shrike/plugboard.h
      - firmware/enigma_shrike/plugboard.cpp
      
      **Verify:**
      - Round-trip: Plugboard(Plugboard(x)) == x
      - Rejects invalid configurations
      - Does not perform rotor stepping or substitution (FPGA only)

---

- [ ] 6. **Implement USB protocol module (usb_protocol.h/cpp)**
      
      JSON-based command handling over USB CDC serial for desktop GUI communication.
      
      **Command Format (JSON):**
      ```json
      {
        "cmd": "ping|config|encrypt|decrypt|reset|status",
        "rotors": [0-4, 0-4, 0-4],
        "windows": [0-25, 0-25, 0-25],
        "rings": [0-25, 0-25, 0-25],
        "plugboard": ["AB", "CD", ...],
        "message": "HELLO"
      }
      ```
      
      **Response Format:**
      ```json
      {
        "status": "ok|error",
        "result": "ILBDA",
        "windows": [4, 4, 4],
        "error": "description"
      }
      ```
      
      **Commands:**
      - **ping**: Return firmware version and FPGA status
      - **config**: Set rotors, windows, rings, plugboard
      - **encrypt/decrypt**: Process message letter by letter
      - **reset**: Reset FPGA and plugboard to defaults
      - **status**: Get current configuration and readiness
      
      **Requirements:**
      - Non-blocking: check Serial.available() without blocking
      - Bounded buffers: max message length (e.g., 1024 chars)
      - No message history: process and discard
      - Responsive: never block indefinitely
      - Validate all inputs before FPGA operations
      
      **Error Handling:**
      - Oversize input: truncate or reject
      - Malformed JSON: return error response
      - Invalid settings: return validation error
      - FPGA timeout: return error, mark state uncertain
      - Disconnect: detect and handle gracefully
      
      **Files:**
      - firmware/enigma_shrike/usb_protocol.h
      - firmware/enigma_shrike/usb_protocol.cpp
      
      **Verify:**
      - Parses valid JSON commands
      - Rejects invalid inputs with error messages
      - Does not block on USB read
      - Never generates fallback ciphertext on error

---

- [ ] 7. **Implement selftest module (selftest.h/cpp)**
      
      Hardware verification using known test vectors through physical FPGA.
      
      **Test Vectors (from spec Section 9):**
      - Rotors I II III, AAA rings, AAA windows, no plugboard:
        - Input: AAAAA → Expected: BDZGO
        - Input: HELLOWORLD → Expected: ILBDAAMTAZ
      - Double stepping: Start ADU with I II III:
        - Windows: ADU → ADV → AEW → BFX → BFY
      - Non-A rings: verify turnover behavior preserved
      
      **Selftest Sequence:**
      1. FPGA PING (verify communication)
      2. CONFIG with known settings
      3. READ_STATE (verify configuration)
      4. TRANSFORM letters and compare results
      5. Verify final window positions
      6. Restore user settings (if any)
      
      **Requirements:**
      - Run on boot (after FPGA load)
      - Must pass before marking board ready
      - If selftest fails, remain unavailable to GUI
      - After passing, restore user's saved settings at their initial windows
      - If restoration fails, remain unavailable
      
      **Interface:**
      ```cpp
      bool Selftest_run();
      bool Selftest_basicVectors();
      bool Selftest_doubleStepping();
      bool Selftest_stateReadback();
      ```
      
      **Files:**
      - firmware/enigma_shrike/selftest.h
      - firmware/enigma_shrike/selftest.cpp
      
      **Verify:**
      - Tests actual FPGA hardware (not simulation)
      - Compares both ciphertext AND final windows
      - Returns boolean success/failure
      - Logs failure details for debugging

---

- [ ] 8. **Implement main sketch (enigma_shrike.ino)**
      
      Integrate all modules with initialization sequence and main loop.
      
      **Initialization Sequence:**
      1. Disable WiFi and Bluetooth (security requirement)
      2. Initialize USB CDC serial
      3. Detect board revision and flash size
      4. Initialize filesystem (SPIFFS/LittleFS)
      5. Load FPGA bitstream
      6. Release configuration pins
      7. Initialize UART to FPGA
      8. Run selftest
      9. If selftest passes, restore saved settings
      10. Mark ready for GUI commands
      
      **Main Loop:**
      1. Check USB serial for commands (non-blocking)
      2. Parse and validate commands
      3. Execute operations via UART protocol
      4. Apply plugboard substitutions
      5. Send responses to USB
      6. Handle watchdog and timeouts
      
      **Error States:**
      - FPGA load failure: report error, halt
      - Selftest failure: report error, halt
      - FPGA communication timeout: mark uncertain, require reset
      - USB disconnect: detect, continue operation
      
      **Files:**
      - firmware/enigma_shrike/enigma_shrike.ino
      
      **Verify:**
      - Compiles for ESP32-S3
      - No infinite blocking loops
      - Watchdog remains responsive
      - Ready LED or status indicator functional

---

- [ ] 9. **Create build documentation**
      
      Document dependencies, build process, upload procedure, and hardware requirements.
      
      **Contents:**
      - Arduino IDE version and board package
      - Required libraries and versions
      - Board settings (flash size, partition scheme, etc.)
      - Upload procedure (USB/JTAG)
      - Filesystem upload (bitstream file)
      - Serial monitor setup
      - Troubleshooting common issues
      
      **Files:**
      - firmware/enigma_shrike/README.md
      - firmware/enigma_shrike/platformio.ini (if using PlatformIO)
      
      **Verify:**
      - Build instructions are complete
      - Dependencies are pinned/versioned
      - Hardware requirements documented
      - Upload steps are reproducible

---

- [ ] 10. **Document Stage 4 completion**
      
      Summarize implementation, test results, and hardware status.
      
      **Contents:**
      - Module summary and file listing
      - Build and upload verification
      - Selftest results (if hardware available)
      - Known test vectors and outcomes
      - Pin mappings confirmation
      - Integration with FPGA verified/pending
      - Stage 5 prerequisites checklist
      
      **Files:**
      - reports/stage4-firmware.txt
      
      **Verify:**
      - Firmware compiles without errors
      - Module interfaces documented
      - Hardware testing status clearly marked (done/pending)
      - Next steps identified

---

## Build Commands Reference

**Arduino CLI (if available):**
```bash
# Install ESP32 board support
arduino-cli core install esp32:esp32

# Install required libraries
arduino-cli lib install "Arduino FPGA"
arduino-cli lib install "ArduinoJson"

# Compile
arduino-cli compile --fqbn esp32:esp32:esp32s3 firmware/enigma_shrike

# Upload
arduino-cli upload -p /dev/cu.usbserial-* --fqbn esp32:esp32:esp32s3 firmware/enigma_shrike

# Upload filesystem
arduino-cli upload --input-dir firmware/enigma_shrike/data -p /dev/cu.usbserial-* --fqbn esp32:esp32:esp32s3
```

**Arduino IDE:**
1. Tools → Board → ESP32 Arduino → ESP32S3 Dev Module
2. Tools → Upload Speed → 921600
3. Tools → Flash Size → (detected size)
4. Tools → Partition Scheme → (with SPIFFS/LittleFS)
5. Sketch → Upload
6. Tools → ESP32 Sketch Data Upload (for filesystem)

**PlatformIO (alternative):**
```bash
pio run -e esp32s3
pio run -t upload
pio run -t uploadfs
```

## Known Constraints and Assumptions

**Arduino FPGA Library:**
- Official library README shows RP2040 defaults
- MUST verify ESP32-S3 support in actual source code (not just README)
- May require adaptation for different GPIO/SPI configuration
- Record actual loader version used

**Flash and Partitions:**
- Do NOT assume 8MB flash (detect actual capacity)
- Do NOT enable PSRAM if not present
- Do NOT erase board as routine setup
- Choose partition scheme based on detected size

**Serial Hardware:**
- USB CDC: Serial (default USB port to GUI)
- UART to FPGA: Serial2 on GPIO11 (RX) / GPIO13 (TX)
- Ensure no conflicts with FPGA loader pins

**Timing:**
- 100ms timeout per FPGA transaction (specification requirement)
- UART at 115200 baud (8N1)
- Non-blocking USB read (main loop remains responsive)

**State Management:**
- Only store firmware + FPGA image + metadata persistently
- Settings and messages are volatile (unless explicitly saved)
- After selftest, restore user's saved settings
- On FPGA timeout, mark rotor state uncertain (require full reconfig)

## Stage 5 Prerequisites

Stage 4 completion provides:
1. Compiled firmware for ESP32-S3
2. FPGA loader with bitstream management
3. UART protocol with all 5 commands
4. Plugboard implementation
5. USB JSON protocol
6. Selftest with known vectors
7. Build and upload documentation

Stage 5 (Desktop GUI) requires:
- Firmware uploaded to physical board
- USB serial protocol specification
- Command/response format documentation
- Error codes and status messages
- Board detection and port selection

## Success Criteria

Stage 4 is complete when:
- [x] All 8 source modules created (ino, loader, uart, plugboard, usb, selftest, config)
- [x] Firmware compiles without errors for ESP32-S3
- [x] FPGA loader verified (source checked for ESP32-S3 support)
- [x] UART protocol implements all 5 commands with CRC
- [x] Plugboard validates and applies substitutions
- [x] USB protocol parses JSON and returns responses
- [x] Selftest runs known vectors
- [x] Build documentation complete
- [x] Stage 4 report written

Hardware testing (if board available):
- [ ] Upload firmware to physical ESP32-S3
- [ ] Verify FPGA bitstream loads successfully
- [ ] Selftest passes on hardware
- [ ] Known vector: AAAAA → BDZGO verified
- [ ] USB communication functional

If hardware unavailable:
- Complete source code and compilation
- Document untested verification steps
- Mark hardware validation as pending

---

**Total Steps:** 10  
**Estimated Effort:** High (new platform, multiple protocols, hardware integration)  
**Critical Path:** FPGA loader (step 3) and UART protocol (step 4)  
**Risk Areas:** Arduino FPGA library ESP32-S3 compatibility, flash detection, timing constraints  
