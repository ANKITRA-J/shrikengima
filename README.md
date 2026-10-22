# Shrike Fi Enigma I Demonstrator

A complete Enigma I cipher implementation for the Vicharak Shrike Fi board. This project demonstrates hardware-accelerated cryptographic computation using the ESP32 S3 microcontroller and onboard FPGA working together to process messages through USB.

## Project Overview

This implementation builds a historically accurate Enigma I machine that operates entirely on the Shrike Fi board. A desktop GUI application communicates with the board via USB to configure settings and process messages. The FPGA performs the core cipher operations (rotor stepping, substitution, ring arithmetic, and reflection) while the ESP32 handles USB communication, text validation, and plugboard substitutions.

### Key Features

- **Hardware Cipher Processing**: All rotor operations execute on the FPGA, never falling back to software computation
- **Complete Enigma I Support**: Three configurable rotors (I-V), reflector B, ring settings, window positions, and plugboard
- **USB-Only Operation**: No Wi-Fi, Bluetooth, or network connectivity required
- **Visual Feedback**: FPGA LED blinks in response to letter processing
- **Reciprocal Operation**: Encrypt and decrypt using the same settings

## Component Responsibilities

| Component | Responsibility | Boundary |
|-----------|---------------|----------|
| **Desktop GUI** | Port selection, settings configuration, message entry, output display, error reporting | No local cipher computation, plugboard substitution, or rotor stepping |
| **ESP32 Firmware** | USB protocol handling, plugboard substitutions, text validation and formatting, FPGA bitstream loading, request/response management | No fallback rotor computation if FPGA unavailable |
| **FPGA** | Rotor state management, stepping logic, ring offset arithmetic, forward/inverse substitution, reflector, activity LED control | Processes contacts numbered 0-25 only |
| **Python Reference** | Development oracle for test generation and verification | Tests only; never used by production GUI |

## Build Prerequisites

### Hardware
- Vicharak Shrike Fi board (ESP32 S3 + Renesas FPGA)
- USB cable for connection to development machine

### Software
- **FPGA Development**: Renesas FPGA toolchain for bitstream generation
- **Firmware**: Arduino IDE with ESP32 S3 support
- **Desktop GUI**: Python 3.8+ with PySide6 and pyserial
- **Development Tools**: Python 3 for reference oracle and ROM generation

### Operating System
- Primary target: macOS
- GUI designed to be portable across platforms

## Implementation Stages

### Stage 1: Reference and Baseline
- Implement Python reference oracle from specification
- Run validation checks on wiring tables and known vectors
- Generate inverse rotor mappings
- Create deterministic test vectors
- Establish clean repository structure

**Deliverables**: Working `reference/enigma_ref.py`, passing self-tests, project structure

### Stage 2: Core Verification
- Add reset and input validation to sequential FPGA core
- Implement rotor ROM with 9-bit addressing (rotor ID, direction, contact)
- Build testbenches for core verification against Python oracle
- Test double-stepping, ring offsets, wraparound, and all rotor combinations
- Ensure simulation failures produce non-zero exit codes

**Deliverables**: Verified Verilog core, passing simulations, test reports

### Stage 3: Board Transport and Synthesis
- Implement UART modules with proper framing and error detection
- Build packet wrapper with CRC-8 validation
- Create top-level FPGA module with vendor-specific attributes
- Synthesize and place design for target FPGA
- Generate resource utilization and timing reports
- Produce real bitstream using vendor toolchain

**Deliverables**: Complete FPGA design, synthesis reports, bitstream image

### Stage 4: Firmware Integration
- Confirm board revision and flash configuration
- Implement FPGA configuration loader
- Establish runtime UART communication after configuration
- Implement internal packet protocol (PING, CONFIG, TRANSFORM, READ_STATE, RESET)
- Add plugboard logic and USB JSON command handler
- Run known test vectors through physical board

**Deliverables**: Working firmware, USB protocol implementation, hardware test results

### Stage 5: Desktop Application
- Build PySide6 GUI with serial port management
- Implement rotor, ring, window, and plugboard configuration
- Add encrypt/decrypt operations with proper state management
- Display initial and final rotor positions
- Show hardware status and connection state
- Handle errors and timeouts gracefully
- Document installation and usage

**Deliverables**: Complete GUI application, user documentation, setup instructions

## Build Instructions

### Generate FPGA ROM
```bash
python3 tools/gen_fpga_files.py
```
This generates `fpga/rtl/rotor_rom.v` containing all rotor and reflector wiring tables.

### Run Reference Tests
```bash
python3 reference/enigma_ref.py
```
Should report "Reference checks passed for all 60 rotor orders"

### FPGA Synthesis
*(Instructions will be added after vendor toolchain integration)*

### Firmware Build
*(Instructions will be added after Arduino configuration)*

### GUI Setup
*(Instructions will be added after dependency resolution)*

## Flashing Instructions

### FPGA Bitstream
*(Instructions will be added after bitstream generation)*

### ESP32 Firmware
*(Instructions will be added after firmware compilation)*

## Running the Application

### Starting the Desktop GUI
*(Instructions will be added after GUI implementation)*

### Basic Usage Flow
1. Connect Shrike Fi board via USB
2. Launch desktop application
3. Select serial port and connect
4. Wait for hardware readiness confirmation
5. Configure rotors (I-V), ring settings (AAA-ZZZ), initial positions (AAA-ZZZ)
6. Optionally add plugboard pairs (0-13 disjoint pairs)
7. Enter message text
8. Click Encrypt or Decrypt
9. View result and final rotor positions
10. To decrypt: paste ciphertext, keep same settings, click Decrypt

### Known Test Vectors
- Default settings (I II III, AAA rings, AAA windows, no plugs):
  - `AAAAA` → `BDZGO`
  - `HELLOWORLD` → `ILBDAAMTAZ`
- Double-stepping demonstration (I II III, AAA rings, ADU windows):
  - After 4 letters: windows advance ADV → AEW → BFX → BFY

## Project Structure

```
shrikengima/
├── docs/                    # Specification and documentation
│   └── SPEC.md             # Complete implementation specification
├── reference/              # Python reference oracle
│   └── enigma_ref.py       # Development oracle (not used by GUI)
├── tools/                  # Build and generation tools
│   └── gen_fpga_files.py   # ROM generator
├── fpga/                   # FPGA design files
│   ├── rtl/               # Verilog modules
│   ├── sim/               # Testbenches
│   └── project/           # Vendor project and constraints
├── firmware/               # ESP32 firmware
│   └── enigma_shrike/     # Arduino sketch
│       └── data/          # FPGA bitstream
├── desktop/                # Desktop GUI application
├── tests/                  # Unit and integration tests
└── reports/                # Build results and verification evidence
```

## Verification Requirements

All implementations must pass:
- Known historical vectors (BDZGO, ILBDAAMTAZ, double-stepping)
- Ring offset correctness with displayed turnover preservation
- All 60 rotor order combinations with randomized settings
- Plugboard validation (disjoint pairs, self-swap rejection)
- Boundary conditions (Z→A wrap, empty messages, non-letters)
- FPGA protocol (invalid packets, CRC failures, timeouts)
- Physical demonstration with visible LED activity

## License

*(To be determined)*

## References

- Specification: `docs/SPEC.md`
- Vicharak Shrike Fi Documentation: https://vicharak-in.github.io/shrike/
- Historical Enigma Details: https://www.cryptomuseum.com/crypto/enigma/

---

**Status**: Initial project structure established. Implementation in progress.
