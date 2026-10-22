# Stage 5 Implementation Plan: Desktop GUI Application

## Overview

Stage 5 implements the Python desktop GUI application that provides the user interface for the Shrike Fi Enigma machine. The GUI communicates with the ESP32 firmware via USB serial using JSON commands.

**Dependencies:** Stage 4 complete (ESP32 firmware with USB JSON protocol)

**Key Design Decisions:**
- **Platform**: Python 3.8+ for cross-platform compatibility (macOS priority)
- **GUI Framework**: PySide6 (Qt6) for modern, native-looking interface
- **Serial Communication**: pyserial for USB CDC connection
- **Configuration**: JSON for settings persistence
- **No local cipher**: All encryption happens on hardware
- **Responsive**: Non-blocking serial I/O with timeout handling

## Implementation Plan

- [ ] 1. **Set up Python project structure**
      
      Create desktop application directory with proper module organization.
      
      **Directory Structure:**
      ```
      desktop/
      ├── enigma_gui.py           # Main application entry point
      ├── main_window.py          # Main window UI
      ├── serial_manager.py       # USB serial communication
      ├── enigma_model.py         # State management
      ├── settings_manager.py     # Configuration persistence
      ├── requirements.txt        # Python dependencies
      ├── README.md               # User documentation
      └── assets/
          └── icon.png            # Application icon (if needed)
      ```
      
      **Files:**
      - desktop/enigma_gui.py
      - desktop/requirements.txt
      - desktop/README.md
      
      **Verify:**
      - Directory structure matches specification Section 8
      - README documents installation and usage

---

- [ ] 2. **Implement serial manager (serial_manager.py)**
      
      Handle USB serial communication with ESP32 firmware.
      
      **Requirements:**
      - Auto-detect available serial ports
      - Connect/disconnect with error handling
      - Send JSON commands
      - Receive JSON responses with timeout
      - Non-blocking operation (threaded or async)
      - Parse firmware responses
      - Handle disconnection gracefully
      
      **Interface:**
      ```python
      class SerialManager:
          def __init__(self)
          def list_ports() -> List[str]
          def connect(port: str, baud: int = 115200) -> bool
          def disconnect()
          def is_connected() -> bool
          def send_command(cmd: dict) -> dict  # Sends JSON, returns response
          def ping() -> dict
          def configure(rotors, windows, rings, plugboard) -> dict
          def encrypt(message: str) -> dict
          def reset() -> dict
          def get_status() -> dict
      ```
      
      **Error Handling:**
      - Port not found
      - Connection timeout
      - Disconnected during operation
      - Invalid response format
      - Firmware error responses
      
      **Files:**
      - desktop/serial_manager.py
      
      **Verify:**
      - Lists available ports correctly
      - Connects to ESP32 successfully
      - JSON commands sent/received properly
      - Timeouts handled gracefully

---

- [ ] 3. **Implement state management (enigma_model.py)**
      
      Manage Enigma machine state and validation rules.
      
      **State:**
      - Rotors: 3 selections from I-V (0-4)
      - Windows: 3 positions A-Z (0-25)
      - Rings: 3 settings A-Z (0-25)
      - Plugboard: List of letter pairs
      - Current message
      - Output result
      
      **Validation:**
      - Rotors must be distinct
      - Windows/rings 0-25 range
      - Plugboard: max 13 pairs, no overlaps
      - Letters A-Z only
      - No self-connections in plugboard
      
      **Interface:**
      ```python
      class EnigmaModel:
          def __init__(self)
          def set_rotors(left, middle, right) -> bool
          def set_windows(left, middle, right) -> bool
          def set_rings(left, middle, right) -> bool
          def set_plugboard(pairs: List[Tuple[str, str]]) -> bool
          def validate_configuration() -> Tuple[bool, str]
          def get_configuration() -> dict
          def reset()
      ```
      
      **Files:**
      - desktop/enigma_model.py
      
      **Verify:**
      - Validation rules match specification
      - Invalid configs rejected with clear errors
      - State updates trigger UI refresh

---

- [ ] 4. **Implement settings persistence (settings_manager.py)**
      
      Save and load user configurations.
      
      **Settings to Persist:**
      - Last used serial port
      - Last rotor configuration
      - Last plugboard settings
      - Window/ring positions (optional)
      - Window geometry and preferences
      
      **Storage:**
      - JSON file in user home directory
      - Cross-platform path handling
      - Graceful fallback if missing/corrupt
      
      **Interface:**
      ```python
      class SettingsManager:
          def __init__(self, config_path: str = None)
          def load() -> dict
          def save(settings: dict)
          def get(key: str, default=None)
          def set(key: str, value)
          def clear()
      ```
      
      **Files:**
      - desktop/settings_manager.py
      
      **Verify:**
      - Settings persist across launches
      - Corrupt files handled gracefully
      - Defaults applied when missing

