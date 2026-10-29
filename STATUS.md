# Project status — verified 29–30 October 2026

**The FPGA-backed Enigma simulator is working on the connected Shrike Fi.** Firmware and the real FPGA image are flashed. Startup self-test, the full hardware suite, extended stress tests, and GUI encryption/decryption pass. This records the tested board/build, not a guarantee for arbitrary boards or future changes.

## Verified results

- Python reference oracle: all 60 rotor orders.
- RTL: core stepping/rings; packet protocol, CRC/error/timeout handling across all 60 orders; top-level clock feedback, startup, UART framing and LED output.
- Desktop: seven transport/validation unit tests; GUI works with no ports; real GUI Connect, Encrypt, Decrypt and Reset buttons pass against the board.
- Native firmware: sequence wrap, CRC/opcode/length rejection, deadlines, malformed reset/state payload rejection, recovery, and no automatic letter replay.
- Physical hardware: startup known vectors; all 60 rotor orders with randomized rings/windows and plugs; exact oracle comparison; decryption reciprocity; empty/nonletter input; 512-byte maximum; invalid input rejection; reset.
- Stress: 30 pairs of randomized 512-letter encryption/decryption messages, totaling **30,720 additional FPGA letter transformations**, with no mismatch. The final firmware was flashed again on 30 October; its full hardware suite and another **5,120 stress-test letters** passed, followed by the GUI hardware test. These final acceptance results are recorded in `hardware-test.log` and `gui-hardware-test.log`.
- Target: ESP32-S3 revision 0.2 with 8 MB flash; SLG47910V Rev BB vendor project. An original MCU flash backup is retained outside the repository.
- FPGA: **136/140 CLBs, 799/1120 LUT5s, 361 FFs**. Post-route internal clock timing passes with worst setup slack **+15.059 ns** and total negative slack **0**. UART inputs are asynchronous; this is not a claim of synchronous external I/O timing signoff.

## Evidence

- [Build manifest and binary hashes](reports/2026-10-29/build-manifest.json)
- [Hardware acceptance](reports/2026-10-29/hardware-test.log)
- [Extended stress test](reports/2026-10-29/hardware-stress.log)
- [GUI hardware test](reports/2026-10-29/gui-hardware-test.log)
- [Flash verification](reports/2026-10-29/flash.log)
- [Host checks](reports/2026-10-29/host-checks.log) and [native transport checks](reports/2026-10-29/native-checks.log)
- [Timing](reports/2026-10-29/PNR_TIMING.log), [I/O mapping](reports/2026-10-29/PNR_IO.log), [resources](reports/2026-10-29/resource-utilization-report.log)

## Corrections that enabled hardware operation

1. Explicit internal clock feedback: OSC/16 → `REF_LOGIC_AS_CLK1` → enabled `LOGIC_AS_CLK1`. The previous implicit divided clock was placed on an unconnected clock input. No external clock jumper is needed.
2. Correct UART pins: MCU GPIO11 TX → FPGA GPIO5 (package pin 18); FPGA GPIO6 (package pin 19) → MCU GPIO13 RX. Manufacturer labels such as “FPGA PIN 5” refer to GPIO numbers here, not package pins.
3. USB receive/transmit buffers now hold a complete bounded JSON line. The default 256-byte receive buffer dropped long requests.
4. Protocol sequencing, CRC handling, validation, reset behavior, native tests, FPGA resource use and GUI job handling were repaired.

The earlier 6.25 MHz physical build produced occasional isolated wrong letters. The final **3.125 MHz** build passes the extended comparisons. Lowering the clock also changes physical placement; the evidence does not isolate the exact electrical/timing cause of that earlier behavior. Retain the tested clock and regenerate/retest after changes. UART remains approximately 115741 baud (27 clocks/bit), compatible with the MCU's 115200 setting.

## Use and development

Start with [README.md](README.md) and [BUILD_AND_USE.md](docs/BUILD_AND_USE.md). On this Mac, `.venv` and ArduinoJson 6.21.5 are installed; double-click `Launch Enigma.command` to launch the app. Source, tests, vendor project, image and reports live in the repository and work independently of Codex/Kiro.

The authoritative RTL is `fpga/rtl`; regenerate the vendor source with `tools/prepare_fpga.py`. The real 46,408-byte MCU image is `firmware/enigma_shrike/data/fpga_bitstream.bin`. Do not substitute the raw core, FLASH_MEM or OTP image.

The built-in FPGA LED is an activity output; the MCU LED blinks on startup/transport failure. LED RTL behavior is simulated; electrical UART/cipher operation is tested. No external LEDs are required.

This implements Enigma encryption/decryption. A Bombe key-search/cracking engine is a separate feature and is not implemented. Historical stage/completion reports are superseded by this document. Changes are committed locally after testing; no GitHub push is part of this update.
