"""Custom Enigma-themed widgets for the Shrike Fi desktop application.

LetterDrum         – Brass-framed cylindrical letter thumbwheel (replaces QComboBox A-Z)
RingDrum           – Nickel-beveled thumbwheel for Ring settings (Ringstellung)
RotorSelector      – Stamped brass plaque showing rotor type I-V (replaces QComboBox I-V)
InspectionPorthole – Tri-aperture brass viewing windows showing live FPGA rotor output
PlugboardWidget    – Interactive Steckerbrett with 26 brass letter sockets and colored cables
JewelIndicator     – Vintage faceted glass jewel pilot light for hardware status
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QRadialGradient,
    QPen, QBrush, QPainterPath
)

# ── Authentic Enigma Material Palette ─────────────────────────────────────────
CHASSIS_DARK    = QColor("#171615")
CHASSIS_PANEL   = QColor("#22201d")
CHASSIS_BEVEL   = QColor("#36322b")

BRASS_HIGHLIGHT = QColor("#fae19c")
BRASS_LIGHT     = QColor("#d9b257")
BRASS_MID       = QColor("#b88f36")
BRASS_DARK      = QColor("#7a5d20")
BRASS_DEEP      = QColor("#4a3710")

NICKEL_LIGHT    = QColor("#d5d8dc")
NICKEL_MID      = QColor("#95a5a6")
NICKEL_DARK     = QColor("#566573")

IVORY_ENGRAVED  = QColor("#f4ede0")
IVORY_MUTED     = QColor("#b8b0a2")
SLOT_BLACK      = QColor("#0d0c0a")

CABLE_COLORS = [
    QColor("#e74c3c"),  # Crimson
    QColor("#3498db"),  # Azure
    QColor("#2ecc71"),  # Emerald
    QColor("#f39c12"),  # Amber
    QColor("#9b59b6"),  # Amethyst
    QColor("#1abc9c"),  # Turquoise
    QColor("#e67e22"),  # Tangerine
    QColor("#e84393"),  # Rose
    QColor("#00b894"),  # Mint
    QColor("#6c5ce7"),  # Iris
    QColor("#fdcb6e"),  # Sunflower
    QColor("#74b9ff"),  # Sky
    QColor("#a29bfe"),  # Lavender
]


# ═══════════════════════════════════════════════════════════════════════════════
#  JewelIndicator
# ═══════════════════════════════════════════════════════════════════════════════
class JewelIndicator(QWidget):
    """Faceted glass jewel indicator lamp in a brass bezel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self._state = "disconnected"

    def set_state(self, state: str):
        if state != self._state:
            self._state = state
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2.0 - 1.5

        # Brass outer rim
        rim = QRadialGradient(cx - 2, cy - 2, r + 2)
        rim.setColorAt(0.0, BRASS_HIGHLIGHT)
        rim.setColorAt(0.6, BRASS_MID)
        rim.setColorAt(1.0, BRASS_DEEP)
        p.setPen(QPen(BRASS_DEEP, 1))
        p.setBrush(rim)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Jewel inner lens
        jr = r - 2.5
        glow = QRadialGradient(cx - 1.5, cy - 1.5, jr)
        if self._state == "connected":
            glow.setColorAt(0.0, QColor("#b9f6ca"))
            glow.setColorAt(0.3, QColor("#00e676"))
            glow.setColorAt(0.8, QColor("#008a3e"))
            glow.setColorAt(1.0, QColor("#004d20"))
        elif self._state == "busy":
            glow.setColorAt(0.0, QColor("#ffe57f"))
            glow.setColorAt(0.4, QColor("#ffab00"))
            glow.setColorAt(0.8, QColor("#c67100"))
            glow.setColorAt(1.0, QColor("#5d3600"))
        elif self._state == "error":
            glow.setColorAt(0.0, QColor("#ff8a80"))
            glow.setColorAt(0.4, QColor("#ff1744"))
            glow.setColorAt(0.8, QColor("#b71c1c"))
            glow.setColorAt(1.0, QColor("#4a0007"))
        else:  # disconnected
            glow.setColorAt(0.0, QColor("#555555"))
            glow.setColorAt(0.5, QColor("#333333"))
            glow.setColorAt(1.0, QColor("#1a1a1a"))

        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QPointF(cx, cy), jr, jr)

        # Specular reflection highlight
        p.setBrush(QColor(255, 255, 255, 110 if self._state != "disconnected" else 40))
        p.drawEllipse(QPointF(cx - 2, cy - 2.5), jr * 0.45, jr * 0.25)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  LetterDrum (Window Position Cylindrical Thumbwheel)
