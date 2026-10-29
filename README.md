# Shrike Fi Enigma

A laptop-controlled Enigma simulator for the Vicharak Shrike Fi. The ESP32-S3 handles USB and the plugboard; the SLG47910V FPGA performs rotor stepping, wiring and reflection. Encryption and decryption use identical settings and the same FPGA operation. The production app has no software cipher fallback.

**Hardware verified:** the included FPGA image has passed all 60 rotor orders, encryption/decryption, the 512-byte message boundary, GUI operation, and 30,720 additional stress-test letters on a physical Shrike Fi. See [STATUS.md](STATUS.md) and the [build manifest](reports/2026-10-29/build-manifest.json) for the tested configuration and evidence.

## What you need

- A Shrike Fi with ESP32-S3, 8 MB flash and SLG47910V FPGA, plus a USB data cable.
- Python **3.9–3.13** and Git (or download this repository as a ZIP). The pinned PySide6 version does not support Python 3.14 or newer.
- Arduino CLI, ESP32 Arduino core **3.3.12**, and ArduinoJson **6.21.5** to build and flash the MCU.
- Go Configure **6.55.002** only if you want to rebuild or change the FPGA logic. A tested MCU-format FPGA image is included.

The complete setup was verified on macOS. The Python GUI and build helper include Linux/Windows support, but those hosts have not undergone the recorded physical acceptance run. No external LED wiring or FPGA programmer is needed for normal use: the MCU loads the FPGA at startup.

## First run

1. Get the project and open its root folder in your editor:

   ```sh
   git clone https://github.com/ANKITRA-J/shrikengima.git
   cd shrikengima
   ```

2. Install the firmware tools and flash **both firmware and LittleFS** using the [step-by-step build guide](docs/BUILD_AND_USE.md#firmware-build-and-flashing). The helper uses the included FPGA image:

   ```sh
   python3 tools/build_firmware.py --bitstream firmware/enigma_shrike/data/fpga_bitstream.bin --port YOUR_PORT
   ```

   Replace `YOUR_PORT` with your board's port from `arduino-cli board list` (for example `/dev/cu.usbmodem1101`, `/dev/ttyACM0`, or `COM5`). A normal Arduino sketch upload alone does not install the FPGA image.

3. Install and start the desktop app from the repository root:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r desktop/requirements.txt
   .venv/bin/python desktop/enigma_gui.py
   ```

   Use a supported Python interpreter to create `.venv` (for example `python3.13 -m venv .venv` if your default `python3` is newer). On Windows, use `python` instead of `python3`, and `.venv\Scripts\python.exe` instead of `.venv/bin/python`. On macOS, after this setup, you can also double-click `Launch Enigma.command`.

4. Close Arduino Serial Monitor and other programs using the port. In the app click **Refresh**, choose the board, then **Connect**. Startup verification must succeed before the app accepts work. With rotors I–II–III, rings AAA, windows AAA and no plugs, `HELLOWORLD` encrypts to `ILBDAAMTAZ`. Enter that ciphertext and click **Decrypt** with the same settings to recover `HELLOWORLD`.

Choose three distinct rotors I–V, rings and initial windows, and optional disjoint plugboard pairs. Each message starts at the selected initial windows; final windows are shown separately. Lowercase becomes uppercase. ASCII punctuation and spacing are preserved without advancing the rotors. Messages may contain up to 512 ASCII bytes.

## Build, test and modify

The [build and use guide](docs/BUILD_AND_USE.md) contains exact installation commands, Arduino IDE settings, the Go Configure workflow, pin mapping, other-IDE instructions and troubleshooting. Source files are ordinary Python, Arduino C++ and Verilog; Codex and Kiro are not runtime dependencies.

After flashing, verify your own board:

```sh
.venv/bin/python tests/hardware_test.py --port YOUR_PORT
.venv/bin/python tests/gui_hardware_test.py --port YOUR_PORT
```

Close the regular GUI before running these tests. Add `--stress-rounds 30` to the hardware test for the extended randomized checks. Developers with Verilator and a C++ compiler can run host tests with `.venv/bin/python tools/run_checks.py`.

To change the FPGA, edit `fpga/rtl/`, run `python3 tools/gen_fpga_files.py` and `python3 tools/prepare_fpga.py`, then open `fpga/project/enigma/enigma.ffpga` in Go Configure. Follow the build guide to generate the correct **MCU SPI image**, rebuild LittleFS, flash and retest. Build products are ignored under `build/`; recorded release evidence is under `reports/2026-10-29/`.

## Source map

| Location | Purpose |
| --- | --- |
| `fpga/rtl/` | Authoritative Verilog core, UART, protocol and LED logic |
| `fpga/sim/` | Core, packet and full top-level testbenches |
| `fpga/project/enigma/` | Renesas project, physical mapping and clock constraints |
| `firmware/enigma_shrike/` | Arduino sketch, FPGA loader, USB/UART protocol and plugboard |
| `desktop/` | PySide6 interface and serial client |
| `reference/` | Independent Python oracle used only by tests |
| `tests/` | Desktop/native tests, vector generation and physical-board acceptance |
| `tools/` | Repeatable generation, build and test entry points |
| `reports/2026-10-29/` | Build manifest, timing, mapping, flash and test evidence |
| [docs/SPEC.md](docs/SPEC.md) | USB JSON and MCU–FPGA UART contracts |
| [STATUS.md](STATUS.md) | Verified results, limitations and hardware corrections |

The FPGA activity LED and MCU status LED are built into the board. This project implements Enigma encryption/decryption; a Bombe-style key-search/cracking engine is not implemented. Historical stage reports and `IMPLEMENTATION_COMPLETE.md` are superseded by STATUS.md and the current build guide.