---

- [ ] 5. **Implement main window UI (main_window.py)**
      
      Create the graphical user interface with Qt/PySide6.
      
      **UI Layout:**
      
      ```
      ┌─────────────────────────────────────────────┐
      │ Shrike Fi Enigma                      [_][□][×]│
      ├─────────────────────────────────────────────┤
      │ Port: [COM3 ▼] [Connect]  ● Connected       │
      ├─────────────────────────────────────────────┤
      │ Rotors:                                     │
      │   Left:   [I ▼]  Window: [A ▼]  Ring: [A ▼]│
      │   Middle: [II▼]  Window: [A ▼]  Ring: [A ▼]│
      │   Right:  [III▼] Window: [A ▼]  Ring: [A ▼]│
      │                                             │
      │ Plugboard: [AB] [CD] [+Add] [-Remove]      │
      │                                             │
      │ [Apply Configuration]                       │
      ├─────────────────────────────────────────────┤
      │ Message:                                    │
      │ ┌─────────────────────────────────────────┐│
      │ │ HELLO WORLD                             ││
      │ └─────────────────────────────────────────┘│
      │                                             │
      │ Output:                                     │
      │ ┌─────────────────────────────────────────┐│
      │ │ ILBDAAMTAZ                              ││
      │ └─────────────────────────────────────────┘│
      │                                             │
      │ [Encrypt] [Decrypt] [Clear] [Reset]        │
      ├─────────────────────────────────────────────┤
      │ Status: Ready                               │
      └─────────────────────────────────────────────┘
      ```
      
      **Components:**
      - Port selection dropdown with refresh
      - Connect/disconnect button
      - Connection status indicator
      - Rotor selection dropdowns (I-V)
      - Window position selectors (A-Z)
      - Ring setting selectors (A-Z)
      - Plugboard pair editor
      - Message input text area
      - Output display (read-only)
      - Action buttons (Encrypt/Decrypt/Clear/Reset)
      - Status bar
      
      **Behavior:**
      - Disable controls when disconnected
      - Real-time validation feedback
      - Show errors in status bar
      - Update windows after each operation
      - LED activity indicator (if supported)
      - Keyboard shortcuts (Ctrl+E for encrypt)
      
      **Files:**
      - desktop/main_window.py
      
      **Verify:**
      - UI matches specification requirements
      - All controls functional
      - Error messages clear and helpful
      - Responsive on macOS

---

- [ ] 6. **Implement main application (enigma_gui.py)**
      
      Application entry point and initialization.
      
      **Responsibilities:**
      - Initialize QApplication
      - Load settings
      - Create main window
      - Set up signal/slot connections
      - Handle application lifecycle
      - Command-line argument parsing (optional)
      
      **Launch Command:**
      ```bash
      python enigma_gui.py
      # or
      python -m desktop.enigma_gui
      ```
      
      **Files:**
      - desktop/enigma_gui.py
      
      **Verify:**
      - Application launches without errors
      - Window appears on screen
      - Settings loaded correctly
      - Clean shutdown

---

- [ ] 7. **Implement error handling and edge cases**
      
      Handle failure scenarios gracefully.
      
      **Error Scenarios:**
      - Board not connected
      - Connection lost during operation
      - Invalid firmware response
      - FPGA timeout
      - Malformed JSON
      - Oversize message input
      - Invalid rotor combinations
      - Plugboard conflicts
      
      **User Feedback:**
      - Error dialogs for critical failures
      - Status bar messages for warnings
      - Visual indicators (red text, icons)
      - Helpful error messages with solutions
      
      **Implementation:**
      - Try/except blocks around serial I/O
      - Validation before sending commands
      - Retry logic with backoff
      - Graceful degradation
      
      **Verify:**
      - Disconnect cable during encryption: shows error, doesn't crash
      - Invalid config: rejected with clear message
      - Firmware error: displayed to user
      - Timeout: handled without hanging

---

- [ ] 8. **Create user documentation**
      
      Document installation, usage, and troubleshooting.
      
      **Contents:**
      - Installation instructions (pip install)
      - Dependencies and versions
      - Launch procedure
      - USB driver requirements (if any)
      - Port selection guide
      - Configuration instructions
      - Example usage
      - Troubleshooting common issues
      - Keyboard shortcuts
      - Known limitations
      
      **Files:**
      - desktop/README.md
      - desktop/TROUBLESHOOTING.md (optional)
      
      **Verify:**
      - Instructions complete and accurate
      - Fresh user can follow and launch
      - Common issues documented

---

