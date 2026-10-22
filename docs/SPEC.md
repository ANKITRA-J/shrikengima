# Shrike Fi Enigma Implementation Specification

Version 1.0 | 22 October 2026 | Implementation handoff for an AI coding IDE

## 1 Purpose and required outcome

Build a working Enigma I demonstrator for the Vicharak Shrike Fi board. A desktop GUI sends messages and settings through USB. The ESP32 S3 and FPGA perform every message transformation on the board and return the result. The GUI displays the result and hardware status.

The FPGA must perform rotor stepping, forward and inverse rotor substitution, ring offsets and reflection. The ESP32 performs the input and output plugboard substitutions, text handling, validation and communication. This preserves the supplied design and keeps the entire cipher operation on the board. Moving the plugboard into the FPGA is an optional later improvement, subject to resource measurements.

This is an implementation specification, not a completed firmware release. The appended Python reference is an executable development oracle. It must not become the GUI's encryption backend. The supplied Verilog was reviewed as a starting design; its simulation, target synthesis, timing and operation on physical hardware are still acceptance gates.

### Mandatory requirements

- Operate through a USB cable, without Wi Fi, Bluetooth, cloud calls or a server.
- Use the FPGA for the Enigma rotor and reflector computation. Report an error if it is unavailable; never silently substitute a laptop or MCU rotor implementation.
- Support three different rotors selected from I through V, reflector B, three ring settings, three initial window positions and a validated plugboard.
- Provide encryption and decryption controls. Both invoke the same reciprocal transformation with identical initial settings.
- Blink the FPGA user LED in response to actual completed letter processing.
- Run within internal ESP32 memory. PSRAM, external sensors, keyboards, displays and extra wiring are not requirements.
- Deliver reproducible source, generated tables, meaningful tests, a real bitstream when the vendor tool is available, and exact flashing instructions.

### Component responsibilities

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Desktop GUI | Port selection, settings, message entry, output and errors | No local cipher, plugboard or rotor stepping |
| ESP32 firmware | USB protocol, plugboard, text formatting, FPGA loading and requests | No fallback rotor computation |
| FPGA | Rotor state, stepping, ring arithmetic, ROM traversal and activity LED | Processes contacts numbered 0 through 25 |
| Python reference | Generate expected values and verify development builds | Tests only; never used by the normal GUI |

Suggested defaults are implementation choices: Arduino C++ firmware, Python with PySide6 and pyserial for the desktop GUI, and Verilog 2001 for synthesizable logic. Resolve dependency versions during implementation and record them. Prioritize macOS operation, while keeping the GUI portable.

<!-- pagebreak -->

## 2 Hardware mapping and startup

Target only Shrike Fi with ESP32 S3 and the Renesas FPGA. Do not inherit RP2040 or RP2350 pin defaults. The manufacturer's documentation describes 1120 five input LUTs and the following board connections. Treat FPGA pin labels as the manufacturer's labels and verify their matching IO planner signals before producing constraints. [S1, S2]

| Board function | ESP32 GPIO | FPGA connection |
| --- | --- | --- |
| FPGA enable | 9 | EN |
| FPGA power control | 8 | PWR |
| Configuration clock | 12 | Pin 3 |
| Configuration select | 10 | Pin 4 |
| Configuration data to FPGA | 11 | Pin 5 |
| Configuration data from FPGA | 13 | Pin 6 and CONFIG role |
| MCU user LED | 21 | Separate MCU LED |
| FPGA user LED | Not applicable | GPIO16 |

Use the existing two data connections as a proposed runtime UART after configuration: ESP32 TX on GPIO11 to FPGA pin 5 as RX; FPGA pin 6 as TX to ESP32 RX on GPIO13. This is a design choice using documented connectivity, not a manufacturer supplied Enigma wiring recipe. Verify that the configuration pins can enter these runtime roles. Leave unused runtime FPGA connections as inputs unless the loader requires a documented state.

The FPGA's nominal internal clock is 50 MHz. Map the clock and enable to OSC_CLK and OSC_EN. Map LED output and enable to GPIO16_OUT and GPIO16_OE. Apply the top level synthesis attributes and output enables required by the vendor flow. Submodules do not receive external pin attributes. [S3, S4]

### Required boot sequence

