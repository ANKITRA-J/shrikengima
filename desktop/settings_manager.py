"""
Settings persistence manager
Saves and loads user preferences
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    """Manages application settings persistence"""
    
    DEFAULT_SETTINGS = {
        "last_port": "",
        "auto_connect": False,
        "window_geometry": None,
        "last_rotors": [0, 1, 2],
        "last_windows": [0, 0, 0],
        "last_rings": [0, 0, 0],
        "last_plugboard": []
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings manager
        
        Args:
            config_path: Custom path to config file (optional)
                        Defaults to ~/.shrike_enigma/settings.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Use user home directory
            config_dir = Path.home() / ".shrike_enigma"
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / "settings.json"
        
        self.settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Load settings from file
        Returns: Settings dictionary
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults (in case new settings added)
                    self.settings = {**self.DEFAULT_SETTINGS, **loaded}
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load settings: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
        
        return self.settings
    
    def save(self, settings: Optional[Dict[str, Any]] = None):
        """
        Save settings to file
        
        Args:
            settings: Settings dictionary (optional, uses current if None)
        """
        if settings:
            self.settings = settings
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            key: Setting key
            default: Default value if key not found
        
        Returns: Setting value
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
    
    def clear(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
