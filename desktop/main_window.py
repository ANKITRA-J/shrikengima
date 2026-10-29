"""
Main GUI window for Shrike Fi Enigma
Tactile vintage hardware simulation aesthetic for the Shrike Fi board.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QPlainTextEdit,
    QGroupBox, QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
    QStatusBar, QDialog, QTextBrowser, QFrame, QApplication, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette

from pathlib import Path

from enigma_model import EnigmaModel
from serial_manager import SerialManager
from settings_manager import SettingsManager
from widgets import (
    LetterDrum, RingDrum, RotorSelector, InspectionPorthole,
    PlugboardWidget, JewelIndicator
)

# ── Authentic Enigma Palette & Stylesheet ─────────────────────────────────────
_CHASSIS_BG     = "#181715"   # Deep vulcanite/crinkle finish metal
_PANEL_BG       = "#22201c"   # Machined instrument casing
_PANEL_ALT      = "#282521"   # Raised plate surface
_BORDER_BEVEL   = "#3a352c"   # Chamfered metal edge
_BRASS_GOLD     = "#d4af37"   # Warm engraved brass
_BRASS_MUTED    = "#a68832"   # Aged brass patina
_IVORY_TEXT     = "#ede7db"   # Stamped ivory lettering
_MUTED_TEXT     = "#948d81"   # Subdued indicator text
_GLOW_AMBER     = "#ffb74d"   # Output phosphor glow
_RECESS_BLACK   = "#0c0b0a"   # Recessed cavity

_ENIGMA_QSS = f"""
/* ── Main Application Chassis ───────────────────────────────────── */
QMainWindow, QDialog {{
    background-color: {_CHASSIS_BG};
}}
QWidget {{
    color: {_IVORY_TEXT};
    font-size: 13px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}

/* ── Group Boxes (Machined Metal Plates) ─────────────────────────── */
QGroupBox {{
    background-color: {_PANEL_BG};
    border: 1px solid {_BORDER_BEVEL};
    border-radius: 7px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 14px;
    color: {_BRASS_GOLD};
    font-family: Georgia, serif;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}

/* ── Standard Pushbuttons ───────────────────────────────────────── */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #332f28, stop:1 #24211b);
    border: 1px solid #4a4234;
    border-radius: 5px;
    color: {_IVORY_TEXT};
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    border-color: {_BRASS_GOLD};
    color: #ffffff;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3d372f, stop:1 #2b2721);
}}
QPushButton:pressed {{
    background: #191714;
    border-color: #363025;
}}
QPushButton:disabled {{
    background: #1c1a17;
    border-color: #2b2823;
    color: #575249;
}}

/* ── Distinct Action Buttons ────────────────────────────────────── */
QPushButton#encryptBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8f1d22, stop:1 #611014);
    border: 1px solid #aa292f;
    border-bottom: 2px solid #3d070a;
    border-radius: 6px;
    color: #fff6e8;
    font-family: Georgia, serif;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 1px;
    padding: 8px 24px;
}}
QPushButton#encryptBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a8262c, stop:1 #73151a);
    border-color: {_BRASS_GOLD};
}}
QPushButton#encryptBtn:pressed {{
    background: #480c0f;
    border-color: #2d0709;
}}
QPushButton#encryptBtn:disabled {{
    background: #2b1416;
    border-color: #3d1b1e;
    color: #5c3538;
}}

QPushButton#decryptBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a6b40, stop:1 #114529);
    border: 1px solid #238550;
    border-bottom: 2px solid #0a2617;
    border-radius: 6px;
    color: #fff6e8;
    font-family: Georgia, serif;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 1px;
    padding: 8px 24px;
}}
QPushButton#decryptBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #22824e, stop:1 #155734);
    border-color: {_BRASS_GOLD};
}}
QPushButton#decryptBtn:pressed {{
    background: #0d301d;
    border-color: #071c11;
}}
QPushButton#decryptBtn:disabled {{
    background: #14291e;
    border-color: #1d3b2b;
    color: #385747;
}}

