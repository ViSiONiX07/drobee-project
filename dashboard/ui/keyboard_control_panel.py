
import math
import time
from collections import deque

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QSizePolicy,
    QProgressBar,
)


# ============================================================
# BEE-BRAIN KEYBOARD TEST
# Visual keyboard input diagnostics — no physical motor output.
# ============================================================

BG = "#111310"
PANEL = "#272a26"
PANEL_DARK = "#191c18"
PANEL_BORDER = "#393d35"
TEXT = "#e7e5dc"
MUTED = "#a49b8d"
COPPER = "#ffb27b"
AMBER = "#f1c15d"
MINT = "#a4cfb9"
GREEN = "#a4cfb9"
RED = "#e98776"


class AttitudeGauge(QWidget):
    """Painted pitch/roll gauge with a visual ±15-degree envelope."""

    def __init__(self, parent=None):
        """Initialize a level gauge with a 15-degree visual envelope."""
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.clamp_degrees = 15.0
        self.setMinimumSize(230, 220)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_attitude(self, roll, pitch):
        """Store roll and pitch in degrees and request a repaint.

        Float-conversion errors propagate. Stored angles are not clamped;
        only the painted marker is limited to the visual envelope.
        """
        self.roll = float(roll)
        self.pitch = float(pitch)
        self.update()

    def paintEvent(self, event):
        """Paint angle readouts and a marker clamped to the visual tilt envelope."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PANEL_DARK))

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = max(45, min(w, h) * 0.36)

        # Gauge rings.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#353b32"), 1))
        painter.drawEllipse(
            QPointF(cx, cy), radius * 1.16, radius * 1.16
        )

        painter.setPen(QPen(QColor(AMBER), 1.4, Qt.PenStyle.DashLine))
        painter.drawEllipse(
            QPointF(cx, cy), radius, radius
        )

        painter.setPen(QPen(QColor(MINT), 1))
        painter.drawEllipse(
            QPointF(cx, cy), radius * 0.55, radius * 0.55
        )

        # Crosshair axes.
        painter.setPen(QPen(QColor("#665f51"), 1))
        painter.drawLine(
            int(cx - radius * 1.25), int(cy),
            int(cx + radius * 1.25), int(cy),
        )
        painter.drawLine(
            int(cx), int(cy - radius * 1.25),
            int(cx), int(cy + radius * 1.25),
        )

        # Gauge angle is clamped to the visual envelope.
        roll = max(
            -self.clamp_degrees,
            min(self.clamp_degrees, self.roll),
        )
        pitch = max(
            -self.clamp_degrees,
            min(self.clamp_degrees, self.pitch),
        )

        # Roll moves the marker horizontally; pitch moves it vertically.
        marker_x = cx + (roll / self.clamp_degrees) * radius * 0.78
        marker_y = cy - (pitch / self.clamp_degrees) * radius * 0.78

        painter.setPen(QPen(QColor(COPPER), 2))
        painter.drawLine(
            int(cx - 14), int(cy), int(cx + 14), int(cy)
        )
        painter.drawLine(
            int(cx), int(cy - 14), int(cx), int(cy + 14)
        )

        painter.setPen(QPen(QColor(COPPER), 2))
        painter.setBrush(QBrush(QColor(COPPER)))
        painter.drawEllipse(
            QPointF(marker_x, marker_y), 5.5, 5.5
        )

        # Labels.
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(
            int(cx - radius - 23), int(cy + 4), "L"
        )
        painter.drawText(
            int(cx + radius + 12), int(cy + 4), "R"
        )
        painter.drawText(
            int(cx - 13), int(cy - radius - 9), "FWD"
        )
        painter.drawText(
            int(cx - 14), int(cy + radius + 16), "BWD"
        )

        painter.setPen(QColor(MINT))
        painter.drawText(
            int(cx - radius * 0.55),
            int(cy + radius * 0.55 + 15),
            "SAFE ENVELOPE",
        )

        painter.setPen(QColor(COPPER))
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.drawText(
            10, 18,
            f"R {self.roll:+.1f}°   P {self.pitch:+.1f}°",
        )

        painter.end()


class KeyboardControlPanel(QWidget):
    """Industrial keyboard diagnostics panel; visual simulation only."""

    MAX_TILT = 15.0
    DEGREES_PER_SECOND = 10.0
    TICK_MS = 16

    KEY_ACTIONS = {
        Qt.Key.Key_W: ("W", "PITCH FWD"),
        Qt.Key.Key_8: ("8", "PITCH FWD"),
        Qt.Key.Key_S: ("S", "PITCH BWD"),
        Qt.Key.Key_5: ("5", "PITCH BWD"),
        Qt.Key.Key_A: ("A", "ROLL L"),
        Qt.Key.Key_4: ("4", "ROLL L"),
        Qt.Key.Key_D: ("D", "ROLL R"),
        Qt.Key.Key_6: ("6", "ROLL R"),
    }

    def __init__(self, parent=None):
        """Build input diagnostics and start the clock, leaving motion stopped."""
        super().__init__(parent)

        self.setObjectName("KeyboardControlPanel")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.pressed_keys = set()
        self.keystrokes = 0
        self.last_event_time = None
        self.jitter_samples = deque(maxlen=20)
        self.event_times = deque(maxlen=20)
        self.event_log_lines = deque(maxlen=100)
        self.last_action = "NONE"

        self.motion_timer = QTimer(self)
        self.motion_timer.setInterval(self.TICK_MS)
        self.motion_timer.timeout.connect(self.update_motion)

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(250)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start()

        self.started_at = time.monotonic()

        self.build_ui()
        self.refresh_view()
        self.apply_theme()
        self.add_log("SYSTEM", "Keyboard diagnostics initialized")

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def apply_theme(self):
        """Apply the keyboard diagnostics palette and component styles."""
        self.setStyleSheet("""
            QWidget#KeyboardControlPanel {
                background: #111310;
                color: #e7e5dc;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #e7e5dc;
                background: transparent;
                border: none;
            }
            QFrame#Card {
                background: #272a26;
                border: 1px solid #393d35;
                border-radius: 8px;
            }
            QFrame#Inset {
                background: #191c18;
                border: 1px solid #30352e;
                border-radius: 5px;
            }
            QPushButton {
                background: #343830;
                color: #e7e5dc;
                border: 1px solid #4b5045;
                border-radius: 4px;
                padding: 8px 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #45483d;
                border-color: #ffb27b;
            }
            QPushButton:pressed {
                background: #5b4432;
            }
        """)

    def build_ui(self):
        """Build key indicators, the attitude gauge, timing readouts, and event log."""
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # Page heading.
        heading_card = self.card()
        heading = QVBoxLayout(heading_card)
        heading.setContentsMargins(14, 10, 14, 10)
        heading.setSpacing(4)

        title_row = QHBoxLayout()
        title = QLabel("Diag / Input Test / Key Actuation Matrix")
        title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        title_row.addWidget(title, 1)

        self.bench_badge = self.badge("TEST BENCH ACTIVE", MINT)
        title_row.addWidget(self.bench_badge)
        heading.addLayout(title_row)

        subtitle = QLabel(
            "Hardware-in-the-loop input diagnostics  ·  "
            "Visual attitude response  ·  No motor commands"
        )
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        heading.addWidget(subtitle)

        status_row = QHBoxLayout()
        self.driver_badge = self.badge(
            "DRIVER: Qt Key Events", COPPER
        )
        self.clamp_badge = self.badge(
            "VISUAL CLAMP: ±15.0°", AMBER
        )
        self.poll_badge = self.badge(
            "POLL: 62.5 Hz UI TIMER", MINT
        )
        status_row.addWidget(self.driver_badge)
        status_row.addWidget(self.clamp_badge)
        status_row.addWidget(self.poll_badge)
        status_row.addStretch()
        heading.addLayout(status_row)
        root.addWidget(heading_card)

        # Three main columns.
        columns = QHBoxLayout()
        columns.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(self.build_primary_input())
        left.addWidget(self.build_numpad_input())
        left.addStretch()

        center = QVBoxLayout()
        center.setSpacing(8)
        center.addWidget(self.build_attitude_card(), 1)
        center.addWidget(self.build_safety_card())

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(self.build_diagnostics_card())
        right.addWidget(self.build_mapping_card())
        right.addStretch()

        columns.addLayout(left, 32)
        columns.addLayout(center, 33)
        columns.addLayout(right, 35)
        root.addLayout(columns, 1)

        # Bottom strip and event console.
        footer = self.card()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 7, 10, 7)
        self.footer_status = QLabel("●  KEYBOARD READY")
        self.footer_status.setStyleSheet(
            f"color: {MINT}; font-family: Consolas; font-size: 10px;"
        )
        self.footer_orientation = QLabel("ROLL: +0.0°  PITCH: +0.0°")
        self.footer_orientation.setStyleSheet(
            f"color: {COPPER}; font-family: Consolas; font-size: 10px;"
        )
        self.uptime_label = QLabel("UPTIME: 00:00")
        self.uptime_label.setStyleSheet(
            f"color: {MUTED}; font-family: Consolas; font-size: 10px;"
        )
        footer_layout.addWidget(self.footer_status, 1)
        footer_layout.addWidget(self.footer_orientation, 1)
        footer_layout.addWidget(self.uptime_label)
        root.addWidget(footer)

        log_card = self.card()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(10, 7, 10, 7)
        log_layout.setSpacing(4)

        log_header = QHBoxLayout()
        log_title = QLabel("INPUT EVENT LOG")
        log_title.setStyleSheet(
            f"color: {COPPER}; font-weight: bold; font-size: 11px;"
        )
        self.log_count_label = QLabel("0 EVENTS")
        self.log_count_label.setStyleSheet(
            f"color: {MUTED}; font-family: Consolas; font-size: 10px;"
        )
        clear_log = QPushButton("CLEAR")
        clear_log.setFixedWidth(70)
        clear_log.clicked.connect(self.clear_log)
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(self.log_count_label)
        log_header.addWidget(clear_log)
        log_layout.addLayout(log_header)

        self.event_log = QLabel("Waiting for keyboard input…")
        self.event_log.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.event_log.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.event_log.setMinimumHeight(75)
        self.event_log.setMaximumHeight(105)
        self.event_log.setStyleSheet(
            "background: #10120f; border: 1px solid #30352e;"
            "border-radius: 4px; padding: 7px;"
            "font-family: Consolas, monospace; font-size: 10px;"
            f"color: {MINT};"
        )
        log_layout.addWidget(self.event_log)
        root.addWidget(log_card)

    def card(self, inset=False):
        """Return an empty card frame, using the recessed style when inset is true."""
        frame = QFrame()
        frame.setObjectName("Inset" if inset else "Card")
        return frame

    def section_title(self, text, tag=None, tag_color=MINT):
        """Return a heading layout with an optional colored status badge."""
        row = QHBoxLayout()
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        row.addWidget(label, 1)
        if tag:
            badge = self.badge(tag, tag_color)
            row.addWidget(badge)
        return row

    def badge(self, text, color):
        """Return a wrapping status label styled with the supplied color."""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"background: #111310; color: {color};"
            "border: 1px solid #383b32; border-radius: 3px;"
            "padding: 4px 6px; font-family: Consolas;"
            "font-size: 9px; font-weight: bold;"
        )
        return label

    def build_primary_input(self):
        """Return WASD key indicators and the instant-level button."""
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(9)

        layout.addLayout(self.section_title(
            "Primary Flight Input: WASD", "LAYER 01", COPPER
        ))

        description = QLabel(
            "Hold a key to change the visual attitude. "
            "Release it to stop the input."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {MUTED}; font-size: 10px;")
        layout.addWidget(description)

        self.key_buttons = {}
        grid = QGridLayout()
        grid.setSpacing(5)

        positions = [
            (Qt.Key.Key_W, 0, 1),
            (Qt.Key.Key_A, 1, 0),
            (Qt.Key.Key_S, 1, 1),
            (Qt.Key.Key_D, 1, 2),
        ]

        for key, row, column in positions:
            name, action = self.KEY_ACTIONS[key]
            button = self.make_keycap(name, action)
            self.key_buttons[key] = button
            grid.addWidget(button, row, column)

        layout.addLayout(grid)

        self.space_button = QPushButton(
            "SPACEBAR  —  INSTANT LEVEL"
        )
        self.space_button.setMinimumHeight(37)
        self.space_button.clicked.connect(self.reset_orientation)
        layout.addWidget(self.space_button)

        self.primary_held = QLabel("HELD: NONE")
        self.primary_held.setStyleSheet(
            f"color: {MINT}; font-family: Consolas; font-size: 10px;"
        )
        layout.addWidget(self.primary_held)
        return frame

    def build_numpad_input(self):
        """Return numeric-key indicators, with unbound 7 and 9 disabled."""
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(8)

        layout.addLayout(self.section_title(
            "Secondary Co-Pilot Input: Numpad", "LAYER 02", MINT
        ))

        grid = QGridLayout()
        grid.setSpacing(5)

        disabled_keys = [
            ("7", "UNBOUND"), ("9", "UNBOUND"),
        ]
        for name, action in disabled_keys:
            button = self.make_keycap(name, action, disabled=True)
            grid.addWidget(button, 0, 0 if name == "7" else 2)

        for key, row, col in [
            (Qt.Key.Key_8, 0, 1),
            (Qt.Key.Key_4, 1, 0),
            (Qt.Key.Key_5, 1, 1),
            (Qt.Key.Key_6, 1, 2),
        ]:
            name, action = self.KEY_ACTIONS[key]
            button = self.make_keycap(name, action)
            self.key_buttons[key] = button
            grid.addWidget(button, row, col)

        layout.addLayout(grid)

        self.numpad_status = QLabel("CO-PILOT: READY")
        self.numpad_status.setStyleSheet(
            f"color: {MINT}; font-family: Consolas; font-size: 10px;"
        )
        layout.addWidget(self.numpad_status)
        return frame

    def make_keycap(self, key, action, disabled=False):
        """Return a key-and-action indicator button without binding motion input."""
        button = QPushButton()
        button.setMinimumSize(58, 62)
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        button.setText(f"{key}\n{action}")
        button.setEnabled(not disabled)
        button.setProperty("active", False)

        if disabled:
            button.setStyleSheet(
                "QPushButton { background: #1b1e19; color: #5c6057;"
                "border: 1px solid #292d25; border-radius: 4px;"
                "font-family: Consolas; font-size: 9px; }"
            )
        else:
            button.setStyleSheet(
                "QPushButton { background: #171a16; color: #e7e5dc;"
                "border: 1px solid #383d33; border-radius: 4px;"
                "font-family: Consolas; font-size: 10px;"
                "font-weight: bold; padding: 5px; }"
                "QPushButton:hover { border: 1px solid #ffb27b; }"
            )
        return button

    def build_attitude_card(self):
        """Return the tilt gauge and target-angle and envelope-margin readouts."""
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(7)

        layout.addLayout(self.section_title(
            "Attitude Response Gauge", "CLAMP: ±15.0°", AMBER
        ))

        self.gauge = AttitudeGauge()
        layout.addWidget(self.gauge, 1)

        metrics = QGridLayout()
        metrics.setSpacing(5)
        self.pitch_value = self.make_metric(
            metrics, 0, "TARGET PITCH", "+0.0°", COPPER
        )
        self.roll_value = self.make_metric(
            metrics, 1, "TARGET ROLL", "+0.0°", COPPER
        )
        self.margin_value = self.make_metric(
            metrics, 2, "ENVELOPE MARGIN", "15.0°", MINT
        )
        layout.addLayout(metrics)
        return frame

    def make_metric(self, layout, column, title, value, color):
        """Add a metric tile at row zero in layout and return its value label."""
        frame = self.card(inset=True)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(8, 7, 8, 7)
        inner.setSpacing(4)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            f"color: {MUTED}; font-size: 9px; font-weight: bold;"
        )
        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {color}; font-family: Consolas;"
            "font-size: 18px; font-weight: bold;"
        )
        inner.addWidget(title_label)
        inner.addWidget(value_label)
        layout.addWidget(frame, 0, column)
        return value_label

    def build_safety_card(self):
        """Return the visual-clamp notice and orientation-reset button."""
        frame = self.card()
        row = QHBoxLayout(frame)
        row.setContentsMargins(11, 9, 11, 9)

        message = QLabel(
            "⚠  VISUAL SAFETY CLAMP\n"
            "Keyboard input is limited to ±15°. "
            "This page does not control physical actuators."
        )
        message.setWordWrap(True)
        message.setStyleSheet(f"color: {AMBER}; font-size: 10px;")
        row.addWidget(message, 1)

        reset = QPushButton("ZERO\nOFFSETS")
        reset.setMinimumWidth(90)
        reset.clicked.connect(self.reset_orientation)
        row.addWidget(reset)
        return frame

    def build_diagnostics_card(self):
        """Return key-event counts, interval timing, and interval-variation readouts."""
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(8)

        layout.addLayout(self.section_title(
            "HID Input Diagnostics", "SIMULATED", AMBER
        ))

        grid = QGridLayout()
        grid.setSpacing(6)

        self.keystrokes_value = self.make_metric(
            grid, 0, "KEYSTROKES DETECTED", "0", TEXT
        )
        self.debounce_value = self.make_metric(
            grid, 1, "EVENT INTERVAL", "-- ms", AMBER
        )
        self.poll_value = self.make_metric(
            grid, 2, "UI UPDATE RATE", "62.5 Hz", MINT
        )
        self.jitter_value = self.make_metric(
            grid, 3, "INTERVAL VARIATION", "-- ms", COPPER
        )

        layout.addLayout(grid)

        jitter_frame = self.card(inset=True)
        jitter_layout = QVBoxLayout(jitter_frame)
        jitter_layout.setContentsMargins(8, 7, 8, 7)
        self.jitter_title = QLabel("RECENT EVENT INTERVALS")
        self.jitter_title.setStyleSheet(
            f"color: {MUTED}; font-family: Consolas; font-size: 9px;"
        )
        jitter_layout.addWidget(self.jitter_title)

        self.jitter_bar = QProgressBar()
        self.jitter_bar.setRange(0, 100)
        self.jitter_bar.setValue(0)
        self.jitter_bar.setTextVisible(False)
        self.jitter_bar.setFixedHeight(8)
        self.jitter_bar.setStyleSheet(
            "QProgressBar { background: #30342d; border: none;"
            "border-radius: 3px; }"
            "QProgressBar::chunk { background: #ffb27b;"
            "border-radius: 3px; }"
        )
        jitter_layout.addWidget(self.jitter_bar)
        layout.addWidget(jitter_frame)
        return frame

    def build_mapping_card(self):
        """Return the key mapping and visual response-rate reference."""
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(11, 10, 11, 10)
        layout.setSpacing(7)

        layout.addLayout(self.section_title(
            "Mapping Specification & Action Rates", None
        ))

        rows = [
            ("W / 8", "Pitch Forward", "−10°/s"),
            ("S / 5", "Pitch Backward", "+10°/s"),
            ("A / 4", "Roll Left", "−10°/s"),
            ("D / 6", "Roll Right", "+10°/s"),
            ("SPACE", "Instant Level", "0° Lock"),
            ("ESC", "Release Keys", "Stop"),
        ]

        header = QHBoxLayout()
        for text, stretch in [
            ("KEY", 1), ("ACTION", 3), ("RATE", 1)
        ]:
            label = QLabel(text)
            label.setStyleSheet(
                f"color: {MUTED}; font-family: Consolas;"
                "font-size: 9px; font-weight: bold;"
            )
            header.addWidget(label, stretch)
        layout.addLayout(header)

        for key, action, rate in rows:
            row = QHBoxLayout()
            for text, stretch, color in [
                (key, 1, COPPER),
                (action, 3, TEXT),
                (rate, 1, MINT),
            ]:
                label = QLabel(text)
                label.setWordWrap(True)
                label.setStyleSheet(
                    f"color: {color}; font-family: Consolas;"
                    "font-size: 9px; padding: 4px 0;"
                )
                row.addWidget(label, stretch)
            layout.addLayout(row)

        warning = QLabel(
            "⚠ SIMULATION ONLY: rates are visual response rates. "
            "No USB HID hardware measurements are available."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            f"background: #191c18; color: {AMBER};"
            "border: 1px solid #393d35; border-radius: 4px;"
            "padding: 7px; font-size: 9px;"
        )
        layout.addWidget(warning)
        return frame

    # --------------------------------------------------------
    # Keyboard handling
    # --------------------------------------------------------

    def activate_controls(self):
        """Request keyboard focus and display the active input state."""
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.footer_status.setText("●  KEYBOARD ACTIVE")
        self.footer_status.setStyleSheet(
            f"color: {MINT}; font-family: Consolas; font-size: 10px;"
        )
        self.add_log("SYSTEM", "Keyboard focus activated")

    def keyPressEvent(self, event):
        """Handle mapped motion keys, Space to level, and Escape to release keys.

        Consume auto-repeat events without applying them. A newly held motion
        key starts the motion timer; unhandled keys go to the base widget.
        """
        key = event.key()

        if event.isAutoRepeat():
            event.accept()
            return

        if key in self.KEY_ACTIONS:
            if key not in self.pressed_keys:
                self.pressed_keys.add(key)
                self.register_key_event(key, "KEY_DOWN")
                if not self.motion_timer.isActive():
                    self.motion_timer.start()
                self.refresh_view()
            event.accept()
            return

        if key == Qt.Key.Key_Space:
            self.register_key_event(key, "LEVEL")
            self.reset_orientation()
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.release_all_keys()
            self.register_key_event(key, "RELEASE_ALL")
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Release a held key and stop the motion timer when none remain.

        Consume auto-repeat events without changing held keys; forward
        unhandled releases to the base widget.
        """
        key = event.key()

        if event.isAutoRepeat():
            event.accept()
            return

        if key in self.pressed_keys:
            self.pressed_keys.discard(key)
            self.register_key_event(key, "KEY_UP")

            if not self.pressed_keys:
                self.motion_timer.stop()

            self.refresh_view()
            event.accept()
            return

        super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        self.release_all_keys()
        super().focusOutEvent(event)

    def register_key_event(self, key, action):
        """Count a key event and refresh timing diagnostics and its log entry.

        key is a Qt key code; action labels the event. Intervals and their
        population standard deviation use milliseconds and the latest 20
        interval samples. Releases and control actions also count as events.
        """
        now = time.monotonic()
        self.keystrokes += 1

        if self.last_event_time is not None:
            interval_ms = (now - self.last_event_time) * 1000.0
            self.event_times.append(interval_ms)
            self.debounce_value.setText(f"{interval_ms:.1f} ms")

            if len(self.event_times) > 1:
                mean = sum(self.event_times) / len(self.event_times)
                variance = sum(
                    (sample - mean) ** 2
                    for sample in self.event_times
                ) / len(self.event_times)
                jitter = math.sqrt(variance)
                self.jitter_value.setText(f"{jitter:.2f} ms")
                self.jitter_bar.setValue(
                    min(100, int(jitter * 10))
                )

        self.last_event_time = now
        self.keystrokes_value.setText(f"{self.keystrokes:,}")

        key_name = self.KEY_ACTIONS.get(
            key, (Qt.Key(key).name, "")
        )[0]
        self.add_log(action, f"{key_name}  |  {self.describe_attitude()}")

    def describe_attitude(self):
        """Return signed roll and pitch readouts in degrees."""
        return f"Roll {self.roll:+.1f}°  Pitch {self.pitch:+.1f}°"

    def update_motion(self):
        """Advance visual tilt for held keys by one configured timer interval.

        Each direction acts once even if both of its mapped keys are held;
        opposing directions cancel. Clamp roll and pitch to MAX_TILT degrees
        and refresh the display.
        """
        step = (
            self.DEGREES_PER_SECOND
            * self.motion_timer.interval()
            / 1000.0
        )

        if self.pressed_keys.intersection(
            {Qt.Key.Key_A, Qt.Key.Key_4}
        ):
            self.roll -= step

        if self.pressed_keys.intersection(
            {Qt.Key.Key_D, Qt.Key.Key_6}
        ):
            self.roll += step

        if self.pressed_keys.intersection(
            {Qt.Key.Key_W, Qt.Key.Key_8}
        ):
            self.pitch += step

        if self.pressed_keys.intersection(
            {Qt.Key.Key_S, Qt.Key.Key_5}
        ):
            self.pitch -= step

        self.roll = max(
            -self.MAX_TILT, min(self.MAX_TILT, self.roll)
        )
        self.pitch = max(
            -self.MAX_TILT, min(self.MAX_TILT, self.pitch)
        )
        self.refresh_view()

    def release_all_keys(self):
        """Clear held keys and stop motion while preserving the current attitude."""
        had_keys = bool(self.pressed_keys)
        self.pressed_keys.clear()
        self.motion_timer.stop()
        self.refresh_view()

        if had_keys:
            self.add_log("SYSTEM", "All held keys released")

    def reset_orientation(self):
        """Release all keys, stop motion, and zero the visual attitude."""
        self.release_all_keys()
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.refresh_view()
        self.add_log("SYSTEM", "Visual attitude reset to level")

    # --------------------------------------------------------
    # Live UI updates
    # --------------------------------------------------------

    def refresh_view(self):
        """Refresh the gauge, degree readouts, envelope margin, and held-key display."""
        self.gauge.set_attitude(self.roll, self.pitch)

        self.roll_value.setText(f"{self.roll:+.1f}°")
        self.pitch_value.setText(f"{self.pitch:+.1f}°")

        margin = self.MAX_TILT - max(
            abs(self.roll), abs(self.pitch)
        )
        self.margin_value.setText(f"{margin:.1f}°")

        held = []
        for key in sorted(self.pressed_keys, key=int):
            name, _ = self.KEY_ACTIONS[key]
            held.append(name)

        self.primary_held.setText(
            "HELD: " + (" + ".join(held) if held else "NONE")
        )
        self.numpad_status.setText(
            "CO-PILOT: ACTIVE"
            if any(
                key in self.pressed_keys
                for key in (
                    Qt.Key.Key_8, Qt.Key.Key_4,
                    Qt.Key.Key_5, Qt.Key.Key_6,
                )
            )
            else "CO-PILOT: READY"
        )

        for key, button in self.key_buttons.items():
            active = key in self.pressed_keys
            button.setStyleSheet(
                "QPushButton {"
                f"background: {'#59412d' if active else '#171a16'};"
                f"color: {'#ffcf9f' if active else '#e7e5dc'};"
                f"border: 2px solid {COPPER if active else '#383d33'};"
                "border-radius: 4px; font-family: Consolas;"
                "font-size: 10px; font-weight: bold; padding: 5px; }"
            )

        self.footer_orientation.setText(
            f"ROLL: {self.roll:+.1f}°  PITCH: {self.pitch:+.1f}°"
        )

    def update_clock(self):
        """Display monotonic session uptime as minutes and seconds."""
        elapsed = int(time.monotonic() - self.started_at)
        minutes, seconds = divmod(elapsed, 60)
        self.uptime_label.setText(
            f"UPTIME: {minutes:02d}:{seconds:02d}"
        )

    def add_log(self, event_name, message):
        """Append to the 100-line log and display the key-event count."""
        stamp = time.strftime("%H:%M:%S")
        self.event_log_lines.append(
            f"[{stamp}] {event_name:<12} {message}"
        )
        self.event_log.setText("\n".join(self.event_log_lines))
        self.log_count_label.setText(
            f"{self.keystrokes:,} KEY EVENTS"
        )

    def clear_log(self):
        """Clear displayed log entries while preserving the key-event count."""
        self.event_log_lines.clear()
        self.event_log.setText("Event log cleared.")
        self.log_count_label.setText(
            f"{self.keystrokes:,} KEY EVENTS"
        )
