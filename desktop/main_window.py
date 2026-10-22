"""
Main GUI window for Shrike Fi Enigma
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QPlainTextEdit,
    QGroupBox, QListWidget, QInputDialog, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from enigma_model import EnigmaModel
from serial_manager import SerialManager
from settings_manager import SettingsManager


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, model: EnigmaModel, serial: SerialManager, settings: SettingsManager):
        super().__init__()
        
        self.model = model
        self.serial = serial
        self.settings = settings
        
        self.setWindowTitle("Shrike Fi Enigma")
        self.setMinimumSize(700, 800)
        
        # Create UI
        self.init_ui()
        
        # Load saved settings
        self.load_settings()
        
        # Update UI state
        self.update_connection_state()
    
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Connection section
        conn_group = self.create_connection_section()
        main_layout.addWidget(conn_group)
        
        # Configuration section
        config_group = self.create_configuration_section()
        main_layout.addWidget(config_group)
        
        # Message section
        message_group = self.create_message_section()
        main_layout.addWidget(message_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_connection_section(self) -> QGroupBox:
        """Create connection controls"""
        group = QGroupBox("Connection")
        layout = QHBoxLayout()
        
        # Port selection
        layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        layout.addWidget(self.port_combo)
        
        # Refresh ports button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(self.refresh_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)
        
        # Connection status
        self.conn_status = QLabel("● Disconnected")
        self.conn_status.setStyleSheet("color: gray;")
        layout.addWidget(self.conn_status)
        
        layout.addStretch()
        
        group.setLayout(layout)
        
        # Initial port refresh
        self.refresh_ports()
        
        return group
    
    def create_configuration_section(self) -> QGroupBox:
        """Create Enigma configuration controls"""
        group = QGroupBox("Configuration")
        layout = QVBoxLayout()
        
        # Rotors
        rotor_layout = QGridLayout()
        rotor_layout.addWidget(QLabel("Rotors:"), 0, 0)
        
        # Left rotor
        rotor_layout.addWidget(QLabel("Left:"), 1, 0)
        self.rotor_left_combo = QComboBox()
        self.rotor_left_combo.addItems(EnigmaModel.ROTOR_NAMES)
        rotor_layout.addWidget(self.rotor_left_combo, 1, 1)
        
        rotor_layout.addWidget(QLabel("Window:"), 1, 2)
        self.window_left_combo = self.create_position_combo()
        rotor_layout.addWidget(self.window_left_combo, 1, 3)
        
        rotor_layout.addWidget(QLabel("Ring:"), 1, 4)
        self.ring_left_combo = self.create_position_combo()
        rotor_layout.addWidget(self.ring_left_combo, 1, 5)
        
        # Middle rotor
        rotor_layout.addWidget(QLabel("Middle:"), 2, 0)
        self.rotor_middle_combo = QComboBox()
        self.rotor_middle_combo.addItems(EnigmaModel.ROTOR_NAMES)
        self.rotor_middle_combo.setCurrentIndex(1)
        rotor_layout.addWidget(self.rotor_middle_combo, 2, 1)
        
        rotor_layout.addWidget(QLabel("Window:"), 2, 2)
        self.window_middle_combo = self.create_position_combo()
        rotor_layout.addWidget(self.window_middle_combo, 2, 3)
        
        rotor_layout.addWidget(QLabel("Ring:"), 2, 4)
        self.ring_middle_combo = self.create_position_combo()
        rotor_layout.addWidget(self.ring_middle_combo, 2, 5)
        
        # Right rotor
        rotor_layout.addWidget(QLabel("Right:"), 3, 0)
        self.rotor_right_combo = QComboBox()
        self.rotor_right_combo.addItems(EnigmaModel.ROTOR_NAMES)
        self.rotor_right_combo.setCurrentIndex(2)
        rotor_layout.addWidget(self.rotor_right_combo, 3, 1)
        
        rotor_layout.addWidget(QLabel("Window:"), 3, 2)
        self.window_right_combo = self.create_position_combo()
        rotor_layout.addWidget(self.window_right_combo, 3, 3)
        
        rotor_layout.addWidget(QLabel("Ring:"), 3, 4)
        self.ring_right_combo = self.create_position_combo()
        rotor_layout.addWidget(self.ring_right_combo, 3, 5)
        
        layout.addLayout(rotor_layout)
        
        # Plugboard
        plugboard_layout = QHBoxLayout()
        plugboard_layout.addWidget(QLabel("Plugboard:"))
        
        self.plugboard_list = QListWidget()
        self.plugboard_list.setMaximumHeight(100)
        plugboard_layout.addWidget(self.plugboard_list)
        
        pb_btn_layout = QVBoxLayout()
        self.add_pair_btn = QPushButton("+ Add Pair")
        self.add_pair_btn.clicked.connect(self.add_plugboard_pair)
        pb_btn_layout.addWidget(self.add_pair_btn)
        
        self.remove_pair_btn = QPushButton("- Remove")
        self.remove_pair_btn.clicked.connect(self.remove_plugboard_pair)
        pb_btn_layout.addWidget(self.remove_pair_btn)
        
        self.clear_pb_btn = QPushButton("Clear All")
        self.clear_pb_btn.clicked.connect(self.clear_plugboard)
        pb_btn_layout.addWidget(self.clear_pb_btn)
        
        plugboard_layout.addLayout(pb_btn_layout)
        layout.addLayout(plugboard_layout)
        
        # Apply configuration button
        self.apply_config_btn = QPushButton("Apply Configuration")
        self.apply_config_btn.clicked.connect(self.apply_configuration)
        self.apply_config_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.apply_config_btn)
        
        group.setLayout(layout)
        return group
    
    def create_message_section(self) -> QGroupBox:
        """Create message input/output section"""
        group = QGroupBox("Messages")
        layout = QVBoxLayout()
        
        # Input
        layout.addWidget(QLabel("Input Message:"))
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("Enter message to encrypt/decrypt (letters only)")
        self.input_text.setMaximumHeight(100)
        layout.addWidget(self.input_text)
        
        # Output
        layout.addWidget(QLabel("Output:"))
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(100)
        output_font = QFont("Courier")
        self.output_text.setFont(output_font)
        layout.addWidget(self.output_text)
        
        # Window display
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Window Positions:"))
        self.window_display = QLabel("A A A")
        window_font = QFont("Courier", 12, QFont.Bold)
        self.window_display.setFont(window_font)
        window_layout.addWidget(self.window_display)
        window_layout.addStretch()
        layout.addLayout(window_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.encrypt_btn = QPushButton("Encrypt")
        self.encrypt_btn.clicked.connect(self.encrypt_message)
        self.encrypt_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.encrypt_btn)
        
        self.decrypt_btn = QPushButton("Decrypt")
        self.decrypt_btn.clicked.connect(self.decrypt_message)
        self.decrypt_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.decrypt_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_messages)
        btn_layout.addWidget(self.clear_btn)
        
        self.reset_btn = QPushButton("Reset Board")
        self.reset_btn.clicked.connect(self.reset_board)
        btn_layout.addWidget(self.reset_btn)
        
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group
    
    def create_position_combo(self) -> QComboBox:
        """Create A-Z position combo box"""
        combo = QComboBox()
        combo.addItems([chr(i) for i in range(ord('A'), ord('Z') + 1)])
        return combo
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = self.serial.list_ports()
        for port_name, desc in ports:
            display_name = f"{port_name} - {desc}"
            self.port_combo.addItem(display_name, port_name)
        
        if not ports:
            self.status_bar.showMessage("No serial ports found", 3000)
    
    def toggle_connection(self):
        """Connect or disconnect from board"""
        if self.serial.is_connected():
            self.serial.disconnect()
            self.update_connection_state()
            self.status_bar.showMessage("Disconnected", 3000)
        else:
            port_name = self.port_combo.currentData()
            if not port_name:
                QMessageBox.warning(self, "No Port", "Please select a serial port")
                return
            
            success, msg = self.serial.connect(port_name)
            if success:
                self.update_connection_state()
                self.status_bar.showMessage(msg, 3000)
                
                # Get initial status
                success, status = self.serial.get_status()
                if success and "windows" in status:
                    windows = status["windows"]
                    self.update_window_display(windows)
            else:
                QMessageBox.critical(self, "Connection Failed", msg)
    
    def update_connection_state(self):
        """Update UI based on connection state"""
        connected = self.serial.is_connected()
        
        # Update status indicator
        if connected:
            self.conn_status.setText("● Connected")
            self.conn_status.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect")
        else:
            self.conn_status.setText("● Disconnected")
            self.conn_status.setStyleSheet("color: gray;")
            self.connect_btn.setText("Connect")
        
        # Enable/disable controls
        self.apply_config_btn.setEnabled(connected)
        self.encrypt_btn.setEnabled(connected)
        self.decrypt_btn.setEnabled(connected)
        self.reset_btn.setEnabled(connected)
    
    def apply_configuration(self):
        """Apply current configuration to board"""
        if not self.serial.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to board first")
            return
        
        # Get configuration from UI
        rotors = [
            self.rotor_left_combo.currentIndex(),
            self.rotor_middle_combo.currentIndex(),
            self.rotor_right_combo.currentIndex()
        ]
        
        windows = [
            self.window_left_combo.currentIndex(),
            self.window_middle_combo.currentIndex(),
            self.window_right_combo.currentIndex()
        ]
        
        rings = [
            self.ring_left_combo.currentIndex(),
            self.ring_middle_combo.currentIndex(),
            self.ring_right_combo.currentIndex()
        ]
        
        plugboard = [self.plugboard_list.item(i).text() 
                    for i in range(self.plugboard_list.count())]
        
        # Validate
        success, msg = self.model.set_rotors(*rotors)
        if not success:
            QMessageBox.warning(self, "Invalid Configuration", msg)
            return
        
        # Send to board
        success, response = self.serial.configure(rotors, windows, rings, plugboard)
        
        if success:
            self.status_bar.showMessage("Configuration applied", 3000)
            if "windows" in response:
                self.update_window_display(response["windows"])
        else:
            error = response.get("error", "Unknown error")
            QMessageBox.critical(self, "Configuration Failed", error)
    
    def encrypt_message(self):
        """Encrypt input message"""
        self.process_message("encrypt")
    
    def decrypt_message(self):
        """Decrypt input message (same as encrypt in Enigma)"""
        self.process_message("decrypt")
    
    def process_message(self, operation: str):
        """Process message (encrypt/decrypt)"""
        if not self.serial.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to board first")
            return
        
        message = self.input_text.toPlainText()
        if not message:
            QMessageBox.information(self, "No Message", "Please enter a message")
            return
        
        # Normalize message
        message = EnigmaModel.normalize_message(message)
        if not message:
            QMessageBox.warning(self, "Invalid Message", "Message must contain at least one letter")
            return
        
        # Process
        self.status_bar.showMessage(f"{operation.capitalize()}ing...", 0)
        self.setCursor(Qt.WaitCursor)
        
        if operation == "encrypt":
            success, response = self.serial.encrypt(message)
        else:
            success, response = self.serial.decrypt(message)
        
        self.setCursor(Qt.ArrowCursor)
        
        if success:
            result = response.get("result", "")
            self.output_text.setPlainText(result)
            self.status_bar.showMessage(f"{operation.capitalize()}ion complete", 3000)
            
            if "windows" in response:
                self.update_window_display(response["windows"])
        else:
            error = response.get("error", "Unknown error")
            QMessageBox.critical(self, f"{operation.capitalize()} Failed", error)
            self.status_bar.showMessage("Error", 3000)
    
    def clear_messages(self):
        """Clear input and output"""
        self.input_text.clear()
        self.output_text.clear()
    
    def reset_board(self):
        """Reset board to default state"""
        if not self.serial.is_connected():
            return
        
        reply = QMessageBox.question(
            self, "Reset Board",
            "Reset board to default configuration?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, response = self.serial.reset()
            if success:
                self.status_bar.showMessage("Board reset", 3000)
                self.window_display.setText("A A A")
            else:
                error = response.get("error", "Unknown error")
                QMessageBox.critical(self, "Reset Failed", error)
    
    def add_plugboard_pair(self):
        """Add plugboard pair dialog"""
        text, ok = QInputDialog.getText(
            self, "Add Plugboard Pair",
            "Enter two letters (e.g., AB):"
        )
        
        if ok and text:
            text = text.upper().strip()
            if len(text) != 2 or not text.isalpha():
                QMessageBox.warning(self, "Invalid Input", "Please enter exactly two letters")
                return
            
            success, msg = self.model.add_plugboard_pair(text[0], text[1])
            if success:
                self.plugboard_list.addItem(text)
            else:
                QMessageBox.warning(self, "Invalid Pair", msg)
    
    def remove_plugboard_pair(self):
        """Remove selected plugboard pair"""
        current_row = self.plugboard_list.currentRow()
        if current_row >= 0:
            self.plugboard_list.takeItem(current_row)
            self.model.remove_plugboard_pair(current_row)
    
    def clear_plugboard(self):
        """Clear all plugboard pairs"""
        self.plugboard_list.clear()
        self.model.clear_plugboard()
    
    def update_window_display(self, windows: list):
        """Update window position display"""
        if len(windows) == 3:
            letters = [EnigmaModel.position_to_letter(w) for w in windows]
            self.window_display.setText(f"{letters[0]}  {letters[1]}  {letters[2]}")
            
            # Also update combo boxes
            self.window_left_combo.setCurrentIndex(windows[0])
            self.window_middle_combo.setCurrentIndex(windows[1])
            self.window_right_combo.setCurrentIndex(windows[2])
    
    def load_settings(self):
        """Load saved settings"""
        # Load last port
        last_port = self.settings.get("last_port", "")
        if last_port:
            index = self.port_combo.findData(last_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        
        # Load last configuration
        last_rotors = self.settings.get("last_rotors", [0, 1, 2])
        self.rotor_left_combo.setCurrentIndex(last_rotors[0])
        self.rotor_middle_combo.setCurrentIndex(last_rotors[1])
        self.rotor_right_combo.setCurrentIndex(last_rotors[2])
        
        last_windows = self.settings.get("last_windows", [0, 0, 0])
        self.window_left_combo.setCurrentIndex(last_windows[0])
        self.window_middle_combo.setCurrentIndex(last_windows[1])
        self.window_right_combo.setCurrentIndex(last_windows[2])
        
        last_rings = self.settings.get("last_rings", [0, 0, 0])
        self.ring_left_combo.setCurrentIndex(last_rings[0])
        self.ring_middle_combo.setCurrentIndex(last_rings[1])
        self.ring_right_combo.setCurrentIndex(last_rings[2])
        
        last_plugboard = self.settings.get("last_plugboard", [])
        for pair in last_plugboard:
            self.plugboard_list.addItem(pair)
            if len(pair) == 2:
                self.model.add_plugboard_pair(pair[0], pair[1])
    
    def save_settings(self):
        """Save current settings"""
        current_port = self.port_combo.currentData()
        if current_port:
            self.settings.set("last_port", current_port)
        
        self.settings.set("last_rotors", [
            self.rotor_left_combo.currentIndex(),
            self.rotor_middle_combo.currentIndex(),
            self.rotor_right_combo.currentIndex()
        ])
        
        self.settings.set("last_windows", [
            self.window_left_combo.currentIndex(),
            self.window_middle_combo.currentIndex(),
            self.window_right_combo.currentIndex()
        ])
        
        self.settings.set("last_rings", [
            self.ring_left_combo.currentIndex(),
            self.ring_middle_combo.currentIndex(),
            self.ring_right_combo.currentIndex()
        ])
        
        plugboard = [self.plugboard_list.item(i).text() 
                    for i in range(self.plugboard_list.count())]
        self.settings.set("last_plugboard", plugboard)
        
        self.settings.save()
    
    def closeEvent(self, event):
        """Handle window close"""
        self.save_settings()
        if self.serial.is_connected():
            self.serial.disconnect()
        event.accept()