# ═══════════════════════════════════════════════════════════════════════════════
class LetterDrum(QWidget):
    """Cylindrical thumbwheel showing A-Z through an aperture in a brass housing."""

    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._hover = False
        self.setFixedSize(66, 92)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("Scroll wheel or click top/bottom to step rotor position (A–Z)")

    def currentIndex(self) -> int:
        return self._value

    def setCurrentIndex(self, v: int):
        v = v % 26
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)
            self.update()

    def currentLetter(self) -> str:
        return chr(65 + self._value)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Brass outer housing with chamfer
        fg = QLinearGradient(0, 0, w, 0)
        fg.setColorAt(0.0, BRASS_DARK)
        fg.setColorAt(0.18, BRASS_LIGHT)
        fg.setColorAt(0.5, BRASS_MID)
        fg.setColorAt(0.82, BRASS_HIGHLIGHT)
        fg.setColorAt(1.0, BRASS_DEEP)
        p.setPen(QPen(QColor("#2d220b"), 1.2))
        p.setBrush(fg)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 5, 5)

        # Knurled grip ridges on edges
        for ry in (12, 24, 36, 48, 60, 72, 80):
            p.setPen(QPen(QColor("#3d2e0e"), 1.0))
            p.drawLine(3, ry, 6, ry)
            p.drawLine(w - 7, ry, w - 4, ry)
            p.setPen(QPen(BRASS_HIGHLIGHT, 0.8))
            p.drawLine(3, ry + 1, 6, ry + 1)
            p.drawLine(w - 7, ry + 1, w - 4, ry + 1)

        # Recessed aperture slot
        slot = QRectF(8, 4, w - 16, h - 8)
        p.setPen(QPen(QColor("#15130f"), 1.2))
        p.setBrush(SLOT_BLACK)
        p.drawRoundedRect(slot, 3, 3)

        # Drum letters
        cy = slot.center().y()
        cell_h = slot.height() / 3.0

        for offset in (-1, 0, 1):
            char = chr(65 + (self._value + offset) % 26)
            y_pos = cy + offset * cell_h

            if offset == 0:
                band = QRectF(slot.left() + 1, y_pos - cell_h * 0.46, slot.width() - 2, cell_h * 0.92)
                bg = QLinearGradient(0, band.top(), 0, band.bottom())
                bg.setColorAt(0.0, QColor("#ab8224"))
                bg.setColorAt(0.35, BRASS_HIGHLIGHT)
                bg.setColorAt(0.7, QColor("#e8c974"))
                bg.setColorAt(1.0, QColor("#99701a"))
                p.setPen(QPen(QColor("#543f0c"), 1))
                p.setBrush(bg)
                p.drawRoundedRect(band, 2, 2)

                p.setFont(QFont("Times New Roman", 17, QFont.Bold))
                p.setPen(QColor("#150e03"))
                p.drawText(band, Qt.AlignCenter, char)

                p.setPen(QPen(QColor(255, 255, 255, 80), 1))
                p.drawLine(band.left() + 2, band.top() + 1, band.right() - 2, band.top() + 1)
            else:
                p.setFont(QFont("Times New Roman", 12))
                p.setPen(QColor(200, 185, 160, 110))
                cell = QRectF(slot.left(), y_pos - cell_h / 2, slot.width(), cell_h)
                p.drawText(cell, Qt.AlignCenter, char)

        if self._hover:
            p.setPen(QPen(BRASS_HIGHLIGHT, 1.0))
            p.setFont(QFont("Arial", 7, QFont.Bold))
            p.drawText(QRectF(slot.left(), slot.top() + 1, slot.width(), 8), Qt.AlignCenter, "▲")
            p.drawText(QRectF(slot.left(), slot.bottom() - 9, slot.width(), 8), Qt.AlignCenter, "▼")

        p.end()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.setCurrentIndex(self._value - 1 if delta > 0 else self._value + 1)
        event.accept()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.position().y() < self.height() / 2:
            self.setCurrentIndex(self._value - 1)
        else:
            self.setCurrentIndex(self._value + 1)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Left):
            self.setCurrentIndex(self._value - 1)
        elif event.key() in (Qt.Key_Down, Qt.Key_Right):
            self.setCurrentIndex(self._value + 1)
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()


