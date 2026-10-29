# Build, test and use Shrike Fi Enigma

Open the repository root in any IDE. Source files are ordinary Python, Arduino C++ and Verilog. The recorded board acceptance run used macOS; Linux and Windows setup paths are provided but have not been hardware-validated here. See the validation section below for the tested image and limitations.

For a new board, install the firmware tools and flash the included image, install the desktop dependencies, then run the board tests. Rebuilding the FPGA is optional unless you change the RTL. All commands below run from the repository root. On Windows use `python` where an example uses `python3`.

## Architecture and behavior

The laptop GUI sends newline-delimited JSON over USB. The ESP32-S3 validates ASCII text and settings, applies the plugboard, and sends CRC-protected UART packets to the FPGA. The FPGA steps the rotors and performs forward wiring, reflector B and inverse wiring. The MCU applies the plugboard again and returns the result. The development oracle in `reference/` is used only for tests.

Choose three distinct rotors I–V, initial windows and rings A–Z, and up to 13 disjoint plugboard pairs. Every Encrypt or Decrypt starts from the selected initial windows. For decryption, keep exactly the same rotor order, rings, windows and plugs. Lowercase letters become uppercase; spaces, punctuation, digits, tabs and line breaks are retained and do not step the machine. Messages are limited to 512 ASCII bytes. Final positions are displayed separately from the initial settings.

## Hardware and connections

Target: Vicharak Shrike Fi, ESP32-S3 with 8 MB flash and SLG47910V Rev BB FPGA. No external LEDs or jumpers are needed for the built-in MCU/FPGA links.

| Function | ESP32 GPIO | FPGA GPIO / package pin |
| --- | --- | --- |
| Runtime UART MCU TX | 11 | GPIO5 / pin 18 (FPGA RX) |
| Runtime UART MCU RX | 13 | GPIO6 / pin 19 (FPGA TX) |
| Built-in activity LED | — | GPIO16 / pin 7 |
| Built-in MCU status LED | 21 | — |
| Configuration SPI | SCK 12, MOSI 11, MISO 13, SS 10 | On-board configuration link |
| FPGA power/enable | 8 / 9 | On-board controls |