1. Start USB reporting with processing unavailable. Mount the filesystem without automatically formatting it on failure.
2. Read the packaged FPGA image and verify its expected size and recorded hash. Use a maintained Shrike Fi compatible loader; inspect its source and explicit pin configuration.
3. Configure the FPGA using the documented EN, PWR and configuration sequence. Do not invent timings, active levels or configuration completion checks.
4. Release the configuration SPI peripheral and transfer pin ownership to the runtime UART. Verify that no ESP32 output opposes an FPGA output, especially on pin 6.
5. Establish the internal protocol handshake, reset logic, apply defaults and read them back. Only then advertise readiness to the GUI.

The official Arduino library README shows RP2040 defaults. Confirm ESP32 support in the actual source rather than copying that example unchanged. Record the loader revision, FPGA tool version, firmware board settings and pin mapping. [S5]

The documentation contains differing flash size guidance. Detect the user's device flash capacity before choosing partitions. Do not assume 8 MB, enable nonexistent PSRAM, or erase the board as a routine setup step. The expected MCU loading image is FPGA_bitstream_MCU.bin from the vendor build output. [S1, S4, S6]

<!-- pagebreak -->

## 3 Exact Enigma behavior

All rotor order, window and ring values use left, middle, right order. Internally A is 0 and Z is 25. The GUI may show A through Z; if it also shows numbers, label A as 01, not 00. The entry wheel is the identity mapping. Use the wide reflector B, not the naval thin B reflector. [S7]

| Rotor | ID | Forward wiring | Pre step turnover letter |
| --- | --- | --- | --- |
| I | 0 | EKMFLGDQVZNTOWYHXUSPAIBRCJ | Q |
| II | 1 | AJDKSIRUXBLHWTMCQGZNPYFVOE | E |
| III | 2 | BDFHJLCPRTXVZNYEIWGAKMUSQO | V |
| IV | 3 | ESOVPZJAYQUIRHXLNFTGKDCMWB | J |
| V | 4 | VZBRGITYUPSDNHLXAWMJQOFECK | Z |

Reflector B wiring is `YRUHQSLDPXNGOKMIEBFZCWVJAT`. Generate inverse rotor mappings from the forward permutations. Check each rotor is a permutation and the reflector is an involution without fixed points.

### Stepping and the signal path

Evaluate both notch conditions from the old window positions. Advance before processing each letter. The left rotor moves if the middle rotor is at its turnover letter; the middle moves if either middle or right is at its turnover letter; the right always moves. Advance any rotor at most once per letter. This includes the middle rotor's double step. [S8]

```text
middle_at_notch = old_middle == turnover[middle_rotor]
right_at_notch  = old_right  == turnover[right_rotor]
left   = (old_left   + middle_at_notch) mod 26
middle = (old_middle + (middle_at_notch OR right_at_notch)) mod 26
right  = (old_right + 1) mod 26
```

For each rotor pass, use `s = (window - ring) mod 26` and `out = (table[(in + s) mod 26] - s) mod 26`. With window positions represented as displayed letters, ring settings affect electrical offsets, not the displayed turnover letter. Do not subtract the ring a second time in the notch comparison. [S8]

The board applies the input plugboard, right forward rotor, middle forward rotor, left forward rotor, reflector B, left inverse rotor, middle inverse rotor, right inverse rotor and output plugboard, in that order.

### Text and message boundaries

Accept ASCII printable characters plus tab, LF and CR. Convert ASCII a through z to uppercase on the ESP32. Transform only letters. Preserve other accepted characters without moving the rotors. Reject non ASCII and other controls before any letter is processed. Preserving punctuation is a user interface convention rather than a historical keyboard feature.

Allow 0 through 13 disjoint plugboard pairs; an empty list is the identity mapping. Reject self pairs, repeated letters, reversed duplicates and malformed pairs. Each Process request begins at the saved initial windows, including repeated submissions. Store final FPGA windows separately for display. Encryption followed by decryption requires the same initial settings; the final windows are not the decryption starting key.

<!-- pagebreak -->

## 4 Reuse assessment and FPGA contract

The useful portions of the supplied code are its standard wiring data, reference algorithm, generated inverse tables, seeded expected vectors, modular arithmetic helpers and one shared ROM traversed by a sequential core. Retain those ideas. The source is incomplete rather than ready to flash.