QPushButton#connectBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a342a, stop:1 #28241d);
    border: 1px solid {_BRASS_MUTED};
    color: {_BRASS_GOLD};
    font-weight: bold;
    padding: 6px 16px;
    border-radius: 5px;
}}
QPushButton#connectBtn:hover {{
    border-color: {_BRASS_GOLD};
    color: #ffffff;
    background: #3f392f;
}}

QPushButton#disconnectBtn {{
    background: transparent;
    border: 1px solid #992b2b;
    color: #e57373;
    font-weight: bold;
    padding: 6px 16px;
    border-radius: 5px;
}}
QPushButton#disconnectBtn:hover {{
    background: #4a1515;
    color: #ffffff;
}}

QPushButton#applyBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #856424, stop:1 #574115);
    border: 1px solid {_BRASS_GOLD};
    border-radius: 5px;
    color: #fff6e8;
    font-weight: bold;
    padding: 6px 16px;
}}
QPushButton#applyBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9c752b, stop:1 #6b501b);
}}

/* ── Combo Boxes ─────────────────────────────────────────────────── */
QComboBox {{
    background-color: {_RECESS_BLACK};
    border: 1px solid #3d3830;
    border-radius: 4px;
    padding: 4px 8px;
    color: {_IVORY_TEXT};
    min-height: 26px;
}}
QComboBox:hover {{
    border-color: {_BRASS_GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: #1e1c18;
    border: 1px solid #4a4336;
    color: {_IVORY_TEXT};
    selection-background-color: {_BRASS_MUTED};
    selection-color: #ffffff;
}}

/* ── Text Input / Output Windows ─────────────────────────────────── */
QPlainTextEdit, QTextEdit {{
    background-color: {_RECESS_BLACK};
    border: 1px solid #38342c;
    border-radius: 5px;
    color: {_IVORY_TEXT};
    padding: 8px;
    selection-background-color: {_BRASS_MUTED};
    selection-color: #ffffff;
}}
QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {_BRASS_GOLD};
}}

/* ── Status Bar & Scrollbar ──────────────────────────────────────── */
QStatusBar {{
    background-color: #141311;
    color: {_MUTED_TEXT};
    border-top: 1px solid #292620;
    font-size: 12px;
}}

