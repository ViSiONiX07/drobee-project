
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
)

from dashboard.ui.drone_view_panel import DroneCanvas


class KeyboardControlPanel(QWidget):
    """Separate keyboard test panel. Visual controls only."""

    MAX_TILT = 45.0
    DEGREES_PER_SECOND = 55.0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.pressed_keys = set()

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.update_motion)

        self.build_ui()
        self.refresh_view()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        title = QLabel("KEYBOARD CONTROL TEST")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        root.addWidget(title)

        subtitle = QLabel(
            "Hold WASD or 8456 to tilt the visual drone. "
            "Release a key to stop changing its angle."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #91a0ab;")
        root.addWidget(subtitle)

        main_row = QHBoxLayout()
        main_row.setSpacing(14)

        # Reuse the existing renderer.
        # The original fake-data drone panel remains separate.
        self.canvas = DroneCanvas()
        self.canvas.setStyleSheet(
            "border: 1px solid #2b3741; border-radius: 8px;"
        )
        self.canvas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        main_row.addWidget(self.canvas, 3)

        side = QFrame()
        side.setMinimumWidth(245)
        side.setStyleSheet(
            "QFrame { background: #141a20; "
            "border: 1px solid #2b3741; border-radius: 8px; }"
            "QLabel { border: none; }"
        )

        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(10)

        heading = QLabel("KEY BINDINGS")
        heading.setStyleSheet(
            "font-weight: bold; color: #00d6a0;"
        )
        side_layout.addWidget(heading)

        bindings = [
            ("W / 8", "Pitch forward"),
            ("S / 5", "Pitch backward"),
            ("A / 4", "Roll left"),
            ("D / 6", "Roll right"),
            ("SPACE", "Reset orientation"),
            ("ESC", "Release all keys"),
        ]

        for key_text, action_text in bindings:
            line = QHBoxLayout()

            key_label = QLabel(key_text)
            key_label.setMinimumWidth(82)
            key_label.setStyleSheet(
                "background: #26343e; color: #e4ebef; "
                "padding: 5px; border-radius: 4px; "
                "font-weight: bold;"
            )

            action_label = QLabel(action_text)
            action_label.setStyleSheet("color: #b8c6cf;")

            line.addWidget(key_label)
            line.addWidget(action_label, 1)
            side_layout.addLayout(line)

        side_layout.addSpacing(8)

        self.focus_status = QLabel(
            "STATUS: ACTIVATE KEYBOARD CONTROLS"
        )
        self.focus_status.setWordWrap(True)
        self.focus_status.setStyleSheet(
            "color: #e4c16a; font-size: 11px;"
        )
        side_layout.addWidget(self.focus_status)

        self.keys_status = QLabel("HELD: NONE")
        self.keys_status.setWordWrap(True)
        self.keys_status.setStyleSheet(
            "color: #00d6a0; font-size: 11px;"
        )
        side_layout.addWidget(self.keys_status)

        activate_button = QPushButton("ACTIVATE KEYBOARD")
        activate_button.clicked.connect(self.activate_controls)

        reset_button = QPushButton("RESET TILT")
        reset_button.clicked.connect(self.reset_orientation)

        for button in (activate_button, reset_button):
            button.setMinimumHeight(36)
            button.setStyleSheet(
                "QPushButton { background: #24323c; "
                "border: 1px solid #3a4b57; border-radius: 5px; "
                "padding: 7px; color: #e4ebef; }"
                "QPushButton:hover { background: #304450; }"
            )
            side_layout.addWidget(button)

        warning = QLabel(
            "VISUAL TEST ONLY — no physical motor commands"
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color: #d8b56a; font-size: 10px;"
        )
        side_layout.addWidget(warning)
        side_layout.addStretch()

        main_row.addWidget(side, 2)
        root.addLayout(main_row, 1)

        # Orientation readouts
        metrics = QGridLayout()
        metrics.setSpacing(10)

        self.roll_value = self.make_metric(
            metrics, 0, "ROLL", "0.0°"
        )
        self.pitch_value = self.make_metric(
            metrics, 1, "PITCH", "0.0°"
        )
        self.yaw_value = self.make_metric(
            metrics, 2, "YAW", "0.0°"
        )

        root.addLayout(metrics)

    def make_metric(self, layout, column, title, initial):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #141a20; "
            "border: 1px solid #2b3741; border-radius: 7px; }"
        )

        inner = QVBoxLayout(card)
        inner.setContentsMargins(12, 8, 12, 8)

        name = QLabel(title)
        name.setStyleSheet(
            "color: #8b9aa6; font-size: 10px; border: none;"
        )

        value = QLabel(initial)
        value.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        value.setStyleSheet(
            "color: #00d6a0; border: none;"
        )

        inner.addWidget(name)
        inner.addWidget(value)
        layout.addWidget(card, 0, column)

        return value

    def activate_controls(self):
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.focus_status.setText("STATUS: KEYBOARD ACTIVE")
        self.focus_status.setStyleSheet(
            "color: #00d6a0; font-size: 11px;"
        )

    def keyPressEvent(self, event):
        key = event.key()

        movement_keys = {
            Qt.Key.Key_W,
            Qt.Key.Key_A,
            Qt.Key.Key_S,
            Qt.Key.Key_D,
            Qt.Key.Key_8,
            Qt.Key.Key_4,
            Qt.Key.Key_5,
            Qt.Key.Key_6,
        }

        if key in movement_keys:
            self.pressed_keys.add(key)

            if not self.timer.isActive():
                self.timer.start()

            self.update_keys_status()
            event.accept()
            return

        if key == Qt.Key.Key_Space:
            self.reset_orientation()
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.release_all_keys()
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        key = event.key()

        if key in self.pressed_keys:
            self.pressed_keys.discard(key)

            if not self.pressed_keys:
                self.timer.stop()

            self.update_keys_status()
            event.accept()
            return

        super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        # Prevent stuck movement when the page loses keyboard focus.
        self.release_all_keys()
        super().focusOutEvent(event)

    def update_motion(self):
        step = (
            self.DEGREES_PER_SECOND
            * self.timer.interval()
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
            self.pitch -= step

        if self.pressed_keys.intersection(
            {Qt.Key.Key_S, Qt.Key.Key_5}
        ):
            self.pitch += step

        self.roll = max(
            -self.MAX_TILT,
            min(self.MAX_TILT, self.roll),
        )
        self.pitch = max(
            -self.MAX_TILT,
            min(self.MAX_TILT, self.pitch),
        )

        self.refresh_view()

    def refresh_view(self):
        # FIX: DroneCanvas exposes set_orientation(), not set_attitude().
        self.canvas.set_orientation(
            self.roll,
            self.pitch,
            self.yaw,
        )

        self.roll_value.setText(f"{self.roll:.1f}°")
        self.pitch_value.setText(f"{self.pitch:.1f}°")
        self.yaw_value.setText(f"{self.yaw:.1f}°")

    def update_keys_status(self):
        names = {
            Qt.Key.Key_W: "W",
            Qt.Key.Key_A: "A",
            Qt.Key.Key_S: "S",
            Qt.Key.Key_D: "D",
            Qt.Key.Key_8: "8",
            Qt.Key.Key_4: "4",
            Qt.Key.Key_5: "5",
            Qt.Key.Key_6: "6",
        }

        active = [
            names[key]
            for key in sorted(self.pressed_keys, key=int)
        ]

        self.keys_status.setText(
            "HELD: " + (" + ".join(active) if active else "NONE")
        )

    def release_all_keys(self):
        self.pressed_keys.clear()
        self.timer.stop()
        self.update_keys_status()

    def reset_orientation(self):
        self.release_all_keys()

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        self.refresh_view()
