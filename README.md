# Shrike Fi Enigma

## Clone → flash → run

Already have the Arduino tools installed? Connect your **8 MB Shrike Fi**, close Serial Monitor, and run these commands. Use Python **3.9–3.13**.

### 1. Clone

```sh
git clone https://github.com/ANKITRA-J/shrikengima.git
cd shrikengima
```

### 2. Flash the board

**If Arduino CLI is not installed:** on macOS/Linux with Homebrew, run:

```sh
brew install arduino-cli
```

Without Homebrew, use the [official Arduino CLI installer/downloads](https://docs.arduino.cc/arduino-cli/installation) (including Windows). If the ESP32 core or ArduinoJson library is also missing, follow the [one-time dependency setup](docs/BUILD_AND_USE.md#firmware-build-and-flashing).

Find your port:

```sh
arduino-cli board list
```

Replace `YOUR_PORT` below with that port, such as `/dev/cu.usbmodem1101` on macOS or `/dev/ttyACM0` on Linux:

```sh
python3 tools/build_firmware.py --bitstream firmware/enigma_shrike/data/fpga_bitstream.bin --port YOUR_PORT
```

This builds and flashes the firmware **and** the filesystem containing the included FPGA image. No Go Configure rebuild is needed. **If this Enigma firmware and FPGA image are already installed, skip flashing.**

### 3. Launch the GUI

First launch from a fresh clone:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r desktop/requirements.txt
.venv/bin/python desktop/enigma_gui.py
```

Next time, from the repository folder, just run:

```sh
.venv/bin/python desktop/enigma_gui.py
```

On macOS you can also double-click **Launch Enigma.command** after the first setup.

In the GUI, click **Refresh → choose your port → Connect**. Keep the default settings, type `HELLOWORLD`, and click **Encrypt**. The result should be **`ILBDAAMTAZ`**. Put that result into the input and click **Decrypt** with the same settings to recover your message.

<details>
<summary>Windows commands</summary>

After cloning and entering the repository folder, find your port with `arduino-cli board list`. Replace `COM5` with your actual port. Skip the flash command if the Enigma firmware and FPGA image are already installed.

```powershell
python tools/build_firmware.py --bitstream firmware/enigma_shrike/data/fpga_bitstream.bin --port COM5
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r desktop/requirements.txt
.venv\Scripts\python.exe desktop/enigma_gui.py
```

For later launches, run only the last command.

</details>

## Need help?

| Problem or question | Where to go |
| --- | --- |
| Arduino tools, board core or library missing | [Install firmware tools](docs/BUILD_AND_USE.md#firmware-build-and-flashing): Arduino CLI, ESP32 core **3.3.12**, ArduinoJson **6.21.5** |
| Python or GUI dependency error | [Desktop setup](docs/BUILD_AND_USE.md#desktop-setup). Use Python **3.9–3.13**; if your default is newer, create the environment with `python3.13 -m venv .venv`. |
| No port, busy port, or board not ready | [Troubleshooting](docs/BUILD_AND_USE.md#troubleshooting). Close other serial programs and use a USB data cable. |
| How do the rotors, rings and plugboard work? | [User guide and cipher experiments](docs/USER_GUIDE.md), also inside the GUI under **How to use Enigma** |
| Want Arduino IDE, another editor, or a new FPGA build? | [Build guide](docs/BUILD_AND_USE.md) |
| Want to check your board or review test evidence? | [Verification](docs/BUILD_AND_USE.md#repeatable-verification) and [validated results](docs/BUILD_AND_USE.md#validation-and-limitations) |

## About the project

The laptop GUI controls an Enigma simulator on the Shrike Fi. The ESP32-S3 handles USB and the plugboard; the SLG47910V FPGA performs rotor stepping, wiring and reflection. There is no software cipher fallback. The board's built-in LEDs are used; no external wiring is needed.

The included image has passed all 60 rotor orders, encryption/decryption round trips, maximum-length messages, GUI operation and extended stress tests on a physical board. The complete setup was verified on macOS; Linux and Windows instructions are provided but have not undergone the recorded hardware acceptance run.

This implements Enigma encryption/decryption. Automatic Bombe-style key cracking is not included.

<details>
<summary>Source map for developers</summary>

| Location | Purpose |
| --- | --- |
| `desktop/` | Python GUI and serial client |
| `firmware/enigma_shrike/` | MCU firmware and included FPGA image |
| `fpga/rtl/` | Authoritative FPGA source |
| `fpga/project/enigma/` | Go Configure project and constraints |
| `fpga/sim/` | RTL testbenches |
| `reference/` | Python test oracle |
| `tests/` | Host and physical-board tests |
| `tools/` | Build, generation and test scripts |
| `reports/` | Binary hashes and verification evidence |

</details>