| Supplied item | Action before use |
| --- | --- |
| Python reference | Retain algorithm; add setting and plugboard validation and explicit ASCII behavior |
| ROM generator | Retain deterministic generation; create output directories and add a main guard |
| ROM case key | Keep nine bits: 3 rotor bits plus 1 direction bit plus 5 contact bits |
| Sequential core | Add reset, configuration locking, invalid input handling and assertions |
| UART modules | Add reset, framing checks, parameter validation and simulation |
| Testbench generator | Compare windows after every letter; use a failing exit status for mismatches and timeout |
| Shell setup | Use relative project paths and preserved line breaks; omit failed setup and cleanup commands |

Do not retain the claim that the whole selectable ROM costs only a handful of LUTs. A single 26 entry fixed table differs from a ROM selected by rotor ID, direction and contact. Resource use must come from target synthesis and placement. Generated tests are not evidence of an executed simulation.

### Core interface

Preserve `clk`, `start`, `letter[4:0]`, `cfg_we`, `cfg_addr[3:0]`, `cfg_data[4:0]`, `busy`, `done`, `result[4:0]` and three window outputs. Add synchronous active high `rst`. A start is accepted only while idle, with no configuration write and a letter in 0 through 25. `done` pulses once; the result stays stable until the next successful result or reset. A start while busy must not step or queue another letter.

| Configuration address | Value | Valid range |
| --- | --- | --- |
| 0 through 2 | Rotor IDs in left middle right order | 0 through 4, distinct |
| 3 through 5 | Window positions in left middle right order | 0 through 25 |
| 6 through 8 | Ring settings in left middle right order | 0 through 25 |

The protocol wrapper validates all nine configuration values before applying writes. Hold its processing lock until the last write completes. The leaf core accepts writes only while idle and checks each field range; the wrapper enforces the three rotor uniqueness rule across the complete update. Invalid requests preserve the old configuration.

Reset establishes I II III, windows AAA, rings AAA, idle state, cleared result, `busy=0` and `done=0`. It must also reset UARTs, packet parser, counters and response state. Establish a target supported power on reset path. A reset input on a module does not by itself establish deterministic physical startup; validate the tool's register initialization or documented reset source.

Retain the compact sequential datapath. Measure latency with a testbench, using a 64 clock acceptance bound for the core. Drive an approximately 80 ms retriggerable LED pulse from actual core completion. At nominal 50 MHz this requires 4,000,000 clocks and a 22 bit counter. Continuous text may keep the LED lit until the last pulse expires.

<!-- pagebreak -->

## 5 Internal board protocol

Use a dedicated ESP32 hardware UART and FPGA UART at 115200 baud, 8 data bits, no parity and one stop bit. At nominal 50 MHz, CLKS_PER_BIT is 434. Keep the divisor configurable and validate actual clock tolerance on hardware.

The following compact packet format is a proposed interface to implement, not existing functionality. One request may be outstanding. The firmware waits for a valid matching response before sending another request.

| Frame | Byte order |
| --- | --- |
| Request | A5, version, sequence, opcode, length, payload, CRC |
| Response | 5A, version, sequence, opcode OR 80, length, status, data, CRC |

All fixed fields are one byte and hexadecimal constants are shown without a prefix. Version is 01. Length counts only payload bytes; response length includes the status byte. Request length is at most 9 and response length at most 10. CRC excludes the first marker byte and the CRC itself. Use CRC 8 polynomial 07, initial value 00, no reflection and no final XOR. Its check value for ASCII `123456789` is F4.

### Commands and responses

| Opcode | Request payload | Successful response data after status |
| --- | --- | --- |
| 01 PING | Empty | ASCII ENG followed by protocol version byte 01 |
| 02 CONFIG | Nine values in configuration address order | Three current window values |
| 03 TRANSFORM | One contact value 0 through 25 | Result contact then three final window values |
| 04 READ_STATE | Empty | Nine configuration values in address order |
| 05 RESET | Empty | Three default window values |

Status 00 means success, 01 invalid length or value, 02 busy, 03 unknown opcode and 04 internal failure. Reply data is empty on nonzero status. For each complete CRC valid packet, validate version, opcode, length and values before any state changes. Drop invalid CRC, invalid version, overlength and framing damaged packets without acting. Abort an incomplete packet after a 10 ms interbyte gap and resume marker search. A marker inside a declared payload is ordinary data.

