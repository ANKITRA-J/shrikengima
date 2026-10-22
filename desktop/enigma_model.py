"""
Enigma machine state model and validation
"""

from typing import List, Tuple, Optional


class EnigmaModel:
    """Manages Enigma configuration state and validation"""
    
    # Rotor names
    ROTOR_NAMES = ["I", "II", "III", "IV", "V"]
    
    def __init__(self):
        # Configuration
        self.rotor_left: int = 0    # Rotor I
        self.rotor_middle: int = 1  # Rotor II
        self.rotor_right: int = 2   # Rotor III
        
        self.window_left: int = 0   # A
        self.window_middle: int = 0  # A
        self.window_right: int = 0   # A
        
        self.ring_left: int = 0     # A
        self.ring_middle: int = 0   # A
        self.ring_right: int = 0    # A
        
        self.plugboard: List[Tuple[str, str]] = []  # List of letter pairs
        
        # Messages
        self.input_message: str = ""
        self.output_message: str = ""
    
    def set_rotors(self, left: int, middle: int, right: int) -> Tuple[bool, str]:
        """Set rotor selection"""
        # Validate range
        if not (0 <= left <= 4 and 0 <= middle <= 4 and 0 <= right <= 4):
            return False, "Rotor IDs must be 0-4 (I-V)"
        
        # Validate distinct
        if left == middle or left == right or middle == right:
            return False, "Rotors must be distinct"
        
        self.rotor_left = left
        self.rotor_middle = middle
        self.rotor_right = right
        return True, "OK"
    
    def set_windows(self, left: int, middle: int, right: int) -> Tuple[bool, str]:
        """Set window positions"""
        if not (0 <= left <= 25 and 0 <= middle <= 25 and 0 <= right <= 25):
            return False, "Window positions must be 0-25 (A-Z)"
        
        self.window_left = left
        self.window_middle = middle
        self.window_right = right
        return True, "OK"
    
    def set_rings(self, left: int, middle: int, right: int) -> Tuple[bool, str]:
        """Set ring settings"""
        if not (0 <= left <= 25 and 0 <= middle <= 25 and 0 <= right <= 25):
            return False, "Ring settings must be 0-25 (A-Z)"
        
        self.ring_left = left
        self.ring_middle = middle
        self.ring_right = right
        return True, "OK"
    
    def add_plugboard_pair(self, letter1: str, letter2: str) -> Tuple[bool, str]:
        """Add a plugboard pair"""
        # Validate letters
        letter1 = letter1.upper()
        letter2 = letter2.upper()
        
        if not (letter1.isalpha() and letter2.isalpha() and 
                len(letter1) == 1 and len(letter2) == 1):
            return False, "Plugboard entries must be single letters A-Z"
        
        # No self-connections
        if letter1 == letter2:
            return False, "Cannot connect a letter to itself"
        
        # Check maximum pairs
        if len(self.plugboard) >= 13:
            return False, "Maximum 13 plugboard pairs"
        
        # Check for conflicts
        for a, b in self.plugboard:
            if letter1 in (a, b) or letter2 in (a, b):
                return False, f"Letter already used in plugboard"
        
        # Add pair (normalized order)
        pair = tuple(sorted([letter1, letter2]))
        self.plugboard.append(pair)
        return True, "OK"
    
    def remove_plugboard_pair(self, index: int) -> bool:
        """Remove plugboard pair by index"""
        if 0 <= index < len(self.plugboard):
            self.plugboard.pop(index)
            return True
        return False
    
    def clear_plugboard(self):
        """Remove all plugboard pairs"""
        self.plugboard.clear()
    
    def get_plugboard_strings(self) -> List[str]:
        """Get plugboard as list of strings like ["AB", "CD"]"""
        return ["".join(pair) for pair in self.plugboard]
    
    def validate_configuration(self) -> Tuple[bool, str]:
        """Validate complete configuration"""
        # Check rotors
        success, msg = self.set_rotors(self.rotor_left, self.rotor_middle, self.rotor_right)
        if not success:
            return False, msg
        
        # Check windows
        success, msg = self.set_windows(self.window_left, self.window_middle, self.window_right)
        if not success:
            return False, msg
        
        # Check rings
        success, msg = self.set_rings(self.ring_left, self.ring_middle, self.ring_right)
        if not success:
            return False, msg
        
        return True, "Configuration valid"
    
    def get_configuration(self) -> dict:
        """Get current configuration as dictionary"""
        return {
            "rotors": [self.rotor_left, self.rotor_middle, self.rotor_right],
            "windows": [self.window_left, self.window_middle, self.window_right],
            "rings": [self.ring_left, self.ring_middle, self.ring_right],
            "plugboard": self.get_plugboard_strings()
        }
    
    def reset(self):
        """Reset to default configuration"""
        self.rotor_left = 0
        self.rotor_middle = 1
        self.rotor_right = 2
        self.window_left = 0
        self.window_middle = 0
        self.window_right = 0
        self.ring_left = 0
        self.ring_middle = 0
        self.ring_right = 0
        self.plugboard.clear()
        self.input_message = ""
        self.output_message = ""
    
    @staticmethod
    def position_to_letter(pos: int) -> str:
        """Convert position (0-25) to letter (A-Z)"""
        if 0 <= pos <= 25:
            return chr(ord('A') + pos)
        return 'A'
    
    @staticmethod
    def letter_to_position(letter: str) -> int:
        """Convert letter (A-Z) to position (0-25)"""
        letter = letter.upper()
        if 'A' <= letter <= 'Z':
            return ord(letter) - ord('A')
        return 0
    
    @staticmethod
    def normalize_message(message: str) -> str:
        """Normalize message to uppercase letters only"""
        return ''.join(c for c in message.upper() if c.isalpha())
