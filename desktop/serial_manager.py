"""
Serial communication manager for Shrike Fi Enigma
Handles USB serial connection to ESP32 firmware
"""

import json
import time
from typing import List, Dict, Optional, Tuple
import serial
import serial.tools.list_ports


class SerialManager:
    """Manages USB serial communication with ESP32 firmware"""
    
    def __init__(self):
        self.port: Optional[serial.Serial] = None
        self.port_name: str = ""
        self.timeout: float = 2.0  # 2 second timeout for responses
        
    def list_ports(self) -> List[Tuple[str, str]]:
        """
        List available serial ports
        Returns: List of (port_name, description) tuples
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            # Filter for likely ESP32 devices
            desc = port.description or ""
            if port.device:
                ports.append((port.device, desc))
        return ports
    
    def connect(self, port_name: str, baud: int = 115200) -> Tuple[bool, str]:
        """
        Connect to serial port
        Returns: (success, message)
        """
        try:
            self.port = serial.Serial(
                port=port_name,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.port_name = port_name
            
            # Clear any garbage in buffers
            time.sleep(0.5)
            self.port.reset_input_buffer()
            self.port.reset_output_buffer()
            
            # Test connection with ping
            success, result = self.ping()
            if success:
                return True, f"Connected to {port_name}"
            else:
                self.disconnect()
                return False, f"Board not responding: {result}"
                
        except serial.SerialException as e:
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disconnect(self):
        """Close serial connection"""
        if self.port and self.port.is_open:
            self.port.close()
        self.port = None
        self.port_name = ""
    
    def is_connected(self) -> bool:
        """Check if connected to board"""
        return self.port is not None and self.port.is_open
    
    def send_command(self, cmd: dict) -> Tuple[bool, Dict]:
        """
        Send JSON command and receive response
        Returns: (success, response_dict)
        """
        if not self.is_connected():
            return False, {"error": "Not connected"}
        
        try:
            # Send command as JSON + newline
            cmd_str = json.dumps(cmd) + "\n"
            self.port.write(cmd_str.encode('utf-8'))
            self.port.flush()
            
            # Read response line
            response_line = self.port.readline().decode('utf-8').strip()
            
            if not response_line:
                return False, {"error": "No response from board (timeout)"}
            
            # Parse JSON response
            try:
                response = json.loads(response_line)
                
                # Check for error status
                if response.get("status") == "error":
                    return False, response
                
                return True, response
                
            except json.JSONDecodeError:
                return False, {"error": f"Invalid JSON response: {response_line}"}
                
        except serial.SerialException as e:
            self.disconnect()
            return False, {"error": f"Serial error: {str(e)}"}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def ping(self) -> Tuple[bool, Dict]:
        """
        Send PING command to verify connection
        Returns: (success, response)
        """
        return self.send_command({"cmd": "ping"})
    
    def configure(self, rotors: List[int], windows: List[int], 
                  rings: List[int], plugboard: List[str] = None) -> Tuple[bool, Dict]:
        """
        Configure Enigma settings
        
        Args:
            rotors: [left, middle, right] rotor IDs (0-4)
            windows: [left, middle, right] positions (0-25)
            rings: [left, middle, right] ring settings (0-25)
            plugboard: List of pairs like ["AB", "CD"] (optional)
        
        Returns: (success, response)
        """
        cmd = {
            "cmd": "config",
            "rotors": rotors,
            "windows": windows,
            "rings": rings
        }
        
        if plugboard:
            cmd["plugboard"] = plugboard
        
        return self.send_command(cmd)
    
    def encrypt(self, message: str) -> Tuple[bool, Dict]:
        """
        Encrypt a message
        Returns: (success, response with 'result' and 'windows')
        """
        cmd = {
            "cmd": "encrypt",
            "message": message
        }
        return self.send_command(cmd)
    
    def decrypt(self, message: str) -> Tuple[bool, Dict]:
        """
        Decrypt a message (same as encrypt in Enigma)
        Returns: (success, response with 'result' and 'windows')
        """
        cmd = {
            "cmd": "decrypt",
            "message": message
        }
        return self.send_command(cmd)
    
    def reset(self) -> Tuple[bool, Dict]:
        """
        Reset board to default state
        Returns: (success, response)
        """
        return self.send_command({"cmd": "reset"})
    
    def get_status(self) -> Tuple[bool, Dict]:
        """
        Get board status
        Returns: (success, response with 'ready', 'state_certain', 'windows')
        """
        return self.send_command({"cmd": "status"})
