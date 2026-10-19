
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QComboBox,
    QProgressBar,
    QSlider,
    QScrollArea,
    QSizePolicy,
)


class ControlPanel(QWidget):
    BG = "#111310"
    PANEL = "#222420"
    INNER = "#171915"
    BORDER = "#343630"
    TEXT = "#DEDCD3"
    MUTED = "#A39485"
    ORANGE = "#F19548"
    AMBER = "#F0C15B"
    GREEN = "#A1CBB7"
    RED = "#D85A54"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_armed = False
        self.failsafe_active = False
        self.current_mode = "STABILIZE"
        self.last_packet = None

        self.init_ui()

    def init_ui(self):
        self.setObjectName("ControlPanelRoot")
        self.setStyleSheet(f"""
            QWidget#ControlPanelRoot {{
                background: {self.BG};
                color: {self.TEXT};
                font-family: 'Consolas', 'Segoe UI';
                font-size: 11px;
            }}
            QFrame#Card {{
                background: {self.PANEL};
                border: 1px solid {self.BORDER};
                border-radius: 3px;
            }}
            QFrame#InnerPanel {{
                background: {self.INNER};
                border: 1px solid #30322C;
                border-radius: 2px;
            }}
            QLabel#SectionTitle {{
                color: {self.MUTED};
                font-size: 10px;
                font-weight: bold;
            }}
            QLabel#SmallMuted {{
                color: {self.MUTED};
                font-size: 10px;
            }}
            QPushButton {{
                background: #30332D;
                color: {self.TEXT};
                border: 1px solid #45473F;
                border-radius: 2px;
                padding: 8px 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #41443B;
                border-color: {self.ORANGE};
            }}
            QPushButton#PrimaryButton {{
                background: {self.ORANGE};
                color: #21180F;
                border: none;
            }}
            QPushButton#DangerButton {{
                background: #A90E18;
                color: white;
                border: 1px solid #DC343C;
            }}
            QComboBox {{
                background: {self.INNER};
                color: {self.TEXT};
                border: 1px solid #45473F;
                padding: 6px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView {{
                background: {self.PANEL};
                color: {self.TEXT};
                selection-background-color: {self.ORANGE};
                selection-color: #171915;
            }}
            QProgressBar {{
                background: #0D0F0C;
                border: 1px solid #3B3D35;
                text-align: center;
                color: {self.TEXT};
                min-height: 16px;
                max-height: 20px;
            }}
            QProgressBar::chunk {{
                background: {self.ORANGE};
            }}
            QSlider::groove:horizontal {{
                background: #111310;
                height: 5px;
                border: 1px solid #3A3C34;
            }}
            QSlider::handle:horizontal {{
                background: {self.ORANGE};
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }}
            QScrollArea {{
                border: none;
                background: {self.BG};
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.content = QWidget()
        self.content.setMinimumWidth(0)

        root = QVBoxLayout(self.content)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(9)

        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll)

        # HEADER
        header = QHBoxLayout()
        header.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)

        title = QLabel("FLIGHT CONTROL / AVIONICS")
        title.setFont(QFont("Consolas", 15, QFont.Bold))
        title.setStyleSheet(f"color: {self.ORANGE};")

        subtitle = QLabel(
            "BEE-BRAIN GROUND CONTROL / NODE 0x7A"
        )
        subtitle.setObjectName("SmallMuted")
        subtitle.setWordWrap(True)

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        self.link_badge = self.value_label(
            "● LINK: WAITING", self.AMBER
        )
        header.addWidget(self.link_badge)

        self.stream_badge = QLabel("FAKE TELEMETRY")
        self.stream_badge.setAlignment(Qt.AlignCenter)
        self.stream_badge.setStyleSheet(
            f"background: {self.ORANGE}; color: #21180F; padding: 8px;"
        )
        header.addWidget(self.stream_badge)

        root.addLayout(header)

        # FLIGHT STATE STRIP
        state_card = self.card()
        state_layout = QVBoxLayout(state_card)
        state_layout.setContentsMargins(9, 8, 9, 8)
        state_layout.setSpacing(7)
        state_layout.addWidget(
            self.section_title("FLIGHT STATE / SIMULATION")
        )

        self.state_label = QLabel("DISARMED")
        self.state_label.setStyleSheet(
            f"color: {self.RED}; font-weight: bold;"
        )
        state_layout.addWidget(self.state_label)

        root.addWidget(state_card)

        # RESPONSIVE COLUMNS
        self.columns_host = QWidget()
        self.columns_host.setMinimumWidth(0)

        self.columns_layout = QHBoxLayout(self.columns_host)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(9)

        self.left_column = self.build_left_column()
        self.center_column = self.build_center_column()
        self.right_column = self.build_right_column()

        self.columns_layout.addWidget(self.left_column, 24)
        self.columns_layout.addWidget(self.center_column, 46)
        self.columns_layout.addWidget(self.right_column, 25)

        root.addWidget(self.columns_host)

        # COMMAND STATUS
        command_card = self.card()
        command_layout = QVBoxLayout(command_card)
        command_layout.setContentsMargins(10, 8, 10, 8)
        command_layout.addWidget(
            self.section_title("COMMAND STATUS")
        )

        self.command_status = QLabel("Waiting for telemetry...")
        self.command_status.setWordWrap(True)
        command_layout.addWidget(self.command_status)

        root.addWidget(command_card)

        self.update_responsive_layout()

    # ---------------------------------------------------------
    # LEFT COLUMN
    # ---------------------------------------------------------

    def build_left_column(self):
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        safety = self.card()
        safety_l = QVBoxLayout(safety)
        safety_l.setContentsMargins(10, 10, 10, 10)
        safety_l.setSpacing(8)

        safety_l.addWidget(
            self.section_title("ARMING & SAFETY BAY")
        )

        self.arm_status = self.value_label("DISARMED", self.RED)
        safety_l.addWidget(
            self.pair("ARM STATUS", self.arm_status)
        )

        self.failsafe_status = self.value_label(
            "WAITING", self.AMBER
        )
        safety_l.addWidget(
            self.pair("LINK / FAILSAFE", self.failsafe_status)
        )

        self.tof_status = self.value_label(
            "WAITING", self.AMBER
        )
        safety_l.addWidget(
            self.pair("TOF SENSOR", self.tof_status)
        )

        self.flow_status = self.value_label(
            "WAITING", self.AMBER
        )
        safety_l.addWidget(
            self.pair("OPTICAL FLOW", self.flow_status)
        )

        self.arm_button = QPushButton("ARM SIMULATION")
        self.arm_button.setObjectName("PrimaryButton")
        self.arm_button.setMinimumHeight(38)
        self.arm_button.clicked.connect(self.toggle_arm)
        safety_l.addWidget(self.arm_button)

        self.kill_button = QPushButton(
            "EMERGENCY CUTOFF — UI ONLY"
        )
        self.kill_button.setObjectName("DangerButton")
        self.kill_button.setMinimumHeight(38)
        self.kill_button.setEnabled(False)
        self.kill_button.setToolTip(
            "Not connected to physical hardware."
        )
        safety_l.addWidget(self.kill_button)

        note = self.muted_label(
            "Simulation controls only. No physical arming or motor cutoff."
        )
        note.setWordWrap(True)
        safety_l.addWidget(note)

        layout.addWidget(safety)

        # FLIGHT TELEMETRY
        telemetry = self.card()
        telemetry_l = QVBoxLayout(telemetry)
        telemetry_l.setContentsMargins(10, 10, 10, 10)
        telemetry_l.setSpacing(8)
        telemetry_l.addWidget(
            self.section_title("FLIGHT TELEMETRY")
        )

        self.altitude_value = self.value_label("-- cm")
        telemetry_l.addWidget(
            self.pair("ALTITUDE", self.altitude_value)
        )

        self.drift_x_value = self.value_label("--")
        telemetry_l.addWidget(
            self.pair("DRIFT X", self.drift_x_value)
        )

        self.drift_y_value = self.value_label("--")
        telemetry_l.addWidget(
            self.pair("DRIFT Y", self.drift_y_value)
        )

        self.battery_value = self.value_label("-- V")
        telemetry_l.addWidget(
            self.pair("BATTERY", self.battery_value)
        )

        layout.addWidget(telemetry)

        routines = self.card()
        routines_l = QVBoxLayout(routines)
        routines_l.setContentsMargins(10, 10, 10, 10)
        routines_l.setSpacing(7)
        routines_l.addWidget(
            self.section_title("FLIGHT SUBROUTINES")
        )

        for name, description in [
            ("TAKEOFF", "UI placeholder"),
            ("HOVER HOLD", "UI placeholder"),
            ("LAND SLOW", "UI placeholder"),
        ]:
            tile = self.card(inner=True)
            tile_l = QVBoxLayout(tile)
            tile_l.setContentsMargins(8, 7, 8, 7)

            heading = QLabel(name)
            heading.setStyleSheet(
                f"color: {self.ORANGE}; font-weight: bold;"
            )

            detail = self.muted_label(description)
            tile_l.addWidget(heading)
            tile_l.addWidget(detail)
            routines_l.addWidget(tile)

        layout.addWidget(routines)
        layout.addStretch()
        return column

    # ---------------------------------------------------------
    # CENTER COLUMN
    # ---------------------------------------------------------

    def build_center_column(self):
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        motor_card = self.card()
        motor_l = QVBoxLayout(motor_card)
        motor_l.setContentsMargins(10, 10, 10, 10)
        motor_l.setSpacing(8)

        motor_l.addWidget(
            self.section_title("MOTOR OUTPUT / X-CONFIGURATION")
        )

        motor_note = self.muted_label(
            "PWM is taken from fake telemetry. RPM feedback is unavailable."
        )
        motor_note.setWordWrap(True)
        motor_l.addWidget(motor_note)

        motor_grid = QGridLayout()
        motor_grid.setSpacing(7)

        self.motor_values = []
        self.motor_bars = []

        motor_names = [
            ("M1", "FRONT LEFT"),
            ("M2", "FRONT RIGHT"),
            ("M3", "REAR RIGHT"),
            ("M4", "REAR LEFT"),
        ]

        for index, (name, position) in enumerate(motor_names):
            cell = self.card(inner=True)
            cell_l = QVBoxLayout(cell)
            cell_l.setContentsMargins(8, 8, 8, 8)
            cell_l.setSpacing(5)

            top = QHBoxLayout()
            motor_name = QLabel(f"{name} / {position}")
            motor_name.setWordWrap(True)
            motor_name.setStyleSheet("font-weight: bold;")

            value = QLabel("--")
            value.setStyleSheet(
                f"color: {self.GREEN}; font-weight: bold;"
            )

            top.addWidget(motor_name, 1)
            top.addWidget(value)
            cell_l.addLayout(top)

            pwm_label = QLabel("PWM: unavailable")
            cell_l.addWidget(pwm_label)

            bar = QProgressBar()
            bar.setRange(0, 255)
            bar.setValue(0)
            bar.setFormat("%v / 255")
            cell_l.addWidget(bar)

            motor_l.addWidget(cell) if False else None
            motor_grid.addWidget(cell, index // 2, index % 2)

            self.motor_values.append((value, pwm_label))
            self.motor_bars.append(bar)

        motor_l.addLayout(motor_grid)
        layout.addWidget(motor_card)

        throttle = self.card()
        throttle_l = QVBoxLayout(throttle)
        throttle_l.setContentsMargins(10, 10, 10, 10)
        throttle_l.setSpacing(8)
        throttle_l.addWidget(
            self.section_title("AVERAGE MOTOR COMMAND")
        )

        self.throttle_value = self.value_label("--%", self.ORANGE)
        throttle_l.addWidget(
            self.throttle_value, alignment=Qt.AlignRight
        )

        self.throttle_bar = QProgressBar()
        self.throttle_bar.setRange(0, 255)
        self.throttle_bar.setValue(0)
        self.throttle_bar.setFormat("%p%")
        throttle_l.addWidget(self.throttle_bar)

        throttle_note = self.muted_label(
            "Average of four PWM command values; not measured thrust."
        )
        throttle_note.setWordWrap(True)
        throttle_l.addWidget(throttle_note)
        layout.addWidget(throttle)

        attitude = self.card()
        attitude_l = QVBoxLayout(attitude)
        attitude_l.setContentsMargins(10, 10, 10, 10)
        attitude_l.setSpacing(8)
        attitude_l.addWidget(
            self.section_title("ATTITUDE / NOT PROVIDED")
        )

        attitude_grid = QGridLayout()
        self.roll_value = self.value_label("--°")
        self.pitch_value = self.value_label("--°")
        self.yaw_value = self.value_label("--°")

        for col, name, value in [
            (0, "ROLL", self.roll_value),
            (1, "PITCH", self.pitch_value),
            (2, "YAW", self.yaw_value),
        ]:
            label = self.muted_label(name)
            label.setAlignment(Qt.AlignCenter)
            value.setAlignment(Qt.AlignCenter)
            attitude_grid.addWidget(label, 0, col)
            attitude_grid.addWidget(value, 1, col)

        attitude_l.addLayout(attitude_grid)
        attitude_l.addWidget(self.muted_label(
            "Your current fake generator does not provide attitude angles."
        ))
        layout.addWidget(attitude)

        layout.addStretch()
        return column

    # ---------------------------------------------------------
    # RIGHT COLUMN
    # ---------------------------------------------------------

    def build_right_column(self):
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        modes = self.card()
        modes_l = QVBoxLayout(modes)
        modes_l.setContentsMargins(10, 10, 10, 10)
        modes_l.setSpacing(8)
        modes_l.addWidget(
            self.section_title("FLIGHT MODE")
        )

        self.flight_mode = QComboBox()
        self.flight_mode.addItems([
            "STABILIZE",
            "ALTITUDE HOLD",
            "POSITION HOLD",
            "AUTONOMOUS",
        ])
        self.flight_mode.currentTextChanged.connect(
            self.set_flight_mode
        )
        modes_l.addWidget(self.flight_mode)

        modes_l.addWidget(self.muted_label(
            "Mode selection is local UI state; it does not command the drone."
        ))
        layout.addWidget(modes)

        trims = self.card()
        trims_l = QVBoxLayout(trims)
        trims_l.setContentsMargins(10, 10, 10, 10)
        trims_l.setSpacing(9)
        trims_l.addWidget(
            self.section_title("FLIGHT SETPOINT TRIMS")
        )

        self.pitch_trim_value = QLabel("0.0°")
        self.roll_trim_value = QLabel("0.0°")

        self.pitch_slider = self.make_trim_slider(
            trims_l, "PITCH TRIM", self.pitch_trim_value
        )
        self.roll_slider = self.make_trim_slider(
            trims_l, "ROLL TRIM", self.roll_trim_value
        )

        self.pitch_slider.valueChanged.connect(
            lambda value: self.pitch_trim_value.setText(
                f"{value / 10:.1f}°"
            )
        )
        self.roll_slider.valueChanged.connect(
            lambda value: self.roll_trim_value.setText(
                f"{value / 10:.1f}°"
            )
        )

        buttons = QGridLayout()
        buttons.setSpacing(6)

        reset_btn = QPushButton("RESET")
        reset_btn.clicked.connect(self.reset_trims)

        save_btn = QPushButton("SAVE MOCK")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.show_mock_saved)

        buttons.addWidget(reset_btn, 0, 0)
        buttons.addWidget(save_btn, 0, 1)
        trims_l.addLayout(buttons)

        layout.addWidget(trims)

        limits = self.card()
        limits_l = QVBoxLayout(limits)
        limits_l.setContentsMargins(10, 10, 10, 10)
        limits_l.setSpacing(7)
        limits_l.addWidget(
            self.section_title("SYSTEM LIMITS / PREVIEW")
        )

        limits_l.addWidget(QLabel("Thrust ceiling"))
        limits_l.addWidget(self.muted_label(
            "No enforced hardware limit available."
        ))

        limits_l.addWidget(QLabel("Yaw rate"))
        limits_l.addWidget(self.muted_label(
            "Unavailable — no gyro telemetry."
        ))

        limits_l.addWidget(QLabel("Control loop rate"))
        limits_l.addWidget(self.muted_label(
            "Unavailable — not included in current packets."
        ))

        layout.addWidget(limits)
        layout.addStretch()
        return column

    # ---------------------------------------------------------
    # RESPONSIVE LAYOUT
    # ---------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_layout()

    def update_responsive_layout(self):
        if not hasattr(self, "columns_layout"):
            return

        width = self.scroll.viewport().width()

        # Reflow to one column when the application is narrow.
        if width >= 1180:
            mode = "three"
        elif width >= 780:
            mode = "two"
        else:
            mode = "one"

        if getattr(self, "_layout_mode", None) == mode:
            return

        self._layout_mode = mode

        while self.columns_layout.count():
            self.columns_layout.takeAt(0)

        if mode == "three":
            self.columns_layout.setDirection(
                QHBoxLayout.LeftToRight
            )
            self.columns_layout.addWidget(self.left_column, 24)
            self.columns_layout.addWidget(self.center_column, 46)
            self.columns_layout.addWidget(self.right_column, 25)

        elif mode == "two":
            self.columns_layout.setDirection(
                QHBoxLayout.TopToBottom
            )

            # Two-column top row.
            top = QWidget()
            top_layout = QHBoxLayout(top)
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(9)
            top_layout.addWidget(self.left_column, 1)
            top_layout.addWidget(self.center_column, 1)

            self.columns_layout.addWidget(top)
            self.columns_layout.addWidget(self.right_column)

        else:
            self.columns_layout.setDirection(
                QHBoxLayout.TopToBottom
            )
            self.columns_layout.addWidget(self.left_column)
            self.columns_layout.addWidget(self.center_column)
            self.columns_layout.addWidget(self.right_column)

        self.content.updateGeometry()

    # ---------------------------------------------------------
    # UI HELPERS
    # ---------------------------------------------------------

    def card(self, inner=False):
        frame = QFrame()
        frame.setObjectName(
            "InnerPanel" if inner else "Card"
        )
        frame.setMinimumWidth(0)
        frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Maximum,
        )
        return frame

    def section_title(self, text):
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        label.setWordWrap(True)
        return label

    def muted_label(self, text):
        label = QLabel(text)
        label.setObjectName("SmallMuted")
        label.setWordWrap(True)
        return label

    def value_label(self, text, color=None):
        label = QLabel(text)
        label.setWordWrap(True)
        if color:
            label.setStyleSheet(
                f"color: {color}; font-weight: bold;"
            )
        return label

    def pair(self, title, value):
        wrapper = QWidget()
        wrapper.setMinimumWidth(0)

        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        name = self.muted_label(title)
        row.addWidget(name, 1)
        row.addWidget(value, 1, Qt.AlignRight)
        return wrapper

    def make_trim_slider(self, parent_layout, title, value_label):
        parent_layout.addWidget(self.section_title(title))

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)

        row.addWidget(self.muted_label("-5°"))

        slider = QSlider(Qt.Horizontal)
        slider.setRange(-50, 50)
        slider.setValue(0)
        slider.setMinimumWidth(35)
        slider.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        row.addWidget(slider, 1)

        row.addWidget(self.muted_label("+5°"))

        wrapper = QWidget()
        wrapper.setMinimumWidth(0)
        wrapper.setLayout(row)
        parent_layout.addWidget(wrapper)

        value_label.setAlignment(Qt.AlignRight)
        parent_layout.addWidget(value_label)
        return slider

    # ---------------------------------------------------------
    # TELEMETRY INTEGRATION
    # ---------------------------------------------------------

    def update_telemetry(self, packet):
        """Update this page from a validated TelemetryPacket."""
        self.last_packet = packet

        # Altitude and drift: supplied by the current fake generator.
        self.altitude_value.setText(
            f"{packet.altitude_cm:.1f} cm"
        )
        self.drift_x_value.setText(
            f"{packet.drift_x:+.2f}"
        )
        self.drift_y_value.setText(
            f"{packet.drift_y:+.2f}"
        )
        self.battery_value.setText(
            f"{packet.battery_v:.3f} V"
        )

        # Link status.
        if packet.link_ok:
            self.link_badge.setText("● LINK: CONNECTED")
            self.link_badge.setStyleSheet(
                f"color: {self.GREEN}; font-weight: bold;"
            )
            self.failsafe_status.setText("READY")
            self.failsafe_status.setStyleSheet(
                f"color: {self.GREEN}; font-weight: bold;"
            )
        else:
            self.link_badge.setText("● LINK: LOST")
            self.link_badge.setStyleSheet(
                f"color: {self.RED}; font-weight: bold;"
            )
            self.failsafe_status.setText("LINK LOST")
            self.failsafe_status.setStyleSheet(
                f"color: {self.RED}; font-weight: bold;"
            )

        # Sensor health.
        self.tof_status.setText(
            "OK" if packet.sensor_status.tof else "ERROR"
        )
        self.tof_status.setStyleSheet(
            "color: " + (
                self.GREEN if packet.sensor_status.tof else self.RED
            ) + "; font-weight: bold;"
        )

        self.flow_status.setText(
            "TRACKING" if packet.sensor_status.optical_flow else "ERROR"
        )
        self.flow_status.setStyleSheet(
            "color: " + (
                self.GREEN
                if packet.sensor_status.optical_flow
                else self.RED
            ) + "; font-weight: bold;"
        )

        # Legacy PWM is 0..255 in the supplied generator.
        pwm_values = list(packet.motor_pwm[:4])
        while len(pwm_values) < 4:
            pwm_values.append(0)

        for index, pwm in enumerate(pwm_values):
            pwm = max(0, min(255, int(pwm)))
            value_label, pwm_label = self.motor_values[index]

            value_label.setText(
                f"{(pwm / 255) * 100:.0f}%"
            )
            pwm_label.setText(f"PWM: {pwm} / 255")
            self.motor_bars[index].setValue(pwm)

        average_pwm = sum(pwm_values) / 4
        self.throttle_value.setText(
            f"{average_pwm / 255 * 100:.0f}%"
        )
        self.throttle_bar.setValue(round(average_pwm))

        # Battery warning color.
        if packet.battery_v > 3.7:
            battery_color = self.GREEN
        elif packet.battery_v > 3.4:
            battery_color = self.AMBER
        else:
            battery_color = self.RED

        self.battery_value.setStyleSheet(
            f"color: {battery_color}; font-weight: bold;"
        )

        self.command_status.setText(
            f"Mode: {self.current_mode} | "
            f"Altitude: {packet.altitude_cm:.1f} cm | "
            f"Link: {'CONNECTED' if packet.link_ok else 'LOST'}"
        )

    # ---------------------------------------------------------
    # SIMULATED CONTROLS
    # ---------------------------------------------------------

    def toggle_arm(self):
        if self.is_armed:
            self.disarm()
        else:
            self.arm()

    def arm(self):
        self.is_armed = True
        self.arm_status.setText("ARMED (SIM)")
        self.arm_status.setStyleSheet(
            f"color: {self.GREEN}; font-weight: bold;"
        )
        self.state_label.setText("ARMED — SIMULATION ONLY")
        self.state_label.setStyleSheet(
            f"color: {self.GREEN}; font-weight: bold;"
        )
        self.arm_button.setText("DISARM SIMULATION")
        self.arm_button.setObjectName("DangerButton")
        self.arm_button.setStyleSheet(
            f"background: {self.RED}; color: white; font-weight: bold;"
        )
        self.command_status.setText(
            f"Simulation armed | Mode: {self.current_mode}"
        )

    def disarm(self):
        self.is_armed = False
        self.arm_status.setText("DISARMED")
        self.arm_status.setStyleSheet(
            f"color: {self.RED}; font-weight: bold;"
        )
        self.state_label.setText("DISARMED")
        self.state_label.setStyleSheet(
            f"color: {self.RED}; font-weight: bold;"
        )
        self.arm_button.setText("ARM SIMULATION")
        self.arm_button.setObjectName("PrimaryButton")
        self.arm_button.setStyleSheet(
            f"background: {self.ORANGE}; color: #21180F;"
        )
        self.command_status.setText(
            f"Simulation disarmed | Mode: {self.current_mode}"
        )

    def set_flight_mode(self, mode):
        self.current_mode = mode
        self.command_status.setText(
            f"Mode selected: {mode} — UI only"
        )

    def set_attitude(self, roll, pitch, yaw):
        # Retain the existing method signature for compatibility.
        self.roll_value.setText(f"{roll:.2f}°")
        self.pitch_value.setText(f"{pitch:.2f}°")
        self.yaw_value.setText(f"{yaw:.2f}°")

    def set_throttle(self, value):
        # Compatibility method for existing callers.
        value = max(0, min(255, int(value)))
        self.throttle_bar.setValue(value)
        self.throttle_value.setText(
            f"{value / 255 * 100:.0f}%"
        )

    def set_failsafe(self, active):
        self.failsafe_active = active
        if active:
            self.failsafe_status.setText("ACTIVE")
            self.failsafe_status.setStyleSheet(
                f"color: {self.RED}; font-weight: bold;"
            )
        else:
            self.failsafe_status.setText("READY")
            self.failsafe_status.setStyleSheet(
                f"color: {self.GREEN}; font-weight: bold;"
            )

    def reset_trims(self):
        self.pitch_slider.setValue(0)
        self.roll_slider.setValue(0)

    def show_mock_saved(self):
        self.command_status.setText(
            "Trim values saved in the UI session only."
        )