- [ ] 9. **Testing and validation**
      
      Test complete system integration.
      
      **Test Cases:**
      1. Port detection and connection
      2. Configuration with valid settings
      3. AAAAA → BDZGO encryption
      4. HELLOWORLD → ILBDAAMTAZ
      5. Decrypt (reverse operation)
      6. Plugboard with AB pair
      7. Reset functionality
      8. Disconnect handling
      9. Invalid input rejection
      10. Long message processing
      
      **Integration Test:**
      - Connect to actual hardware
      - Configure rotors I II III, AAA windows, AAA rings
      - Encrypt "AAAAA"
      - Verify output "BDZGO"
      - Verify windows updated to "AAE"
      - Test with plugboard
      - Verify LED pulses (if visible)
      
      **Files:**
      - tests/test_gui.py (optional)
      - tests/integration_test.md
      
      **Verify:**
      - All test cases pass
      - No crashes or hangs
      - Errors handled gracefully

---

- [ ] 10. **Document Stage 5 completion**
      
      Summarize implementation and testing results.
      
      **Contents:**
      - Module summary and file listing
      - UI screenshots (if possible)
      - Integration test results
      - Known vectors verified
      - Hardware demonstration evidence
      - Build/launch instructions
      - Known issues or limitations
      - Future enhancement ideas
      
      **Files:**
      - reports/stage5-desktop.txt
      
      **Verify:**
      - Complete system documentation
      - Hardware testing status recorded
      - Delivery checklist complete

---

## Launch Commands Reference

**Install Dependencies:**
```bash
cd desktop
pip install -r requirements.txt
```

**Run Application:**
```bash
# From desktop directory
python enigma_gui.py

# Or from project root
python -m desktop.enigma_gui

# With virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python enigma_gui.py
```

**Dependencies (requirements.txt):**
```
PySide6>=6.5.0
pyserial>=3.5
```

## UI/UX Requirements

**Visual Design:**
- Clean, professional appearance
- Consistent spacing and alignment
- Clear labels and tooltips
- Keyboard focus indicators
- Disabled state styling
- macOS native look (Qt default)

**Usability:**
- Logical tab order
- Enter key submits actions
- Escape closes dialogs
- Ctrl+Q quits application
- Status feedback for all actions
- Progress indication for long operations
- Confirmation for destructive actions

**Accessibility:**
- Keyboard navigation throughout
- Screen reader compatible (Qt handles)
- High contrast support
- Resizable text
- Clear error messages

## Known Constraints

**No Local Cipher:**
- GUI must NOT perform rotor stepping
- GUI must NOT perform letter substitution (except plugboard display)
- GUI must NOT fall back to software encryption
- All cipher operations happen on hardware

**Hardware Dependency:**
- Application requires physical Shrike Fi board
- USB connection mandatory
- No simulation mode
- Error if FPGA unavailable

**Platform:**
- macOS is priority target
- Linux/Windows support via Qt
- USB serial drivers may vary by platform
- Test on actual target platform

**Performance:**
- Serial operations may take 100ms+ per letter
- Long messages process letter-by-letter
- UI must remain responsive during operations
- Consider progress bar for long messages

## Stage 5 Success Criteria

Stage 5 is complete when:
- [x] All 6 source modules created (gui, serial, model, settings, window, main)
- [x] GUI launches and displays correctly
- [x] Port selection and connection functional
- [x] All configuration controls working
- [x] Encryption/decryption through hardware works
- [x] Error handling tested
- [x] User documentation complete
- [x] Integration test passed

Hardware demonstration (if board available):
- [ ] GUI launches from clean environment
- [ ] Connects to board via USB
- [ ] Known vector: AAAAA → BDZGO verified
- [ ] Windows update after encryption
- [ ] Plugboard functionality demonstrated
- [ ] LED activity visible
- [ ] Disconnect handled gracefully

If hardware unavailable:
- Complete GUI source code
- Document expected behavior
- Mark hardware validation as pending
- Provide mock/simulation notes

## Project Completion Checklist

After Stage 5, the complete system includes:

✓ Stage 1: Python reference oracle and ROM generator  
✓ Stage 2: FPGA Enigma core (enigma_core.v)  
✓ Stage 3: UART protocol and top-level synthesis  
✓ Stage 4: ESP32-S3 firmware  
✓ Stage 5: Desktop GUI application  

**Final Deliverables:**
1. Complete source repository
2. Generated ROM and test vectors
3. FPGA RTL and synthesis project
4. ESP32 firmware with selftest
5. Desktop GUI application
6. Build instructions for all components
7. Test evidence and reports
8. Hardware demonstration (if available)

---

**Total Steps:** 10  
**Estimated Effort:** Medium-High (GUI framework, serial I/O, integration testing)  
**Critical Path:** Serial manager (step 2) and main window (step 5)  
**Risk Areas:** Serial port detection across platforms, USB driver compatibility  