# ═══════════════════════════════════════════════════════════════════════════════
#  RingDrum (Ring Setting / Ringstellung)
# ═══════════════════════════════════════════════════════════════════════════════
class RingDrum(QWidget):
    """Compact nickel-steel thumbwheel for Ring settings (0-25 / A-Z)."""

    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._hover = False
        self.setFixedSize(66, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("Ring setting (Ringstellung): scroll or click to change internal wiring offset")

    def currentIndex(self) -> int:
        return self._value

    def setCurrentIndex(self, v: int):
        v = v % 26
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)
            self.update()

    def currentLetter(self) -> str:
        return chr(65 + self._value)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Nickel-plated steel frame
        bg = QLinearGradient(0, 0, w, 0)
        bg.setColorAt(0.0, NICKEL_DARK)
        bg.setColorAt(0.3, NICKEL_LIGHT)
        bg.setColorAt(0.7, NICKEL_MID)
        bg.setColorAt(1.0, NICKEL_DARK)
        p.setPen(QPen(QColor("#2c3e50"), 1))
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 4, 4)

        # Slot aperture
        slot = QRectF(6, 3, w - 12, h - 6)
        p.setBrush(SLOT_BLACK)
        p.setPen(QPen(QColor("#1a252f"), 1))
        p.drawRoundedRect(slot, 2, 2)

        # Active central band
        band = QRectF(slot.left() + 1, slot.top() + 2, slot.width() - 2, slot.height() - 4)
        bgrad = QLinearGradient(0, band.top(), 0, band.bottom())
        bgrad.setColorAt(0.0, QColor("#e2e5e8"))
        bgrad.setColorAt(0.5, QColor("#ffffff"))
        bgrad.setColorAt(1.0, QColor("#bdc3c7"))
        p.setBrush(bgrad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(band, 2, 2)

        # Letter + numerical offset: e.g. "A · 01"
        char = chr(65 + self._value)
        num_str = f"{self._value + 1:02d}"

        p.setFont(QFont("Times New Roman", 12, QFont.Bold))
        p.setPen(QColor("#17202a"))
        p.drawText(QRectF(band.left() + 4, band.top(), band.width() / 2 - 2, band.height()),
                   Qt.AlignCenter, char)

        p.setFont(QFont("Courier New", 9, QFont.Bold))
        p.setPen(QColor("#566573"))
        p.drawText(QRectF(band.left() + band.width() / 2 - 2, band.top(), band.width() / 2, band.height()),
                   Qt.AlignCenter, num_str)

        if self._hover:
            p.setPen(QPen(QColor("#2980b9"), 1))
            p.setFont(QFont("Arial", 7))
            p.drawText(QRectF(0, 0, 6, h), Qt.AlignCenter, "◀")
            p.drawText(QRectF(w - 6, 0, 6, h), Qt.AlignCenter, "▶")

        p.end()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.setCurrentIndex(self._value - 1 if delta > 0 else self._value + 1)
        event.accept()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.position().x() < self.width() / 2:
            self.setCurrentIndex(self._value - 1)
        else:
            self.setCurrentIndex(self._value + 1)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.setCurrentIndex(self._value - 1)
        elif event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.setCurrentIndex(self._value + 1)
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()


# ═══════════════════════════════════════════════════════════════════════════════
#  RotorSelector (Roman Numeral Rotor Type Plaque)
# ═══════════════════════════════════════════════════════════════════════════════
class RotorSelector(QWidget):
    """Heavy brass plaque displaying the installed rotor type (I, II, III, IV, V)."""

    NAMES = ["I", "II", "III", "IV", "V"]
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._hover = False
        self.setFixedSize(86, 34)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("Rotor Model: Click left/right or scroll to switch between I, II, III, IV, V")

    def addItems(self, _items):
        """No-op kept for drop-in compatibility with QComboBox code."""

    def currentIndex(self) -> int:
        return self._value

    def setCurrentIndex(self, v: int):
        v = max(0, min(4, v))
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Raised brass plaque gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, BRASS_HIGHLIGHT)
        grad.setColorAt(0.2, BRASS_LIGHT)
        grad.setColorAt(0.8, BRASS_MID)
        grad.setColorAt(1.0, BRASS_DEEP)

        p.setPen(QPen(QColor("#3d2f10"), 1.2))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 5, 5)

        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawLine(3, 2, w - 4, 2)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2d1f05"))
        p.drawEllipse(QPointF(4, h / 2.0), 1.4, 1.4)
        p.drawEllipse(QPointF(w - 4, h / 2.0), 1.4, 1.4)

        name = self.NAMES[self._value]
        p.setFont(QFont("Georgia", 15, QFont.Bold))
        p.setPen(QColor(255, 255, 255, 60))
        p.drawText(QRectF(0, 1, w, h), Qt.AlignCenter, name)
        p.setPen(QColor("#1f1505"))
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, name)

        arrow_alpha = 160 if self._hover else 75
        p.setFont(QFont("Arial", 8, QFont.Bold))
        p.setPen(QColor(45, 30, 8, arrow_alpha))
        p.drawText(QRectF(8, 0, 12, h), Qt.AlignCenter, "◀")
        p.drawText(QRectF(w - 20, 0, 12, h), Qt.AlignCenter, "▶")

        p.end()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.position().x() < self.width() / 2:
            self.setCurrentIndex((self._value - 1) % 5)
        else:
            self.setCurrentIndex((self._value + 1) % 5)
        event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.setCurrentIndex((self._value - 1) % 5 if delta > 0 else (self._value + 1) % 5)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.setCurrentIndex((self._value - 1) % 5)
        elif event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.setCurrentIndex((self._value + 1) % 5)
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()