Ensure UART RX checks the stop bit, resynchronizes after a break and emits a framing error indication. Synchronize asynchronous RX with two flip flops. Size baud counters from supported parameters, or explicitly reject unsupported divisors. A transmitter start while busy is not a queued byte; the response serializer must honor `busy` for every byte.

The firmware uses incrementing eight bit sequence values. Set a 100 ms response deadline per transaction. On missing, corrupt, mismatched or impossible TRANSFORM responses, stop the job and mark rotor state uncertain. Do not automatically replay a letter, because the FPGA may already have stepped. Reinitialize the link and reapply the complete initial configuration before a user requested restart. Timing out and silently using a software result is prohibited.

<!-- pagebreak -->

## 6 USB API

Use newline delimited UTF 8 JSON over the selected USB serial endpoint. ASCII message restrictions are enforced after parsing. Each request is one JSON object with an integer ID from 0 through 65535 and a command. Permit only one outstanding request. Ignore JSON object key order and use explicit schema validation.

Set a 4096 byte maximum JSON line excluding its LF delimiter and a 512 byte maximum decoded message. These bounds allow an escaped 512 character ASCII message plus settings. A two second gap in a partial line discards it and produces a structured error. After overlength input, discard through the next LF before parsing again. Reject unknown fields and wrong types. A JSON boolean is not an acceptable integer ID.

### Operations

| Command | Required request fields beyond id and cmd | Effect |
| --- | --- | --- |
| hello | None | Return versions, readiness, limits and capability fpga_enigma |
| configure | rotors, positions, rings, plugs | Validate and apply complete settings; store initial windows |
| process | mode and text | mode is encrypt or decrypt; process from saved initial settings |
| status | None | Return settings, ready state and last FPGA window readback |
| reset | None | Restore I II III, AAA, AAA and empty plugboard |
| selftest | None | Run board vectors through FPGA; restore saved initial settings afterward |

The examples below wrap for readability. On USB, serialize each request as one JSON line followed by LF.

```json
{"id":1,"cmd":"configure","rotors":["I","II","III"],
 "positions":"AAA","rings":"AAA","plugs":[]}
{"id":2,"cmd":"process","mode":"encrypt","text":"AAAAA"}
```

The following successful response is an expected API example, not a captured hardware result. For the second request it must be:

```json
{"id":2,"ok":true,"result":"BDZGO",
 "initial_positions":"AAA","final_positions":"AAF",
 "letters_processed":5,"engine":"fpga_enigma"}
```

Every response includes the matching `id` and boolean `ok`. A failure contains an `error` object with `code` and `message`. Use `id:null` when a request ID cannot be recovered. Define at least BAD_JSON, INVALID_REQUEST, INVALID_SETTINGS, INVALID_TEXT, TOO_LONG, NOT_READY, BUSY, FPGA_TIMEOUT, FPGA_PROTOCOL and SELFTEST_FAILED. Error responses must not masquerade as successful empty outputs.

### Message execution

Validate the entire request and message first. Build a temporary plugboard map and commit it only after successful FPGA configuration. Before Process, reapply saved initial settings; for each letter, apply the MCU plugboard, request the FPGA transformation, apply the MCU plugboard again and append the returned character. Preserve accepted nonletters. Return success only after all letters and final state are confirmed.

On midmessage failure, discard the incomplete output from normal result display and report processed letter count and uncertain state in the error details. Require recovery before another job. Return empty input successfully with zero letters and unchanged initial windows. Serialize processing, settings changes, reset and selftest. Keep diagnostic output separate from the JSON channel, and never log message text by default.

<!-- pagebreak -->

## 7 Firmware and desktop application

### ESP32 firmware

Keep board pins, loader adaptation, internal protocol, plugboard and USB command handling in separate modules. Initialize no wireless networking. Use fixed limits and bounded buffers rather than retaining arbitrary message histories. Never block waiting indefinitely for a USB connection or FPGA response. Keep request parsing and watchdog handling responsive during long jobs.

The plugboard is a 26 element byte array initialized to identity. For each validated pair, assign both directions. Validate disjoint letters before committing. The input to the FPGA is already plugboard mapped; the FPGA response receives the second mapping on the MCU. The GUI must not perform either substitution.

Store only firmware, FPGA image and image metadata persistently. Default to volatile message contents and settings. File export is initiated explicitly in the GUI. Do not require the laptop to upload an FPGA image on each message: normal boot loads the packaged image from board storage.