QScrollBar:vertical {{
    background: #181715;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: #3a352c;
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_BRASS_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


def _sep() -> QFrame:
    """Subtle engraved dividing line."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: #302c25;")
    return line


# ── Thread Worker ─────────────────────────────────────────────────────────────
class BoardJob(QThread):
    result_ready = Signal(object)

    def __init__(self, task, parent):
        super().__init__(parent)
        self.task = task

    def run(self):
        try:
            result = self.task()
        except Exception as exc:
            result = (False, {"error": str(exc)})
        self.result_ready.emit(result)


# ── Main Application Window ───────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """Main window with authentic tactile Enigma controls."""

    def __init__(self, model: EnigmaModel, serial: SerialManager, settings: SettingsManager):
        super().__init__()
        self.model = model
        self.serial = serial
        self.settings = settings
        self.job = None

        self.setWindowTitle("Shrike Fi Enigma I · Hardware Cipher Machine")
        self.setMinimumSize(800, 840)
        self.resize(820, 940)

        # Apply authentic Enigma stylesheet
        QApplication.instance().setStyleSheet(_ENIGMA_QSS)

        self.init_ui()
        self.update_connection_state()

    # ── UI Construction ────────────────────────────────────────────────────────
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        vbox = QVBoxLayout(content)
        vbox.setSpacing(10)
        vbox.setContentsMargins(14, 10, 14, 14)

        # Top Title Bar & Machine Banner
        vbox.addLayout(self._build_header_row())
        vbox.addWidget(_sep())

        # Hardware Link & USB Port Section
        vbox.addWidget(self.create_connection_section())

        # Rotor Mechanism Bay (The Core Scrambler)
        vbox.addWidget(self.create_configuration_section())

        # Steckerbrett (Plugboard Panel)
        vbox.addWidget(self._build_plugboard_panel())

        # Message Telegram Terminal (Input / Encrypt / Output)
        vbox.addWidget(self.create_message_section())

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _build_header_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        # Logo & Machine Plate
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title = QLabel("ENIGMA I")
        title.setStyleSheet(
            f"font-family: Georgia, serif; font-size: 20px; font-weight: bold; "
            f"color: {_BRASS_GOLD}; letter-spacing: 2.5px; background: transparent;"
        )
        subtitle = QLabel("Vicharak Shrike Fi · ESP32-S3 & SLG47910V FPGA Cipher Engine")
        subtitle.setStyleSheet(
            f"font-size: 11px; color: {_MUTED_TEXT}; letter-spacing: 0.5px; background: transparent;"
        )
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        row.addLayout(title_box)

        row.addStretch()

        self.guide_btn = QPushButton("📖  How to use Enigma")
        self.guide_btn.setToolTip("Open the interactive beginner guide and historical cipher instructions")
        self.guide_btn.setFixedHeight(32)
        self.guide_btn.clicked.connect(self.show_user_guide)
        row.addWidget(self.guide_btn)

        return row

    # ── Connection Section ─────────────────────────────────────────────────────
    def create_connection_section(self) -> QGroupBox:
        group = QGroupBox("Hardware Communication Link")
        row = QHBoxLayout(group)
        row.setSpacing(10)

        # Jewel Indicator Lamp
        self.jewel = JewelIndicator()
        row.addWidget(self.jewel)

        lbl = QLabel("Serial Port:")
        lbl.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 12px;")
        row.addWidget(lbl)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(240)
        self.port_combo.setToolTip("Select the USB communication port of the connected Shrike Fi board")
        row.addWidget(self.port_combo, 1)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setToolTip("Scan serial bus for newly connected devices")
        self.refresh_btn.setFixedHeight(30)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        row.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.setFixedHeight(30)
        self.connect_btn.setToolTip("Establish connection and run startup hardware verification on the FPGA")
        self.connect_btn.clicked.connect(self.toggle_connection)
        row.addWidget(self.connect_btn)

        self.conn_status = QLabel("● Disconnected")
        self.conn_status.setStyleSheet(f"color: {_MUTED_TEXT}; font-weight: bold; min-width: 140px;")
        row.addWidget(self.conn_status)

        self.refresh_ports()
        return group

    # ── Rotor Scrambler Bay ────────────────────────────────────────────────────
    def create_configuration_section(self) -> QGroupBox:
        group = QGroupBox("Rotor Mechanism && Key Settings")
        outer = QVBoxLayout(group)
        outer.setSpacing(10)

        # Top row: Explanatory note & Inspection porthole
        top_row = QHBoxLayout()

        desc_box = QVBoxLayout()
        desc_box.setSpacing(3)
        hint = QLabel(
            "Scroll or click the brass wheels to adjust starting window positions. "
            "Each message starts at these initial windows. Encrypt and Decrypt with matching settings."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 12px; background: transparent;")
        desc_box.addWidget(hint)

        # Rotor Inspection Porthole (Live Stepped Rotor Display)
        self.inspection_porthole = InspectionPorthole()
        self.window_display = QLabel("—  —  —")
        self.window_display.setVisible(False)

        porthole_col = QVBoxLayout()
        porthole_lbl = QLabel("Live Stepped Rotor Output:")
        porthole_lbl.setStyleSheet(f"color: {_BRASS_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        porthole_col.addWidget(porthole_lbl, 0, Qt.AlignCenter)
        porthole_col.addWidget(self.inspection_porthole)

        top_row.addLayout(desc_box, 1)
        top_row.addSpacing(14)
        top_row.addLayout(porthole_col)
        outer.addLayout(top_row)

        outer.addWidget(_sep())

        # Rotor Cassettes (Side by Side: Left, Middle, Right)
        rotors_row = QHBoxLayout()
        rotors_row.setSpacing(14)

        self.rotor_left_combo = RotorSelector()
        self.rotor_middle_combo = RotorSelector()
        self.rotor_middle_combo.setCurrentIndex(1)
        self.rotor_right_combo = RotorSelector()
        self.rotor_right_combo.setCurrentIndex(2)

        self.window_left_combo = LetterDrum()
        self.window_middle_combo = LetterDrum()
        self.window_right_combo = LetterDrum()

        self.ring_left_combo = RingDrum()
        self.ring_middle_combo = RingDrum()
        self.ring_right_combo = RingDrum()

        bay_data = [
            ("LEFT ROTOR (Slow)", self.rotor_left_combo, self.window_left_combo, self.ring_left_combo),
            ("MIDDLE ROTOR", self.rotor_middle_combo, self.window_middle_combo, self.ring_middle_combo),
            ("RIGHT ROTOR (Fast)", self.rotor_right_combo, self.window_right_combo, self.ring_right_combo),
        ]

        for title_str, r_sel, w_drum, ri_drum in bay_data:
            cassette = QFrame()
            cassette.setMinimumHeight(240)
            cassette.setStyleSheet(
                f"background-color: {_PANEL_ALT}; border: 1px solid {_BORDER_BEVEL}; "
                f"border-radius: 8px;"
            )
            c_box = QVBoxLayout(cassette)
            c_box.setSpacing(5)
            c_box.setContentsMargins(8, 8, 8, 8)
            c_box.setAlignment(Qt.AlignHCenter)

            c_hdr = QLabel(title_str)
            c_hdr.setStyleSheet(
                f"color: {_BRASS_GOLD}; font-family: Georgia, serif; font-size: 11px; "
                f"font-weight: bold; letter-spacing: 0.8px;"
            )
            c_box.addWidget(c_hdr, 0, Qt.AlignHCenter)

            # Rotor Type (I-V)
            c_box.addWidget(r_sel, 0, Qt.AlignHCenter)

            # Window Thumbwheel (A-Z)
            w_lbl = QLabel("WINDOW")
            w_lbl.setStyleSheet(f"color: {_BRASS_MUTED}; font-size: 9px; font-weight: bold; letter-spacing: 1px;")
            c_box.addWidget(w_lbl, 0, Qt.AlignHCenter)
            c_box.addWidget(w_drum, 0, Qt.AlignHCenter)

            # Ring Setting
            ri_lbl = QLabel("RING OFFSET")
            ri_lbl.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
            c_box.addWidget(ri_lbl, 0, Qt.AlignHCenter)
            c_box.addWidget(ri_drum, 0, Qt.AlignHCenter)

            rotors_row.addWidget(cassette, 1)

        outer.addLayout(rotors_row)

        # Apply Settings Row
        apply_row = QHBoxLayout()
        apply_hint = QLabel(
            "Note: Encrypt and Decrypt apply all visible settings automatically. "
            "Use Apply Configuration only if pre-loading settings without sending text."
        )
        apply_hint.setWordWrap(True)
        apply_hint.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 11px;")
        apply_row.addWidget(apply_hint, 1)

        self.apply_config_btn = QPushButton("Apply Configuration")
        self.apply_config_btn.setObjectName("applyBtn")
        self.apply_config_btn.setToolTip("Upload current rotor order, windows, rings and plugboard to the board")
        self.apply_config_btn.setFixedHeight(32)
        self.apply_config_btn.clicked.connect(self.apply_configuration)
        apply_row.addWidget(self.apply_config_btn)
        outer.addLayout(apply_row)

        return group

    # ── Steckerbrett (Plugboard Panel) ─────────────────────────────────────────
    def _build_plugboard_panel(self) -> QGroupBox:
        group = QGroupBox("Steckerbrett · Plugboard (Letter-Swap Cables, Max 13 Pairs)")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(6)

        # Interactive Socket Matrix
        self.plugboard_widget = PlugboardWidget()
        vbox.addWidget(self.plugboard_widget)

        # Hidden QListWidget kept for backwards compatibility with any legacy code
        self.plugboard_list = QListWidget()
        self.plugboard_list.setVisible(False)
        vbox.addWidget(self.plugboard_list)

        # Socket control actions
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        help_lbl = QLabel("Click socket letter to connect/disconnect pairs")
        help_lbl.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 11px;")
        btn_row.addWidget(help_lbl)

        btn_row.addStretch()

        self.add_pair_btn = QPushButton("＋ Add Cable by Text")
        self.add_pair_btn.setToolTip("Add a pair using text dialog, e.g. 'AB'")
        self.add_pair_btn.setFixedHeight(28)
        self.add_pair_btn.clicked.connect(self.add_plugboard_pair)
        btn_row.addWidget(self.add_pair_btn)

        self.clear_pb_btn = QPushButton("✕ Clear All Cables")
        self.clear_pb_btn.setToolTip("Disconnect all active plugboard cables")
        self.clear_pb_btn.setFixedHeight(28)
        self.clear_pb_btn.clicked.connect(self.clear_plugboard)
        btn_row.addWidget(self.clear_pb_btn)

        vbox.addLayout(btn_row)
        return group

    # ── Message Section ────────────────────────────────────────────────────────
    def create_message_section(self) -> QGroupBox:
        group = QGroupBox("Message Terminal")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(7)

        # Input Header
        in_hdr = QHBoxLayout()
        in_lbl = QLabel("Input Message:")
        in_lbl.setStyleSheet(f"font-weight: bold; color: {_IVORY_TEXT};")
        in_hdr.addWidget(in_lbl)
        in_hdr.addStretch()
        char_hint = QLabel("ASCII letters, digits, spaces & punctuation (max 512 chars)")
        char_hint.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 11px;")
        in_hdr.addWidget(char_hint)
        vbox.addLayout(in_hdr)

        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText(
            "Enter text to encrypt or decrypt — e.g. HELLOWORLD\n"
            "Lowercase letters are uppercased on the board; spacing and punctuation are preserved."
        )
        self.input_text.setFixedHeight(75)
        monofont = QFont("Courier New", 12)
        self.input_text.setFont(monofont)
        vbox.addWidget(self.input_text)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 2, 0, 2)

        self.encrypt_btn = QPushButton("🔒  ENCRYPT")
        self.encrypt_btn.setObjectName("encryptBtn")
        self.encrypt_btn.setFixedHeight(38)
        self.encrypt_btn.setMinimumWidth(140)
        self.encrypt_btn.setToolTip("Process input through the physical FPGA cipher engine")
        self.encrypt_btn.clicked.connect(self.encrypt_message)
        btn_row.addWidget(self.encrypt_btn)

        self.decrypt_btn = QPushButton("🔓  DECRYPT")
        self.decrypt_btn.setObjectName("decryptBtn")
        self.decrypt_btn.setFixedHeight(38)
        self.decrypt_btn.setMinimumWidth(140)
        self.decrypt_btn.setToolTip("Recover original text using the same key settings")
        self.decrypt_btn.clicked.connect(self.decrypt_message)
        btn_row.addWidget(self.decrypt_btn)

        btn_row.addStretch()

        self.clear_btn = QPushButton("Clear Text")
        self.clear_btn.setToolTip("Clear input and output text fields")
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.clicked.connect(self.clear_messages)
        btn_row.addWidget(self.clear_btn)

        vbox.addLayout(btn_row)

        # Output Header
        out_hdr = QHBoxLayout()
        out_lbl = QLabel("Output Result:")
        out_lbl.setStyleSheet(f"font-weight: bold; color: {_IVORY_TEXT};")
        out_hdr.addWidget(out_lbl)

        badge = QLabel(" FPGA Verified Ciphertext ")
        badge.setStyleSheet(
            f"background-color: #1a3826; color: #5ce693; border: 1px solid #238550; "
            f"border-radius: 3px; font-size: 10px; font-weight: bold;"
        )
        out_hdr.addWidget(badge)
        out_hdr.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setToolTip("Copy ciphertext output to system clipboard")
        self.copy_btn.setFixedHeight(24)
        self.copy_btn.setFixedWidth(64)
        self.copy_btn.clicked.connect(self._copy_output)
        out_hdr.addWidget(self.copy_btn)
        vbox.addLayout(out_hdr)

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFixedHeight(75)
        self.output_text.setFont(monofont)
        self.output_text.setStyleSheet(f"color: {_GLOW_AMBER};")
        self.output_text.setPlaceholderText("Output ciphertext will be displayed here...")
        vbox.addWidget(self.output_text)

        vbox.addWidget(_sep())

        # Hardware Utility Controls
        util_row = QHBoxLayout()
        util_row.setSpacing(10)

        hw_lbl = QLabel("Hardware Maintenance:")
        hw_lbl.setStyleSheet(f"color: {_MUTED_TEXT}; font-size: 11px;")
        util_row.addWidget(hw_lbl)

        self.reset_btn = QPushButton("↺  Reset Board to Defaults")
        self.reset_btn.setToolTip("Restore Rotors I-II-III, Windows AAA, Rings AAA, and identity plugboard")
        self.reset_btn.setFixedHeight(28)
        self.reset_btn.clicked.connect(self.reset_board)
        util_row.addWidget(self.reset_btn)

        self.selftest_btn = QPushButton("🔬  Hardware Self-test")
        self.selftest_btn.setToolTip("Run FPGA self-test vectors through the hardware link")
        self.selftest_btn.setFixedHeight(28)
        self.selftest_btn.clicked.connect(self.selftest_board)
        util_row.addWidget(self.selftest_btn)

        util_row.addStretch()
        vbox.addLayout(util_row)

        return group

    # ── Shared Helpers ─────────────────────────────────────────────────────────
    def create_position_combo(self) -> LetterDrum:
        """Drop-in factory for backward compatibility."""
        return LetterDrum()

    def _copy_output(self):
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("Output copied to clipboard", 2500)

    def show_user_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("How to use Enigma — Beginner & Historical Guide")
        dialog.resize(720, 680)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenLinks(False)
        guide = Path(__file__).resolve().parents[1] / "docs/USER_GUIDE.md"
        browser.setMarkdown(guide.read_text(encoding="utf-8"))
        layout.addWidget(browser)
        close = QPushButton("Close Guide")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    # ── Port Management ────────────────────────────────────────────────────────
    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial.list_ports()
        for port_name, desc in ports:
            display = f"{port_name}  —  {desc}" if desc else port_name
            self.port_combo.addItem(display, port_name)
        if not ports:
            self.status_bar.showMessage("No serial ports detected — please connect USB cable and click ↻ Refresh", 4000)

    def toggle_connection(self):
        if self.serial.is_connected():
            self.serial.disconnect()
            self.update_connection_state()
            self.status_bar.showMessage("Disconnected from Shrike Fi board", 3000)
        else:
            port_name = self.port_combo.currentData()
            if not port_name:
                QMessageBox.warning(self, "No Port Selected", "Please select a serial port from the dropdown menu.")
                return

            self.jewel.set_state("busy")
            self.status_bar.showMessage("Connecting — initializing FPGA bitstream and handshake...", 0)

            def complete(result):
                success, message = result
                if success:
                    self.status_bar.showMessage(str(message), 4000)
                else:
                    QMessageBox.critical(self, "Connection Failed", str(message))
                    self.status_bar.showMessage("Connection failed — inspect error details", 4000)

            self.run_job(lambda: self.serial.connect(port_name), complete)

    # ── Job Runner ─────────────────────────────────────────────────────────────
    def run_job(self, task, callback):
        if self.job is not None:
            return
        self.centralWidget().setEnabled(False)
        self.setCursor(Qt.WaitCursor)
        self.job = BoardJob(task, self)
        self.job.result_ready.connect(callback)
        self.job.finished.connect(self.finish_job)
        self.job.start()

    def finish_job(self):
        self.job.deleteLater()
        self.job = None
        self.centralWidget().setEnabled(True)
        self.setCursor(Qt.ArrowCursor)
        self.update_connection_state()

    # ── State Sync ─────────────────────────────────────────────────────────────
    def update_connection_state(self):
        connected = self.serial.is_connected()

        if connected:
            self.jewel.set_state("connected")
            self.conn_status.setText("● Connected")
            self.conn_status.setStyleSheet("color: #4ade80; font-weight: bold; min-width: 140px;")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setObjectName("disconnectBtn")
        else:
            self.jewel.set_state("disconnected")
            self.conn_status.setText("● Disconnected")
            self.conn_status.setStyleSheet(f"color: {_MUTED_TEXT}; font-weight: bold; min-width: 140px;")
            self.connect_btn.setText("Connect")
            self.connect_btn.setObjectName("connectBtn")

        self.connect_btn.setStyle(self.connect_btn.style())

        for btn in (self.apply_config_btn, self.encrypt_btn,
                    self.decrypt_btn, self.reset_btn, self.selftest_btn):
            btn.setEnabled(connected)

    # ── Configuration ──────────────────────────────────────────────────────────
    def apply_configuration(self):
        if not self.serial.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to the board first.")
            return

        rotors = [self.rotor_left_combo.currentIndex(), self.rotor_middle_combo.currentIndex(), self.rotor_right_combo.currentIndex()]
        windows = [self.window_left_combo.currentIndex(), self.window_middle_combo.currentIndex(), self.window_right_combo.currentIndex()]
        rings = [self.ring_left_combo.currentIndex(), self.ring_middle_combo.currentIndex(), self.ring_right_combo.currentIndex()]
        plugboard = self.plugboard_widget.get_pairs()

        success, msg = self.model.set_rotors(*rotors)
        if not success:
            QMessageBox.warning(self, "Invalid Rotor Configuration", msg)
            return

        def complete(result):
            ok, response = result
            if ok:
                self.status_bar.showMessage("Configuration verified and applied to FPGA", 3000)
                if "windows" in response:
                    self.update_window_display(response["windows"])
            else:
                QMessageBox.critical(self, "Configuration Failed", response.get("error", "Unknown error"))

        self.run_job(lambda: self.serial.configure(rotors, windows, rings, plugboard), complete)

    # ── Encrypt / Decrypt ──────────────────────────────────────────────────────
    def encrypt_message(self):
        self.process_message("encrypt")

    def decrypt_message(self):
        self.process_message("decrypt")

    def process_message(self, operation: str):
        if not self.serial.is_connected():
            QMessageBox.warning(self, "Not Connected", "Please connect to the board first.")
            return

        message = self.input_text.toPlainText()
        try:
            message = EnigmaModel.normalize_message(message)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Message Text", str(exc))
            return

        self.output_text.clear()
        self.status_bar.showMessage(f"{operation.capitalize()}ing text on FPGA cipher engine...", 0)
        self.setCursor(Qt.WaitCursor)

        rotors = [self.rotor_left_combo.currentIndex(), self.rotor_middle_combo.currentIndex(), self.rotor_right_combo.currentIndex()]
        windows = [self.window_left_combo.currentIndex(), self.window_middle_combo.currentIndex(), self.window_right_combo.currentIndex()]
        rings = [self.ring_left_combo.currentIndex(), self.ring_middle_combo.currentIndex(), self.ring_right_combo.currentIndex()]
        plugs = self.plugboard_widget.get_pairs()

        def task():
            ok, response = self.serial.configure(rotors, windows, rings, plugs)
            if ok:
                return (self.serial.encrypt(message)
                        if operation == "encrypt"
                        else self.serial.decrypt(message))
            return ok, response

        def complete(result):
            ok, response = result
            if ok:
                self.output_text.setPlainText(response.get("result", ""))
                count = response.get("letters_processed", "?")
                self.status_bar.showMessage(
                    f"{'Encrypted' if operation == 'encrypt' else 'Decrypted'} "
                    f"{count} letter(s) on FPGA hardware", 5000
                )
                if "windows" in response:
                    self.update_window_display(response["windows"])
            else:
                QMessageBox.critical(self, f"{operation.capitalize()} Failed",
                                     response.get("error", "Unknown error"))
                self.status_bar.showMessage("Processing error encountered", 3000)

        self.run_job(task, complete)

    # ── Text Clear ─────────────────────────────────────────────────────────────
    def clear_messages(self):
        self.input_text.clear()
        self.output_text.clear()

    # ── Hardware Reset ─────────────────────────────────────────────────────────
    def reset_board(self):
        if not self.serial.is_connected():
            return

        def complete(result):
            ok, response = result
            if not ok:
                QMessageBox.critical(self, "Reset Failed", response.get("error", "Unknown error"))
                return

            self.model.set_rotors(0, 1, 2)
            self.model.set_windows(0, 0, 0)
            self.model.set_rings(0, 0, 0)

            for i, side in enumerate(("left", "middle", "right")):
                getattr(self, f"rotor_{side}_combo").setCurrentIndex(i)
                getattr(self, f"window_{side}_combo").setCurrentIndex(0)
                getattr(self, f"ring_{side}_combo").setCurrentIndex(0)

            self.clear_plugboard()
            self.output_text.clear()
            self.update_window_display([0, 0, 0])
            self.status_bar.showMessage("Hardware and settings reset to Rotor I–II–III / AAA / AAA", 5000)

        self.run_job(self.serial.reset, complete)

    # ── Self-test ──────────────────────────────────────────────────────────────
    def selftest_board(self):
        if not self.serial.is_connected():
            return

        def complete(result):
            ok, response = result
            if ok:
                self.status_bar.showMessage("✓ FPGA hardware self-test passed successfully", 5000)
            else:
                QMessageBox.critical(self, "Self-test Failed", response.get("error", "Unknown error"))

        self.run_job(self.serial.selftest, complete)

    # ── Plugboard Management ───────────────────────────────────────────────────
    def add_plugboard_pair(self):
        text, ok = QInputDialog.getText(
            self, "Add Plugboard Cable",
            "Enter two letters to pair without space (e.g. AB):"
        )
        if ok and text:
            text = text.upper().strip()
            if len(text) != 2 or not text.isalpha():
                QMessageBox.warning(self, "Invalid Pair", "Please enter exactly two letters A-Z (e.g. AB).")
                return

            if self.plugboard_widget.add_pair(text):
                self.model.add_plugboard_pair(text[0], text[1])
                self._sync_legacy_plugboard_list()
            else:
                QMessageBox.warning(self, "Invalid Pair", "Cannot connect pair: duplicate or maximum 13 pairs reached.")

    def remove_plugboard_pair(self):
        row = self.plugboard_list.currentRow()
        if row >= 0:
            item = self.plugboard_list.takeItem(row)
            pair_str = item.data(Qt.UserRole)
            self.plugboard_widget.remove_pair(pair_str)
            self.model.remove_plugboard_pair(row)

    def clear_plugboard(self):
        self.plugboard_widget.clear()
        self.plugboard_list.clear()
        self.model.clear_plugboard()

    def _sync_legacy_plugboard_list(self):
        self.plugboard_list.clear()
        for p in self.plugboard_widget.get_pairs():
            item = QListWidgetItem(f" {p[0]} ↔ {p[1]} ")
            item.setData(Qt.UserRole, p)
            self.plugboard_list.addItem(item)

    # ── Window Position Display ────────────────────────────────────────────────
    def update_window_display(self, windows: list):
        if len(windows) == 3:
            letters = [EnigmaModel.position_to_letter(w) for w in windows]
            self.inspection_porthole.set_windows(windows)
            self.window_display.setText(f"{letters[0]}  {letters[1]}  {letters[2]}")

    # ── Settings Persistence ───────────────────────────────────────────────────
    def load_settings(self):
        last_port = self.settings.get("last_port", "")
        if last_port:
            idx = self.port_combo.findData(last_port)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

        last_rotors = self.settings.get("last_rotors", [0, 1, 2])
        last_windows = self.settings.get("last_windows", [0, 0, 0])
        last_rings = self.settings.get("last_rings", [0, 0, 0])

        for i, side in enumerate(("left", "middle", "right")):
            getattr(self, f"rotor_{side}_combo").setCurrentIndex(last_rotors[i])
            getattr(self, f"window_{side}_combo").setCurrentIndex(last_windows[i])
            getattr(self, f"ring_{side}_combo").setCurrentIndex(last_rings[i])

        for pair in self.settings.get("last_plugboard", []):
            if len(pair) == 2:
                self.plugboard_widget.add_pair(pair)
                self.model.add_plugboard_pair(pair[0], pair[1])
        self._sync_legacy_plugboard_list()

    def save_settings(self):
        if port := self.port_combo.currentData():
            self.settings.set("last_port", port)
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
        self.settings.set("last_plugboard", self.plugboard_widget.get_pairs())
        self.settings.save()

    # ── Close Event ────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        if self.job is not None:
            event.ignore()
            self.status_bar.showMessage("Please wait for board operation to finish before closing", 3000)
            return
        if self.serial.is_connected():
            self.serial.disconnect()
        event.accept()
