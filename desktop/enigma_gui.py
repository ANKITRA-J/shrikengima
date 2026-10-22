#!/usr/bin/env python3
"""
Shrike Fi Enigma - Desktop GUI Application
Main application entry point
"""

import sys
from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from enigma_model import EnigmaModel
from serial_manager import SerialManager
from settings_manager import SettingsManager


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Shrike Fi Enigma")
    app.setOrganizationName("Shrike")
    
    # Initialize components
    model = EnigmaModel()
    serial = SerialManager()
    settings = SettingsManager()
    
    # Create and show main window
    window = MainWindow(model, serial, settings)
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