The board selftest must send actual requests through the FPGA link. It checks known ciphertext, double stepping and state readback. Restore the user's saved settings at their initial windows, even after a successful selftest. If restoration fails, remain unavailable.

### Desktop GUI

Build a local Python desktop application using PySide6 and pyserial. The main window includes a serial port selector with refresh and connect controls; three distinct rotor selectors; ring and initial window fields; plugboard pairs; input and output panes; Encrypt and Decrypt actions; Copy result; Reset to initial settings; Restore defaults; and a hardware selftest action.

Show saved initial windows separately from the final windows reported by the board. Label the selected engine and readiness based on the board handshake. Display connection failure, missing FPGA, invalid settings and timeout messages near the relevant controls. A spinner may indicate a pending job; do not fabricate perletter progress or animate rotor changes that were not returned by the board.

Use a worker thread or asynchronous serial worker so port operations and message processing never freeze the UI. Disable conflicting actions while a request is in progress. Clear or visibly invalidate stale output when a new job fails. A disconnect during processing changes the display to unavailable and requires a fresh handshake before reuse.

The normal GUI must not import the reference model. A transport mock is allowed only in automated tests. Do not ship a demo mode that displays locally generated ciphertext as a board result. Preserve typed text when a port disconnects so the user can reconnect and explicitly rerun it.

### User flow

Connect the board, open the application, choose the serial port and connect. After hardware readiness is confirmed, apply settings and process a message. To decrypt, retain the same rotor order, rings, plugs and initial windows, paste the ciphertext and press Decrypt. The board starts each submission from those initial windows automatically.

<!-- pagebreak -->

## 8 Repository and implementation order

Use a relative project root named `enigma_shrike`. Do not depend on `/home/claude` or another machine's absolute paths. Preserve normal source line breaks; the pasted one line shell history is not an installation script.

| Path under project root | Required contents |
| --- | --- |
| docs/SPEC.md | This specification and any documented changes |
| reference/enigma_ref.py | Appendix A oracle and development checks |
| tools/gen_fpga_files.py | Deterministic ROM and test vector generation |
| fpga/rtl | Core, ROM, UARTs, packet wrapper, reset and LED logic |
| fpga/sim | Core, UART and protocol testbenches |
| fpga/project | Vendor project and explicit IO mappings |
| firmware/enigma_shrike | Arduino sketch, board configuration and firmware modules |
| firmware/enigma_shrike/data | Real MCU loading image and its manifest |
| desktop | GUI, serial client and pinned dependency manifest |
| tests | Reference, firmware logic and desktop transport tests |
| reports | Commands, results, synthesis use, timing and hardware evidence |

### Stage 1 Reference and baseline

Create the reference from Appendix A, run its checks, generate inverse wiring and fixed expected vectors, and establish a clean source layout. Record that this verifies the oracle only. Preserve useful supplied HDL in version history before editing it.

### Stage 2 Core verification

Add reset and guards to the sequential core, then compare every ciphertext and window transition against the oracle. Exercise simultaneous notches, wraparound and non A rings. Gate all mismatches and timeouts with nonzero simulator exit status. Do not start GUI polishing while the core remains unverified.

### Stage 3 Board transport and synthesis

Implement the UART framing and request wrapper. Test complete packets before adding the vendor top. Synthesize and place the actual target project; save resource and timing reports. If it exceeds capacity, optimize the shared ROM and control first. Do not remove the FPGA computation to claim a fit. Generate a real bitstream only with the vendor toolchain.

### Stage 4 Firmware integration

Confirm the user's board revision, detected flash size and loader. Load the image, release configuration pins and establish PING and READ_STATE. Add plugboard and USB operations, then run known vectors through the physical board. Capture the result and final windows.

### Stage 5 Desktop handoff

Build the GUI against the USB contract, test failure paths and provide one documented launch command from a clean environment. Write firmware upload, filesystem upload, vendor project build and hardware demonstration instructions. If a required vendor tool or physical board is unavailable, complete the independent source and tests and label the remaining verification steps explicitly. Never fabricate an image or a passing report.

<!-- pagebreak -->

## 9 Verification and definition of done

These checks protect cipher correctness and stateful hardware behavior. UI styling alone does not require a separate test suite. Compare both letters and windows; a reciprocal implementation can still be historically wrong if both directions share the same error.