The table distinguishes FPGA GPIO numbers from package-pin numbers: Vicharak's “FPGA PIN 5/6” labels mean GPIO5/6, which are package pins 18/19 on this device. Confusing these labels leaves the UART disconnected. Mappings are based on [Vicharak's pinout](https://github.com/vicharak-in/shrike/blob/main/docs/shrike_pinouts.md) and Shrike Arduino library 1.1.0. The loader releases shared SPI pins before starting UART. Debug prints are disabled on the JSON port. Wi-Fi and Bluetooth are disabled.

## Desktop setup

Use Python **3.9–3.13** (the recorded run used Python 3.9.6, PySide6 6.8.3 and pyserial 3.5). The pinned PySide6 package requires Python below 3.14. Install a compatible Python from [python.org](https://www.python.org/downloads/) if needed; if your default `python3` is newer, use `python3.13` to create the virtual environment. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r desktop/requirements.txt
.venv/bin/python desktop/enigma_gui.py
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`. In your IDE choose this virtual environment as the Python interpreter. The app requires a board flashed using the firmware steps below. On macOS, after creating `.venv`, `Launch Enigma.command` is a double-click launcher. On Windows the equivalent commands are:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r desktop/requirements.txt
.venv\Scripts\python.exe desktop/enigma_gui.py
```

Connect USB, click Refresh, select the board's serial port, then Connect. Set rotors/rings/windows/plugs, enter text and Encrypt. Copy the ciphertext into the input and Decrypt to verify reciprocity. Hardware Self-test runs known vectors on the FPGA. Reset Board resets both hardware and visible settings to I–II–III, AAA windows, AAA rings and no plugs. Settings are volatile.

## Firmware build and flashing

Install [Arduino CLI](https://arduino.github.io/arduino-cli/latest/installation/) and put `arduino-cli` on your PATH. Arduino IDE is optional for the command-line workflow. The helper can also use the CLI bundled in the standard macOS Arduino IDE installation, or an explicit `--arduino-cli PATH`.

Install the exact board core and JSON library used by the tested build:

```sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.12 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli lib install ArduinoJson@6.21.5
arduino-cli board list
```

The ESP32 core also installs `esptool` and `mklittlefs`. The custom FPGA loader uses core SPI/LittleFS; a third-party Shrike/FPGA library is not required. Connect the board with a USB data cable and identify its port in the last command. Examples are `/dev/cu.usbmodem1101` on macOS, `/dev/ttyACM0` on Linux, and `COM5` on Windows; use the port actually shown for your board. Close the GUI, Serial Monitor and other serial programs before flashing.

The helper compiles the sketch and packages `/fpga_bitstream.bin` in LittleFS. First build without changing the board, then flash:

```sh
python3 tools/build_firmware.py --bitstream firmware/enigma_shrike/data/fpga_bitstream.bin
python3 tools/build_firmware.py --bitstream firmware/enigma_shrike/data/fpga_bitstream.bin --port YOUR_PORT
```

The second command compiles again and flashes the bootloader, partition table, application and filesystem. It replaces the previous application/data in those partitions; preserve anything you need first. Successful flashing reports verification of the written data and resets the board. At startup the MCU loads the FPGA from LittleFS and runs its known-vector self-test. Verify success with the hardware test below; a blinking LED alone is not acceptance evidence.

Outputs are in `build/firmware/`. The tested partition layout has LittleFS at `0x670000`, size `0x180000`; the helper reads these values from the generated partition CSV instead of assuming them. The FPGA is configured at each MCU startup, so no separate permanent FPGA programming step is needed.

Optional arguments are `--arduino-cli PATH`, `--esp32-tools PATH`, `--libraries PATH` and `--build PATH`; see `python3 tools/build_firmware.py --help`. Standard Arduino package tool locations are detected by operating system:

| Host | Default ESP32 tools folder |
| --- | --- |
| macOS | `~/Library/Arduino15/packages/esp32/tools` |
| Linux | `~/.arduino15/packages/esp32/tools` |
| Windows | `%LOCALAPPDATA%/Arduino15/packages/esp32/tools` |

For a portable/custom Arduino installation, override `--esp32-tools` with its `packages/esp32/tools` directory. Quote paths containing spaces. If Arduino CLI is not on PATH and not at the standard macOS IDE location, supply its full executable path with `--arduino-cli`.

### Arduino IDE or another editor

Open `firmware/enigma_shrike/enigma_shrike.ino` in Arduino IDE. In Preferences, add the ESP32 board-manager URL from the CLI commands above; install **esp32 by Espressif Systems 3.3.12** through Boards Manager and **ArduinoJson 6.21.5** through Library Manager. Select:

| Setting | Value |
| --- | --- |
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | Enabled |
| Flash Size | 8 MB |
| Partition Scheme | 8M with spiffs (3MB APP/1.5MB SPIFFS) |
| Port | Your connected board's port |

The corresponding CLI FQBN is `esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=8M,PartitionScheme=default_8MB`. Despite the partition label `spiffs`, the project stores a **LittleFS** image there. Do not use a SPIFFS-format uploader.

Arduino IDE can compile or upload the sketch, but its normal Upload button does **not** install `data/fpga_bitstream.bin`. Use the helper for the first installation and whenever the FPGA image or partition layout changes. Once LittleFS is installed, ordinary sketch uploads using the same partition settings can update the MCU application. Re-run the hardware tests after changes.

VS Code, CLion or another editor can open the repository and invoke the same scripts in its terminal. Select `.venv` as the Python interpreter. Use Go Configure for FPGA synthesis/place-and-route; editing Verilog in another IDE does not replace that device-specific build step. There is no PlatformIO project configuration included.

## Optional: rebuild the FPGA in Go Configure

Skip this section when using the tested `firmware/enigma_shrike/data/fpga_bitstream.bin`. To rebuild, install Renesas Go Configure Software Hub with FPGA Editor support for SLG47910. Validated tool version during development: Go Configure Software Hub **6.55.002**, bundled Yosys v59 and placer v23. The project targets **SLG47910V Rev BB**.

```sh
python3 tools/gen_fpga_files.py
python3 tools/prepare_fpga.py
```

Open `fpga/project/enigma/enigma.ffpga` in Go Configure. Select FPGA Editor, Synthesize, then Generate Bitstream. The project includes physical I/O mappings. `fpga/rtl/` is the source of truth: do not edit generated `ffpga/src/main.v` directly. Regenerate it after RTL edits. The synthesis options `-nocarry -nowidelut` avoid inefficient Xilinx carry/multiplexer mapping on this device.

The 50 MHz oscillator feeds a registered divide-by-sixteen clock (3.125 MHz) for the protocol and cipher. The divider output `core_clk_out` maps to `REF_LOGIC_AS_CLK1`, `core_clk_en` drives `LOGIC_AS_CLK1_EN` high, and `core_clk` maps to the dedicated `LOGIC_AS_CLK1` clock input. This is an internal chip connection, requiring no external jumper. Do not use an unmapped logic-derived clock: simulation can pass while hardware remains stopped. See section 6.4 of the [SLG47910 datasheet](https://www.renesas.com/en/document/dst/slg47910-datasheet). UART uses 27 core clocks per bit (about 115741 baud, within 0.5% of 115200). LED pulse and protocol timeout counters are scaled to this clock. Timing constraints are in `ffpga/timing-constraints/clocks.sdc`; verify that they are included in the project and that routing/timing passes before using an image.

Use `ffpga/build/bitstream/FPGA_bitstream_MCU.bin`, the vendor MCU SPI image. Do not use the raw core, FLASH_MEM, or OTP image with this loader. A successful synthesis alone does not mean a valid image exists. The tracked `firmware/enigma_shrike/data/fpga_bitstream.bin` contains the tested image; its SHA-256 and validation status are in the [build manifest](../reports/2026-10-29/build-manifest.json). The recorded board acceptance and stress tests pass; see the validation section below.

After a new successful FPGA build, pass its image directly to the firmware helper:

```sh
python3 tools/build_firmware.py --bitstream fpga/project/enigma/ffpga/build/bitstream/FPGA_bitstream_MCU.bin --port YOUR_PORT
```

This packages that image into LittleFS. Rebuilding or uploading the Arduino sketch without rebuilding/flashing LittleFS leaves the old FPGA image installed. After acceptance tests pass, replace the tracked `firmware/enigma_shrike/data/fpga_bitstream.bin` and update the build manifest when preparing a new release. Existing reports describe the recorded build, not your new binary.

## Repeatable verification

For host/RTL tests, install Verilator 5.x with timing support, a C++ compiler and Make in a POSIX build environment (macOS/Linux, or an appropriately configured Windows development environment). Physical-board and GUI tests only need the Python dependencies and flashed board. Close the regular GUI before running the serial tests, and replace `YOUR_PORT` below:

```sh
.venv/bin/python tools/run_checks.py
.venv/bin/python tests/hardware_test.py --port YOUR_PORT
.venv/bin/python tests/gui_hardware_test.py --port YOUR_PORT
```

For extended randomized board checking, add `--stress-rounds 30` to the hardware test (30,720 additional letters, including decryption).

The first command runs reference tests, desktop tests, native firmware transport tests, core tests, all-rotor packet simulations and a full top-level UART/startup simulation. The second runs the actual USB→MCU→FPGA path, including all 60 rotor orders, random rings/positions, plugs, encryption/decryption reciprocity, boundaries and validation. It restores default settings when successful. The third command exercises real GUI buttons and asynchronous callbacks against the connected board. The GUI test opens its own window; set `QT_QPA_PLATFORM=offscreen` for unattended testing (`QT_QPA_PLATFORM=offscreen .venv/bin/python tests/gui_hardware_test.py --port YOUR_PORT` on macOS/Linux). Run serial tests sequentially so they do not compete for the port.

For vendor Verilator installations lacking runtime headers/make support, `run_checks.py` accepts `--verilator /path/to/verilator_bin --runtime /path/to/verilator/include`. Use matching runtime/binary versions. Build products go under `build/`, which is ignored by Git.

## Troubleshooting

- Power LED on but no USB serial port: unplug/reconnect a data cable; hold BOOT, tap RESET, release BOOT to enter the downloader. A power LED alone does not confirm USB enumeration.
- Port busy: close Arduino Serial Monitor, the regular GUI and any other serial terminal before flashing or running tests. On Linux, a permission error may require your account to join the distribution’s serial-device group (commonly `dialout`) and log in again.
- Missing `mklittlefs`/`esptool`: install the specified ESP32 core; for a custom Arduino data directory, set `--esp32-tools` to the matching package tools folder.
- Python dependency installation fails: use a supported Python version with a PySide6 6.8.3 wheel for your OS/CPU and install into `.venv`, not the system Python.
- FPGA not ready: check that a real bitstream is in LittleFS and matches this board; inspect the firmware's `hello` response. No ciphertext is returned when the FPGA is unavailable.
- UART error or uncertain rotor state: reconnect/reapply settings before another operation. A failed letter is never automatically retried, since the physical rotor state may already have advanced.
- Resource or timing failure: regenerate source, check target device and project synthesis settings, and read vendor reports. Do not use reports from an earlier RTL revision.

For custom clients, consult `desktop/serial_manager.py` and `firmware/enigma_shrike/usb_protocol.cpp` for the USB messages, and `firmware/enigma_shrike/uart_protocol.cpp` and `fpga/rtl/packet_wrapper.v` for the board protocol. These describe the implemented interfaces.


## Validation and limitations

The included image passed all 60 rotor orders, randomized rings/windows and plugboard checks, encryption/decryption round trips, the 512-byte boundary, and GUI Connect/Encrypt/Decrypt/Reset against a physical Shrike Fi. Extended testing completed 30,720 additional letter transformations; the final firmware acceptance run added another 5,120. Host checks cover the reference, desktop transport, native firmware transport and RTL simulations.

The build uses **136/140 CLBs, 799/1120 LUT5s and 361 flip-flops**. Post-route internal clock timing has **+15.059 ns** worst setup slack and zero total negative slack. This does not claim synchronous timing signoff for asynchronous UART inputs.

Retain the tested **3.125 MHz** core clock. An earlier 6.25 MHz image produced occasional wrong letters on hardware; changing the clock also changed placement, so the precise cause was not isolated. Regenerate and retest after RTL changes. Linux and Windows instructions are provided, but the recorded physical acceptance used macOS.

Build records retain their original timestamps for traceability:

- [Manifest and binary hashes](../reports/2026-10-29/build-manifest.json)
- [Hardware acceptance](../reports/2026-10-29/hardware-test.log), [stress test](../reports/2026-10-29/hardware-stress.log), and [GUI acceptance](../reports/2026-10-29/gui-hardware-test.log)
- [Flash verification](../reports/2026-10-29/flash.log), [host checks](../reports/2026-10-29/host-checks.log), and [native transport checks](../reports/2026-10-29/native-checks.log)
- [Timing](../reports/2026-10-29/PNR_TIMING.log), [I/O mapping](../reports/2026-10-29/PNR_IO.log), and [resource use](../reports/2026-10-29/resource-utilization-report.log)
