# Shrike Fi Enigma - Desktop GUI

## Overview

Desktop graphical user interface for the Shrike Fi Enigma machine. Provides intuitive control of the hardware Enigma implementation via USB serial connection.

## Features

- **Port Management**: Auto-detect and connect to Shrike Fi board
- **Rotor Configuration**: Select rotors I-V, set window positions and ring settings
- **Plugboard**: Configure up to 13 letter pair swaps with validation
- **Encryption/Decryption**: Process messages through hardware cipher
- **Real-time Feedback**: Window positions update after each operation
- **Settings Persistence**: Save and restore last used configuration
- **Error Handling**: Clear feedback for connection issues and validation errors

## Requirements

### Hardware
- Shrike Fi board with ESP32-S3 and FPGA
- USB cable for connection
- Working firmware (Stage 4)

### Software
- **Python**: 3.8 or later
- **Operating System**: macOS (primary), Linux, Windows (via Qt)
- **USB Drivers**: Most systems include CDC ACM drivers by default

## Installation

### 1. Install Python

macOS (using Homebrew):
```bash
brew install python3
```

Or download from: https://www.python.org/downloads/

### 2. Create Virtual Environment (Recommended)

```bash
cd desktop
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **PySide6**: Qt6 Python bindings for GUI
- **pyserial**: Serial port communication

## Usage

### Launch Application

From the `desktop` directory:

```bash
python enigma_gui.py
```

Or from project root:

```bash
python -m desktop.enigma_gui
```

### Connect to Board

1. **Select Port**: Choose your Shrike Fi board from the port dropdown
   - macOS: `/dev/cu.usbserial-*` or `/dev/cu.usbmodem*`
   - Linux: `/dev/ttyUSB*` or `/dev/ttyACM*`
   - Windows: `COM*`

2. **Click Connect**: Application will ping the board to verify connection

3. **Wait for "Connected"**: Status indicator turns green

### Configure Enigma

1. **Select Rotors**: Choose three different rotors from I-V
2. **Set Windows**: Choose starting positions (A-Z) for each rotor
3. **Set Rings**: Choose ring settings (A-Z) for each rotor
4. **Add Plugboard** (optional):
   - Click "+ Add Pair"
   - Enter two letters (e.g., "AB")
   - Pairs must be distinct (no overlaps)
   - Maximum 13 pairs

5. **Click "Apply Configuration"**: Sends settings to hardware

### Encrypt/Decrypt Messages

1. **Enter Message**: Type text in the input field
   - Only letters A-Z are processed
   - Case insensitive (normalized to uppercase)
   - Other characters are ignored

2. **Click "Encrypt" or "Decrypt"**:
   - Message processed letter by letter through hardware
   - Result appears in output field
   - Window positions update to show final state

3. **Note**: Encryption and decryption are the same in Enigma
   - To decrypt, set windows to starting position and "encrypt" the ciphertext

### Reset Board

Click "Reset Board" to return hardware to default state:
- Rotors: I II III
- Windows: A A A
- Rings: A A A
- Plugboard: empty

## Example Session

### Test Vector: AAAAA → BDZGO

1. Connect to board
2. Configuration:
   - Rotors: I, II, III
   - Windows: A, A, A
   - Rings: A, A, A
   - Plugboard: (empty)
3. Click "Apply Configuration"
4. Input: `AAAAA`
5. Click "Encrypt"
6. Output: `BDZGO`
7. Window positions: `A A E`

### With Plugboard

1. Configuration:
   - Rotors: I, II, III
   - Windows: A, A, A
   - Rings: A, A, A
   - Plugboard: AB, CD
2. Click "Apply Configuration"
3. Input: `HELLO`
4. Click "Encrypt"
5. Output will reflect plugboard substitution

## Keyboard Shortcuts

- **Ctrl+Q**: Quit application
- **Enter**: In plugboard dialog, confirms input
- **Delete/Backspace**: In plugboard list, removes selected pair

## Troubleshooting

### No Ports Found

- **Check USB Connection**: Ensure board is connected
- **Install Drivers**: Some systems need CH340/CP2102 drivers
- **Permissions**: Linux may require user in `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  # Log out and back in
  ```

### Connection Failed

- **Board Not Responding**: Check firmware is uploaded and running
- **Wrong Port**: Try different ports or click "Refresh"
- **Port in Use**: Close other serial programs (Arduino IDE, screen, minicom)
- **Baud Rate**: Application uses 115200, firmware must match

### FPGA Timeout

- **State Uncertain**: Board lost rotor state after timeout
- **Solution**: Click "Reset Board" and reconfigure
- **Prevention**: Ensure stable USB connection

### Invalid Configuration

- **Distinct Rotors**: Must choose three different rotors
- **Plugboard Conflicts**: Each letter used at most once
- **Range Errors**: Positions must be 0-25 (A-Z)

### Application Won't Start

- **Missing Dependencies**: Run `pip install -r requirements.txt`
- **Python Version**: Requires Python 3.8+, check with `python --version`
- **PySide6 Issues**: Try reinstalling: `pip install --force-reinstall PySide6`

## Configuration Files

Settings are saved in:
- **macOS/Linux**: `~/.shrike_enigma/settings.json`
- **Windows**: `C:\Users\<username>\.shrike_enigma\settings.json`

To reset settings, delete this file.

## Known Limitations

- **Hardware Required**: No software-only simulation mode
- **Serial Only**: No network or Bluetooth support
- **Sequential Processing**: Long messages process one letter at a time
- **No Undo**: Operations cannot be reversed (reset and reconfigure instead)
- **Platform Testing**: Primarily tested on macOS

## Architecture

```
enigma_gui.py          - Application entry point
main_window.py         - Qt GUI (730 lines)
enigma_model.py        - State management and validation
serial_manager.py      - USB serial communication
settings_manager.py    - Configuration persistence
requirements.txt       - Python dependencies
```

## Development

### Running from Source

```bash
git clone <repository>
cd desktop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python enigma_gui.py
```

### Code Style

- Follow PEP 8
- Type hints for public methods
- Docstrings for classes and methods
- Qt signal/slot pattern for events

## Support

For issues:
1. Check firmware is running (Stage 4)
2. Verify hardware connections
3. Review `reports/stage5-desktop.txt`
4. Check project documentation in `docs/SPEC.md`

## License

See project root LICENSE file.

## Version

1.0.0 - Initial release (Stage 5 implementation)