| Area | Required evidence |
| --- | --- |
| Known vectors | I II III, AAA rings and windows, no plugs: AAAAA gives BDZGO and HELLOWORLD gives ILBDAAMTAZ |
| Double stepping | Start ADU with I II III; successive windows are ADV, AEW, BFX, BFY |
| Ring handling | Non A rings change substitution while preserving the specified displayed turnover conditions |
| Rotor options | Cover all 60 distinct orders from I through V with deterministic randomized settings |
| Plugboard | Valid round trips and rejection of AA, AB plus AC, AB plus BA, malformed and non ASCII pairs |
| Boundaries | Z wraps to A; empty and punctuation only messages do not step; lowercase normalizes on board |
| Core handshake | Start while busy, start plus configuration write, invalid contacts and reset during work cannot duplicate a step |
| UART | Back to back bytes, start glitches, invalid stop bits, break recovery and supported clock and baud tolerance |
| Packet wrapper | Bad CRC, version, length, opcode and truncated frames cause no unintended configuration or stepping |
| USB and GUI | Oversize input, malformed JSON, timeout and disconnect produce visible errors without fallback ciphertext |
| Board startup | Image load, pin ownership change, PING and settings readback before readiness |
| Target build | Successful synthesis, placement and timing, with actual LUT and register use recorded |

Add a watchdog timeout to each simulation. Use `$fatal(1, ...)` or an equivalent failing simulator exit for mismatches and timeouts, rather than printing FAIL and ending successfully. Check rotor positions after every accepted letter. Exhaustively verify forward followed by inverse wiring for all five rotors and all 26 contacts.

At minimum, run deterministic round trip checks across all 60 rotor orders in the reference and FPGA comparison tests. Vary positions, rings, messages and plugboard settings across the integration checks. Ensure the test generator cannot import or execute the oracle through the normal GUI path.

### Physical demonstration

Show the USB GUI connected to the actual board, encrypt AAAAA to BDZGO, decrypt it back from the same initial settings, and show an observable FPGA activity LED response. Repeat with a valid nonempty plugboard and non A rings. Show that an unavailable FPGA or disconnected USB cable produces an error and no new successful output. Record device versions and commands alongside the result.

Final delivery includes the complete source repository, generated ROM and vectors, passing test logs for checks actually run, vendor project and pin mappings, actual synthesis and timing results, firmware and filesystem setup steps, GUI launch steps and hardware observations. Clearly identify any unexecuted physical or vendor tool checks. A source only delivery must not be described as tested on the board.

<!-- pagebreak -->

## Appendix A Reusable Python reference

Save the following block as `reference/enigma_ref.py`. It retains the useful supplied model while enforcing the specified input rules. This code is for verification and generation only. The normal application must communicate with the board for processing.

```python
"""Development oracle for Enigma I. Not a desktop processing backend."""
from itertools import permutations
import random

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ROTOR_ORDER = ("I", "II", "III", "IV", "V")
ROTORS = {
    "I": ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II": ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV": ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V": ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"

def letters(value, length):
    if not isinstance(value, str) or len(value) != length:
        raise ValueError("incorrect setting length")
    if any(c not in ALPHABET + ALPHABET.lower() for c in value):
        raise ValueError("settings must contain ASCII letters")
    value = value.upper()
    return [ord(c) - 65 for c in value]

def normalize(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if any(not (32 <= ord(c) <= 126 or c in "\t\n\r") for c in text):
        raise ValueError("unsupported character")
    return text.upper()

class Enigma:
    def __init__(self, rotors=("I", "II", "III"),
                 pos="AAA", ring="AAA", plugs=()):
        if (len(rotors) != 3 or any(r not in ROTORS for r in rotors)
                or len(set(rotors)) != 3):
            raise ValueError("select three distinct rotors I through V")
        self.pos, self.ring = letters(pos, 3), letters(ring, 3)
        self.fw = [[ord(c) - 65 for c in ROTORS[r][0]] for r in rotors]
        self.bw = []
        for wiring in self.fw:
            inverse = [0] * 26
            for i, output in enumerate(wiring):
                inverse[output] = i
            self.bw.append(inverse)
        self.notch = [ord(ROTORS[r][1]) - 65 for r in rotors]
        self.ref = [ord(c) - 65 for c in REFLECTOR_B]
        if not isinstance(plugs, (list, tuple)) or len(plugs) > 13:
            raise ValueError("plugboard must be a list of at most 13 pairs")
        self.plug, used = list(range(26)), set()
        for pair in plugs:
            a, b = letters(pair, 2)
            if a == b or a in used or b in used:
                raise ValueError("plugboard pairs must be disjoint")
            used.update((a, b))
            self.plug[a], self.plug[b] = b, a

    def step(self):
        middle = self.pos[1] == self.notch[1]
        right = self.pos[2] == self.notch[2]
        if middle:
            self.pos[0] = (self.pos[0] + 1) % 26
        if middle or right:
            self.pos[1] = (self.pos[1] + 1) % 26
        self.pos[2] = (self.pos[2] + 1) % 26

    def _pass(self, contact, slot, table):
        shift = self.pos[slot] - self.ring[slot]
        return (table[slot][(contact + shift) % 26] - shift) % 26

    def letter(self, ch):
        if not isinstance(ch, str) or len(ch) != 1 or ch not in ALPHABET:
            raise ValueError("letter must be one uppercase ASCII letter")
        self.step()
        contact = self.plug[ord(ch) - 65]
        for slot in (2, 1, 0):
            contact = self._pass(contact, slot, self.fw)
        contact = self.ref[contact]
        for slot in (0, 1, 2):
            contact = self._pass(contact, slot, self.bw)
        return chr(self.plug[contact] + 65)

    def text(self, text):
        text = normalize(text)  # validate the whole message before stepping
        return "".join(self.letter(c) if c in ALPHABET else c for c in text)

    def window(self):
        return "".join(chr(p + 65) for p in self.pos)
```

