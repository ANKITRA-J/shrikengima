"""Single-outstanding-request client for the FPGA USB API in docs/SPEC.md."""
import json
import time
import serial
import serial.tools.list_ports


class SerialManager:
    ROTORS = ("I", "II", "III", "IV", "V")

    def __init__(self):
        self.port = None
        self.port_name = ""
        self.timeout = 2.0
        self.next_id = 0

    def list_ports(self):
        return [(p.device, p.description or "") for p in serial.tools.list_ports.comports() if p.device]

    def connect(self, port_name, baud=115200):
        try:
            self.port = serial.Serial(port_name, baudrate=baud, timeout=0.1, write_timeout=2)
            self.port_name = port_name
            # Opening USB CDC may reset the MCU. Allow bounded boot time.
            deadline = time.monotonic() + 10
            result = {"error": "Board startup timed out"}
            while time.monotonic() < deadline:
                success, result = self.ping()
                if success and result.get("ready") is True and result.get("engine") == "fpga_enigma":
                    return True, f"Connected to {port_name} (FPGA verified)"
                time.sleep(0.2)
            self.disconnect()
            return False, result.get("error", "FPGA not ready: " + result.get("loader_status", "") + "; " + result.get("selftest_status", ""))
        except (serial.SerialException, OSError) as exc:
            self.disconnect()
            return False, str(exc)

    def disconnect(self):
        if self.port is not None:
            self.port.close()
        self.port = None
        self.port_name = ""

    def is_connected(self):
        return self.port is not None and self.port.is_open

    def send_command(self, cmd):
        if not self.is_connected():
            return False, {"error": "Not connected"}
        request_id = self.next_id
        self.next_id = (self.next_id + 1) % 65536
        request = dict(cmd, id=request_id)
        wire = json.dumps(request, ensure_ascii=True).encode("ascii")
        if len(wire) > 4096:
            return False, {"error": "JSON line exceeds 4096 bytes"}
        # Worst case: 512 FPGA transactions, each bounded by 100 ms.
        timeout = 55 if cmd["cmd"] == "process" else 10 if cmd["cmd"] == "selftest" else self.timeout
        try:
            self.port.write(wire + b"\n")
            deadline = time.monotonic() + timeout
            buffer = bytearray()
            while time.monotonic() < deadline:
                chunk = self.port.read(1)
                if not chunk:
                    continue
                buffer.extend(chunk)
                if len(buffer) > 8192:
                    raise ValueError("Oversize board response")
                if chunk != b"\n":
                    continue
                response = json.loads(buffer.decode("utf-8"))
                buffer.clear()
                if not isinstance(response, dict):
                    raise ValueError("Board response must be an object")
                if type(response.get("id")) is not int or response["id"] != request_id:
                    continue  # Stale response from an earlier request; never display it.
                if type(response.get("ok")) is not bool:
                    raise ValueError("Missing boolean ok in response")
                if not response["ok"]:
                    error = response.get("error", {})
                    return False, {"error": error.get("message", "Board error") if isinstance(error, dict) else str(error), "details": error}
                if cmd["cmd"] == "process":
                    if response.get("engine") != "fpga_enigma" or not isinstance(response.get("result"), str):
                        raise ValueError("Invalid FPGA result")
                if "final_positions" in response:
                    positions = response["final_positions"]
                    if not isinstance(positions, str) or len(positions) != 3 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in positions):
                        raise ValueError("Invalid final positions")
                    response["windows"] = [ord(c)-65 for c in positions]
                return True, response
            raise TimeoutError("Board response timed out; reconnect and reapply settings")
        except (serial.SerialException, OSError, ValueError, TimeoutError) as exc:
            self.disconnect()
            return False, {"error": str(exc)}

    def ping(self):
        return self.send_command({"cmd": "hello"})

    def configure(self, rotors, windows, rings, plugboard=None):
        return self.send_command({"cmd": "configure", "rotors": [self.ROTORS[i] for i in rotors],
                                  "positions": ''.join(chr(65+i) for i in windows),
                                  "rings": ''.join(chr(65+i) for i in rings), "plugs": plugboard or []})

    def encrypt(self, message):
        return self.send_command({"cmd": "process", "mode": "encrypt", "text": message})

    def decrypt(self, message):
        return self.send_command({"cmd": "process", "mode": "decrypt", "text": message})

    def reset(self):
        return self.send_command({"cmd": "reset"})

    def get_status(self):
        return self.send_command({"cmd": "status"})

    def selftest(self):
        return self.send_command({"cmd": "selftest"})
