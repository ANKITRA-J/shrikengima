# FPGA Synthesis Project

## Overview

This directory contains the synthesis project for the Shrike Fi Enigma implementation targeting the Renesas FPGA (1120 LUTs).

## Target Hardware

- **Board**: Shrike Fi
- **FPGA**: Renesas (1120 LUTs)
- **Clock**: 50MHz (OSC_CLK with OSC_EN enable)

## Pin Mappings

| Signal | Pin | Direction | Connection |
|--------|-----|-----------|------------|
| OSC_CLK | OSC_CLK | Input | 50MHz clock source |
| OSC_EN | OSC_EN | Input | Clock enable |
| uart_rx_pin | 5 | Input | ESP32-S3 GPIO11 (TX) |
| uart_tx_pin | 6 | Output | ESP32-S3 GPIO13 (RX) |
| led_out | GPIO16 | Output | Status LED |
| led_oe | GPIO16_OE | Output | LED output enable |

## Source Files

RTL modules (in `../../rtl/`):
- `enigma_top.v` - Top-level module
- `uart_rx.v` - UART receiver (115200 baud, 8N1)
- `uart_tx.v` - UART transmitter (115200 baud, 8N1)
- `packet_wrapper.v` - Protocol handler and packet parser
- `crc8.v` - CRC-8 calculator (polynomial 0x07)
- `enigma_core.v` - Enigma cipher engine
- `led_controller.v` - LED pulse controller
- `rotor_rom.v` - Rotor wiring lookup tables
- `helpers.v` - Modular arithmetic functions

## Synthesis Instructions

### Tool Requirements

This project requires Renesas FPGA design tools. The exact tool name and version depend on the specific Renesas FPGA variant used on the Shrike Fi board.

### Project Setup (Example - adjust to actual tool)

1. **Create New Project**
   ```bash
   # Launch Renesas FPGA Designer (or equivalent tool)
   # Select "New Project"
   # Choose target device matching Shrike Fi board
   ```

2. **Add Source Files**
   ```tcl
   # Add all RTL files
   add_file ../../rtl/enigma_top.v
   add_file ../../rtl/uart_rx.v
   add_file ../../rtl/uart_tx.v
   add_file ../../rtl/packet_wrapper.v
   add_file ../../rtl/crc8.v
   add_file ../../rtl/enigma_core.v
   add_file ../../rtl/led_controller.v
   add_file ../../rtl/rotor_rom.v
   add_file ../../rtl/helpers.v
   
   # Set top-level module
   set_top_module enigma_top
   ```

3. **Apply Constraints**
   ```tcl
   # Load pin constraints
   read_constraints enigma_shrike/constraints.pcf
   ```

4. **Run Synthesis**
   ```tcl
   # Synthesize design
   synthesize -target <device> -optimization balanced
   
   # Check resource utilization
   report_utilization
   ```

5. **Place and Route**
   ```tcl
   # Run place and route
   place_and_route
   
   # Check timing
   report_timing
   ```

6. **Generate Bitstream**
   ```tcl
   # Generate programming file
   generate_bitstream -output enigma_shrike.bit
   ```

### Expected Resource Usage

Estimated resource utilization:
- **LUTs**: ~750-1150 (target: <1120)
  - Enigma core: ~200-300 LUTs
  - Rotor ROM: ~400-600 LUTs
  - UART + Protocol: ~150-250 LUTs
- **Registers**: ~300-400
- **Clock domains**: 1 (50MHz)

### Optimization Notes

If resource usage exceeds 1120 LUTs:
1. Consider sequential ROM access instead of combinational
2. Compress rotor tables (exploit symmetries)
3. Share arithmetic resources between rotors
4. Use bit-serial CRC (8 cycles vs. 1 cycle)

### Timing Constraints

- **Clock frequency**: 50MHz (20ns period)
- **Setup/hold**: All paths must meet timing at 50MHz
- **UART timing**: 115200 baud with CLKS_PER_BIT=434 assumes exactly 50MHz clock

### Verification

Before synthesis, verify design using Icarus Verilog:
```bash
cd ../..
# Run all testbenches (see sim/README.md)
./run_all_tests.sh
```

## Status

**Synthesis Status**: Pending vendor tool availability

The RTL design is complete and verified via simulation. Synthesis requires access to Renesas FPGA design tools compatible with the Shrike Fi board.

## Next Steps (Stage 4)

1. Obtain Renesas FPGA design tools
2. Run synthesis and verify resource usage
3. Generate bitstream file
4. Integrate with ESP32-S3 firmware for flashing
5. Hardware testing on physical board