<!-- pagebreak -->

## Appendix A Reference checks

Append these checks to the same file. Do not run Python with optimization enabled for this assert based development check. Use an ordinary test runner with explicit failures in the implemented repository.

```python
def selftest():
    assert Enigma().text("AAAAA") == "BDZGO"
    assert Enigma().text("BDZGO") == "AAAAA"
    assert Enigma().text("HELLOWORLD") == "ILBDAAMTAZ"
    machine = Enigma(pos="ADU")
    windows = []
    for _ in range(4):
        machine.letter("A")
        windows.append(machine.window())
    assert windows == ["ADV", "AEW", "BFX", "BFY"]
    machine = Enigma()
    assert machine.text(" \t123!?\n") == " \t123!?\n"
    assert machine.window() == "AAA"
    assert Enigma().text("aaaaa") == "BDZGO"
    rng = random.Random(1941)
    for order in permutations(ROTOR_ORDER, 3):
        pos = "".join(rng.choices(ALPHABET, k=3))
        ring = "".join(rng.choices(ALPHABET, k=3))
        message = "".join(rng.choices(ALPHABET + " !123", k=100))
        settings = dict(rotors=order, pos=pos, ring=ring,
                        plugs=("AB", "CD", "EF", "GH"))
        cipher = Enigma(**settings).text(message)
        assert Enigma(**settings).text(cipher) == message
    for plugs in (("AA",), ("AB", "AC"), ("AB", "BA"), ("A1",)):
        try:
            Enigma(plugs=plugs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid plugs accepted")
    machine = Enigma()
    try:
        machine.text("A\u00e9")
    except ValueError:
        assert machine.window() == "AAA"
    else:
        raise AssertionError("non ASCII message accepted")
    for wiring, _ in ROTORS.values():
        assert sorted(wiring) == list(ALPHABET)
    for i, ch in enumerate(REFLECTOR_B):
        j = ord(ch) - 65
        assert j != i and ord(REFLECTOR_B[j]) - 65 == i
    print("Reference checks passed for all 60 rotor orders")

if __name__ == "__main__":
    selftest()
```

Run `python3 reference/enigma_ref.py` from the project root. The oracle's seeded round trips help expose implementation errors but do not independently prove historical accuracy. Preserve the fixed known vectors and the documented wiring and stepping convention as separate checks.

<!-- pagebreak -->

## Appendix B Reusable ROM generation

Save this block as `tools/gen_fpga_files.py`. It preserves the supplied nine bit key and deterministic table generation, creates the output directory and avoids work on import. The IDE must separately implement the expanded test vector generator specified in Section 9.

