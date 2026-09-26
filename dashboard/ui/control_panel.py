from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QComboBox,
    QProgressBar,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class HoverComboBox(QComboBox):
    """
    Combo box that opens its popup automatically when the mouse
    hovers over it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(120)
        self._hover_timer.timeout.connect(self._show_popup)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hover_timer.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover_timer.stop()

    def _show_popup(self):
        if self.isEnabled():
            self.showPopup()


class ControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_armed = False
        self.failsafe_active = False
        self.current_mode = "STABILIZE"

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(16)

        # --------------------------------------------------
        # TITLE
        # --------------------------------------------------

        title = QLabel("FLIGHT CONTROL")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)

        subtitle = QLabel("Bee-Brain flight control interface")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888888;")

        layout.addWidget(subtitle)

        # --------------------------------------------------
        # SYSTEM SAFETY
        # --------------------------------------------------

        safety_frame = self.create_section("SYSTEM SAFETY")

        safety_layout = QGridLayout()
        safety_layout.setContentsMargins(0, 0, 0, 0)

        arm_title = QLabel("ARM STATUS")
        arm_title.setStyleSheet("color: #dddddd;")

        self.arm_status = self.create_value("DISARMED")
        self.arm_status.setStyleSheet("color: #ff4444;")

        failsafe_title = QLabel("FAILSAFE")
        failsafe_title.setStyleSheet("color: #dddddd;")

        self.failsafe_status = self.create_value("READY")
        self.failsafe_status.setStyleSheet("color: #00ff99;")

        safety_layout.addWidget(arm_title, 0, 0)
        safety_layout.addWidget(
            self.arm_status,
            0,
            1,
            alignment=Qt.AlignRight,
        )

        safety_layout.addWidget(failsafe_title, 1, 0)
        safety_layout.addWidget(
            self.failsafe_status,
            1,
            1,
            alignment=Qt.AlignRight,
        )

        safety_frame.layout().addLayout(safety_layout)

        layout.addWidget(safety_frame)

        # --------------------------------------------------
        # FLIGHT STATE
        # --------------------------------------------------

        flight_frame = self.create_section("FLIGHT STATE")

        flight_layout = QGridLayout()
        flight_layout.setContentsMargins(0, 0, 0, 0)
        flight_layout.setVerticalSpacing(10)

        # ARM BUTTON
        self.arm_button = QPushButton("ARM")

        self.arm_button.setMinimumHeight(45)

        self.arm_button.clicked.connect(self.toggle_arm)

        flight_layout.addWidget(
            self.arm_button,
            0,
            0,
            1,
            2,
        )

        # FLIGHT MODE
        mode_label = QLabel("Flight Mode:")
        mode_label.setStyleSheet("color: #dddddd;")

        self.flight_mode = HoverComboBox()

        self.flight_mode.addItems(
            [
                "STABILIZE",
                "ALTITUDE HOLD",
                "POSITION HOLD",
                "AUTONOMOUS",
            ]
        )

        self.flight_mode.currentTextChanged.connect(
            self.set_flight_mode
        )

        self.flight_mode.setMinimumHeight(32)

        flight_layout.addWidget(
            mode_label,
            1,
            0,
        )

        flight_layout.addWidget(
            self.flight_mode,
            1,
            1,
        )

        flight_frame.layout().addLayout(flight_layout)

        layout.addWidget(flight_frame)

        # --------------------------------------------------
        # ATTITUDE
        # --------------------------------------------------

        attitude_frame = self.create_section("ATTITUDE")

        attitude_layout = QGridLayout()
        attitude_layout.setContentsMargins(0, 0, 0, 0)

        self.roll_value = self.create_value("0.00°")
        self.pitch_value = self.create_value("0.00°")
        self.yaw_value = self.create_value("0.00°")

        attitude_layout.addWidget(
            QLabel("ROLL"),
            0,
            0,
            alignment=Qt.AlignCenter,
        )

        attitude_layout.addWidget(
            QLabel("PITCH"),
            0,
            1,
            alignment=Qt.AlignCenter,
        )

        attitude_layout.addWidget(
            QLabel("YAW"),
            0,
            2,
            alignment=Qt.AlignCenter,
        )

        attitude_layout.addWidget(
            self.roll_value,
            1,
            0,
            alignment=Qt.AlignCenter,
        )

        attitude_layout.addWidget(
            self.pitch_value,
            1,
            1,
            alignment=Qt.AlignCenter,
        )

        attitude_layout.addWidget(
            self.yaw_value,
            1,
            2,
            alignment=Qt.AlignCenter,
        )

        attitude_frame.layout().addLayout(attitude_layout)

        layout.addWidget(attitude_frame)

        # --------------------------------------------------
        # THROTTLE
        # --------------------------------------------------

        throttle_frame = self.create_section("THROTTLE")

        throttle_layout = QVBoxLayout()
        throttle_layout.setContentsMargins(0, 0, 0, 0)

        self.throttle_value = self.create_value("0%")

        throttle_layout.addWidget(
            self.throttle_value,
            alignment=Qt.AlignCenter,
        )

        self.throttle_bar = QProgressBar()

        self.throttle_bar.setMinimum(0)
        self.throttle_bar.setMaximum(100)
        self.throttle_bar.setValue(0)

        self.throttle_bar.setFormat("%p%")

        self.throttle_bar.setMinimumHeight(26)

        throttle_layout.addWidget(
            self.throttle_bar
        )

        throttle_frame.layout().addLayout(
            throttle_layout
        )

        layout.addWidget(throttle_frame)

        # --------------------------------------------------
        # COMMAND STATUS
        # --------------------------------------------------

        command_frame = self.create_section("COMMAND STATUS")

        command_layout = QVBoxLayout()
        command_layout.setContentsMargins(0, 0, 0, 0)

        self.command_status = QLabel(
            "No flight commands active"
        )

        self.command_status.setAlignment(
            Qt.AlignCenter
        )

        self.command_status.setStyleSheet(
            "color: #888888;"
        )

        command_layout.addWidget(
            self.command_status
        )

        command_frame.layout().addLayout(
            command_layout
        )

        layout.addWidget(command_frame)

        layout.addStretch()

    # ======================================================
    # UI HELPERS
    # ======================================================

    def create_section(self, title_text):
        frame = QFrame()

        frame.setFrameStyle(
            QFrame.StyledPanel | QFrame.Raised
        )

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        title = QLabel(title_text)

        title.setFont(
            QFont(
                "Arial",
                10,
                QFont.Bold,
            )
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            "color: #888888;"
        )

        layout.addWidget(title)

        return frame

    def create_value(self, text):
        label = QLabel(text)

        label.setFont(
            QFont(
                "Arial",
                12,
            )
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        return label

    # ======================================================
    # ARM / DISARM
    # ======================================================

    def toggle_arm(self):
        if self.is_armed:
            self.disarm()
        else:
            self.arm()

    def arm(self):
        self.is_armed = True

        self.arm_status.setText("ARMED")
        self.arm_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.arm_button.setText(
            "DISARM"
        )

        self.arm_button.setStyleSheet(
            """
            QPushButton {
                background-color: #8b0000;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #aa0000;
            }
            """
        )

        self.command_status.setText(
            "Flight system armed"
        )

        self.command_status.setStyleSheet(
            "color: #00ff99;"
        )

    def disarm(self):
        self.is_armed = False

        self.arm_status.setText(
            "DISARMED"
        )

        self.arm_status.setStyleSheet(
            "color: #ff4444;"
        )

        self.arm_button.setText(
            "ARM"
        )

        self.arm_button.setStyleSheet("")

        self.command_status.setText(
            "No flight commands active"
        )

        self.command_status.setStyleSheet(
            "color: #888888;"
        )

    # ======================================================
    # FLIGHT MODE
    # ======================================================

    def set_flight_mode(self, mode):
        self.current_mode = mode

        self.command_status.setText(
            f"Flight mode: {mode}"
        )

    # ======================================================
    # ATTITUDE
    # ======================================================

    def set_attitude(
        self,
        roll,
        pitch,
        yaw,
    ):
        self.roll_value.setText(
            f"{roll:.2f}°"
        )

        self.pitch_value.setText(
            f"{pitch:.2f}°"
        )

        self.yaw_value.setText(
            f"{yaw:.2f}°"
        )

    # ======================================================
    # THROTTLE
    # ======================================================

    def set_throttle(self, value):
        value = max(
            0,
            min(100, int(value))
        )

        self.throttle_bar.setValue(
            value
        )

        self.throttle_value.setText(
            f"{value}%"
        )

    # ======================================================
    # FAILSAFE
    # ======================================================

    def set_failsafe(self, active):
        self.failsafe_active = active

        if active:
            self.failsafe_status.setText(
                "ACTIVE"
            )

            self.failsafe_status.setStyleSheet(
                "color: #ff4444;"
            )
        else:
            self.failsafe_status.setText(
                "READY"
            )

            self.failsafe_status.setStyleSheet(
                "color: #00ff99;"
            )