# ═══════════════════════════════════════════════════════════════════════════════
#  InspectionPorthole (Final Live Rotor Windows on Top Chassis)
# ═══════════════════════════════════════════════════════════════════════════════
class InspectionPorthole(QWidget):
    """Tri-aperture brass inspection plate showing the live stepped rotor positions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._letters = ["A", "A", "A"]
        self.setFixedHeight(50)
        self.setMinimumWidth(260)
        self.setToolTip(
            "Final Rotor Position Windows:\n"
            "Shows where the rotors stopped on the physical FPGA after processing.\n"
            "Note: For decryption, always retain your starting INITIAL windows."
        )

    def set_letters(self, l_str: str):
        parts = [c for c in l_str.upper() if c.isalpha()]
        if len(parts) == 3:
            self._letters = parts
            self.update()

    def set_windows(self, windows: list):
        if len(windows) == 3:
            self._letters = [chr(65 + (w % 26)) for w in windows]
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        plate_w = min(w - 20, 270)
        plate_x = (w - plate_w) / 2.0
        plate = QRectF(plate_x, 2, plate_w, h - 4)

        p_grad = QLinearGradient(0, plate.top(), 0, plate.bottom())
        p_grad.setColorAt(0.0, BRASS_LIGHT)
        p_grad.setColorAt(0.5, BRASS_MID)
        p_grad.setColorAt(1.0, BRASS_DARK)

        p.setPen(QPen(QColor("#2d2008"), 1))
        p.setBrush(p_grad)
        p.drawRoundedRect(plate, 6, 6)

        diameter = h - 14
        spacing = (plate_w - 3 * diameter) / 4.0
        cy = plate.center().y()

        for i in range(3):
            cx = plate_x + spacing + i * (diameter + spacing) + diameter / 2.0
            r = diameter / 2.0

            bezel = QRadialGradient(cx - 2, cy - 2, r)
            bezel.setColorAt(0.0, BRASS_HIGHLIGHT)
            bezel.setColorAt(0.7, BRASS_DARK)
            bezel.setColorAt(1.0, QColor("#1f1505"))
            p.setPen(QPen(QColor("#1f1505"), 1))
            p.setBrush(bezel)
            p.drawEllipse(QPointF(cx, cy), r, r)

            glass = QRadialGradient(cx, cy, r - 3)
            glass.setColorAt(0.0, QColor("#1a150c"))
            glass.setColorAt(0.8, QColor("#090704"))
            glass.setColorAt(1.0, QColor("#000000"))
            p.setPen(Qt.NoPen)
            p.setBrush(glass)
            p.drawEllipse(QPointF(cx, cy), r - 3, r - 3)

            p.setFont(QFont("Times New Roman", 15, QFont.Bold))
            p.setPen(QColor("#ffda8a"))
            letter_rect = QRectF(cx - r, cy - r, diameter, diameter)
            p.drawText(letter_rect, Qt.AlignCenter, self._letters[i])

            p.setPen(QPen(QColor(255, 255, 255, 65), 1))
            p.drawArc(QRectF(cx - r + 3, cy - r + 3, diameter - 6, diameter - 6),
                      45 * 16, 90 * 16)

        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  PlugboardWidget (Tactile Steckerbrett Dual-Jack Panel)
# ═══════════════════════════════════════════════════════════════════════════════
class PlugboardWidget(QWidget):
    """Interactive Steckerbrett with 26 dual-contact letter sockets and colored patch cords."""

    pairsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pairs: dict[str, str] = {}
        self._colors: dict[str, int] = {}
        self._selected: str | None = None
        self._next_color = 0
        self._hover_letter: str | None = None

        self.setFixedHeight(120)
        self.setMinimumWidth(560)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setToolTip("Click any socket to select, then click another to plug a cable. Click plugged socket to disconnect.")

    def get_pairs(self) -> list[str]:
        seen = set()
        res = []
        for a, b in self._pairs.items():
            key = tuple(sorted([a, b]))
            if key not in seen:
                seen.add(key)
                res.append(a + b)
        return res

    def pair_count(self) -> int:
        return len(self._pairs) // 2

    def clear(self):
        self._pairs.clear()
        self._colors.clear()
        self._selected = None
        self._next_color = 0
        self.pairsChanged.emit()
        self.update()

    def add_pair(self, pair_str: str) -> bool:
        if len(pair_str) != 2:
            return False
        a, b = pair_str[0].upper(), pair_str[1].upper()
        if not (a.isalpha() and b.isalpha()) or a == b:
            return False
        if a in self._pairs or b in self._pairs:
            return False
        if self.pair_count() >= 13:
            return False

        ci = self._next_color % len(CABLE_COLORS)
        self._next_color += 1
        self._pairs[a] = b
        self._pairs[b] = a
        self._colors[a] = ci
        self._colors[b] = ci
        self.pairsChanged.emit()
        self.update()
        return True

    def remove_pair(self, pair_str: str):
        if len(pair_str) >= 2:
            a, b = pair_str[0].upper(), pair_str[1].upper()
            self._pairs.pop(a, None)
            self._pairs.pop(b, None)
            self._colors.pop(a, None)
            self._colors.pop(b, None)
            self.pairsChanged.emit()
            self.update()

    def _socket_geometry(self) -> dict[str, QRectF]:
        w = self.width()
        sock_w = min(40.0, (w - 20) / 13.5)
        sock_h = 40.0
        gap_x = (w - 20 - 13 * sock_w) / 12.0
        start_x = 10.0
        row1_y = 8.0
        row2_y = 56.0

        rects: dict[str, QRectF] = {}
        for i in range(26):
            char = chr(65 + i)
            row = i // 13
            col = i % 13
            x = start_x + col * (sock_w + gap_x)
            y = row1_y if row == 0 else row2_y
            rects[char] = QRectF(x, y, sock_w, sock_h)
        return rects

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        chassis = QLinearGradient(0, 0, 0, h)
        chassis.setColorAt(0.0, QColor("#1e1c18"))
        chassis.setColorAt(1.0, QColor("#141311"))
        p.setPen(QPen(CHASSIS_BEVEL, 1.2))
        p.setBrush(chassis)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 6, 6)

        p.setFont(QFont("Arial", 9))
        if self._selected:
            p.setPen(QColor("#ffd54f"))
            p.drawText(QRectF(0, h - 16, w, 14), Qt.AlignCenter,
                       f"Cable plugged into [{self._selected}] — click a second socket to complete pair")
        elif self.pair_count() == 0:
            p.setPen(QColor("#80796d"))
            p.drawText(QRectF(0, h - 16, w, 14), Qt.AlignCenter,
                       "Plugboard empty (identity mapping) · Click any socket to plug a cable")
        else:
            p.setPen(QColor("#a9a296"))
            pairs_str = "   ".join([f"{a}↔{b}" for a, b in sorted(self._pairs.items()) if a < b])
            p.drawText(QRectF(0, h - 16, w, 14), Qt.AlignCenter,
                       f"{self.pair_count()} cable(s) active:   {pairs_str}   (Click socket to unplug)")

        rects = self._socket_geometry()
        for char, r in rects.items():
            is_paired = char in self._pairs
            is_sel = char == self._selected
            is_hover = char == self._hover_letter

            if is_paired:
                col = CABLE_COLORS[self._colors[char]]
                p.setBrush(col.darker(280))
                p.setPen(QPen(col, 1.8))
            elif is_sel:
                p.setBrush(QColor("#403010"))
                p.setPen(QPen(BRASS_HIGHLIGHT, 2.0))
            elif is_hover:
                p.setBrush(QColor("#2d2922"))
                p.setPen(QPen(BRASS_LIGHT, 1.2))
            else:
                p.setBrush(QColor("#181714"))
                p.setPen(QPen(QColor("#3d3830"), 1.0))

            p.drawRoundedRect(r, 4, 4)

            p.setFont(QFont("Times New Roman", 11, QFont.Bold))
            if is_paired:
                p.setPen(CABLE_COLORS[self._colors[char]].lighter(130))
            elif is_sel:
                p.setPen(BRASS_HIGHLIGHT)
            elif is_hover:
                p.setPen(IVORY_ENGRAVED)
            else:
                p.setPen(IVORY_MUTED)
            p.drawText(QRectF(r.left(), r.top() + 2, r.width(), 16), Qt.AlignCenter, char)

            hole_y = r.top() + 24.0
            h1_x = r.center().x() - 4.5
            h2_x = r.center().x() + 4.5

            if is_paired:
                col = CABLE_COLORS[self._colors[char]]
                p.setPen(QPen(QColor("#111"), 0.8))
                p.setBrush(col)
                p.drawEllipse(QPointF(r.center().x(), hole_y), 6.5, 6.5)
                p.setBrush(BRASS_HIGHLIGHT)
                p.drawEllipse(QPointF(r.center().x(), hole_y), 2.0, 2.0)
            else:
                for hx in (h1_x, h2_x):
                    p.setPen(QPen(BRASS_DARK, 0.8))
                    p.setBrush(QColor("#0a0a09"))
                    p.drawEllipse(QPointF(hx, hole_y), 2.8, 2.8)

        p.end()

    def mousePressEvent(self, event):
        pos = event.position()
        rects = self._socket_geometry()
        for char, r in rects.items():
            if r.contains(pos):
                self._handle_socket_click(char)
                return
        self._selected = None
        self.update()

    def _handle_socket_click(self, char: str):
        if char in self._pairs:
            partner = self._pairs.pop(char)
            self._pairs.pop(partner, None)
            self._colors.pop(char, None)
            self._colors.pop(partner, None)
            self._selected = None
            self.pairsChanged.emit()
        elif self._selected is None:
            self._selected = char
        elif self._selected == char:
            self._selected = None
        else:
            a, b = self._selected, char
            if self.pair_count() < 13 and a != b and a not in self._pairs and b not in self._pairs:
                ci = self._next_color % len(CABLE_COLORS)
                self._next_color += 1
                self._pairs[a] = b
                self._pairs[b] = a
                self._colors[a] = ci
                self._colors[b] = ci
                self.pairsChanged.emit()
            self._selected = None
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        rects = self._socket_geometry()
        old = self._hover_letter
        self._hover_letter = None
        for char, r in rects.items():
            if r.contains(pos):
                self._hover_letter = char
                break
        if old != self._hover_letter:
            self.update()

    def leaveEvent(self, event):
        self._hover_letter = None
        self.update()