```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
from enigma_ref import ROTORS, ROTOR_ORDER, REFLECTOR_B

def generate():
    out = ROOT / "fpga" / "rtl"
    out.mkdir(parents=True, exist_ok=True)
    lines = [
        "// Generated by tools/gen_fpga_files.py",
        "module rotor_rom (input [2:0] rotor, input inv,",
        "  input [4:0] x, output reg [4:0] y);",
        "always @(*) begin",
        "  case ({rotor, inv, x})",
    ]
    for rid, name in enumerate(ROTOR_ORDER):
        forward = [ord(c) - 65 for c in ROTORS[name][0]]
        inverse = [0] * 26
        for i, value in enumerate(forward):
            inverse[value] = i
        for direction, table in enumerate((forward, inverse)):
            for x, y in enumerate(table):
                key = (rid << 6) | (direction << 5) | x
                lines.append(f"    9'd{key}: y = 5'd{y};")
    for x, ch in enumerate(REFLECTOR_B):
        key = (5 << 6) | x
        lines.append(f"    9'd{key}: y = 5'd{ord(ch) - 65};")
    lines += ["    default: y = 5'd0;", "  endcase", "end", "endmodule"]
    target = out / "rotor_rom.v"
    target.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(target.relative_to(ROOT))

if __name__ == "__main__":
    generate()
```

Run `python3 tools/gen_fpga_files.py`. Valid keys comprise 260 rotor entries plus 26 reflector entries. The default branch is only a combinational assignment to avoid latches; it does not make invalid requests valid. Guard all external inputs and verify that internal ROM selections remain in range. Never mask a bad packet by treating it as an identity substitution.

Retain the supplied `inc26`, `add26` and `sub26` arithmetic approach with widened intermediate sums. Their precondition is that operands are 0 through 25. Exhaustively compare all 676 input pairs against software modulo arithmetic. Do not replace these with general division hardware without measuring target synthesis.

<!-- pagebreak -->

## Appendix C IDE execution instruction

Use the following instruction with this complete Markdown file in the project context:

```text
Implement the Shrike Fi Enigma project described in this specification.
Read the requirements and hardware verification gates before writing code.
Reuse the appended reference and ROM generator and the useful sequential
datapath design from the supplied source. Correct the documented gaps.

Keep all production message processing on the board. The FPGA must do rotor
stepping, ring offsets, rotor substitution and reflection. The ESP32 must do
plugboard substitution and USB handling. The desktop GUI only communicates
with the board and displays its replies. Do not add a software fallback.

Work through the implementation stages in order. Run meaningful checks for
each stage, record the commands and results, and continue all work that can
be completed with the available tools. Verify the real board mapping and
loader rather than copying RP2040 defaults. Do not invent vendor APIs,
bitstreams, utilization numbers, passing simulations or hardware results.

Deliver a complete repository, usable GUI, firmware, FPGA source and vendor
project, reproducible generated tables, test evidence and setup instructions.
Identify precisely which physical checks remain if hardware is unavailable.
```

### Sources and verification record

Manufacturer and technical references were checked on 22 October 2026. Source descriptions document hardware facts; protocol formats, software structure, limits and default UI choices above are project design decisions.

- **S1 Hardware overview** https://vicharak-in.github.io/shrike/hardware_overview.html
- **S2 Shrike Fi pinouts** https://vicharak-in.github.io/shrike/shrike_pinouts.html
- **S3 Vendor Verilog style guide** https://vicharak-in.github.io/shrike/verilog_style_guide.html
- **S4 Bitstream generation and IO mapping** https://vicharak-in.github.io/shrike/generating_your_first_bitstream.html
- **S5 Official Arduino loader repository** https://github.com/vicharak-in/shrike_arduino
- **S6 Getting started and programming flow** https://vicharak-in.github.io/shrike/getting_started.html
- **S7 Crypto Museum wiring tables** https://www.cryptomuseum.com/crypto/enigma/wiring.htm
- **S8 Crypto Museum working principle** https://www.cryptomuseum.com/crypto/enigma/working.htm

The user supplied the initial Python model, ROM and testbench generators, partial core and UART source. This handoff retains selected portions and defines the missing implementation.

The embedded Python checks were executed successfully, including the two known ciphertext vectors, double stepping, ASCII handling and round trips across all 60 rotor orders. Additional checks passed for non A ring turnover behavior, invalid settings, 286 distinct generated ROM entries, deterministic generation and the CRC check value. FPGA RTL simulation, target synthesis, timing and physical board checks have not been run. No bitstream or target utilization result is claimed.
