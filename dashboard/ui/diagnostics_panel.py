
import math
import random
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
    QProgressBar,
    QCheckBox,
)


class DiagnosticsPanel(QWidget):
    """Stitch-style Bee-Brain diagnostics with animated demo data."""

    C = {
        "bg": "#10120F",
        "panel": "#1B1E1A",
        "inner": "#0C0F0C",
        "border": "#30352E",
        "text": "#E6E6DD",
        "muted": "#A19788",
        "green": "#A5D5BD",
        "amber": "#F6B65F",
        "orange": "#F39A4A",
        "red": "#E87870",
        "blue": "#89B9D6",
    }

    def __init__(self, parent=None):
        """Build diagnostics and start the clock and simulated-value timers.

        Demo values refresh every 500 ms until update_telemetry is called;
        the clock refreshes every second.
        """
        super().__init__(parent)

        self._has_telemetry = False
        self._demo_tick = 0
        self._demo_packet_count = 148
        self._demo_battery = 3.84
        self._log_entries = []
        self.log_filter = "ALL"

        self._build_ui()
        self._apply_styles()

        self._append_event("INFO", "Diagnostics interface initialized.")
        self._append_event("INFO", "Demo sensor values loaded.")
        self._append_event("WARN", "Hardware readings are not connected.")

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo_values)
        self.demo_timer.start(500)

    # ==================================================
    # UI
    # ==================================================

    def _build_ui(self):
        """Build the scrollable subsystem panels, footers, and legacy aliases."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("diagnosticsContent")

        page = QVBoxLayout(content)
        page.setContentsMargins(12, 10, 12, 8)
        page.setSpacing(9)

        page.addWidget(self._build_top_bar())
        page.addWidget(self._build_readiness_bar())

        columns = QGridLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setHorizontalSpacing(10)
        columns.setVerticalSpacing(10)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.addWidget(self._build_tof_panel())
        left_layout.addWidget(self._build_optical_panel())
        left_layout.addStretch()

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.addWidget(self._build_power_panel())
        right_layout.addWidget(self._build_mcu_panel())
        right_layout.addWidget(self._build_log_panel(), 1)

        left = QWidget()
        left.setLayout(left_layout)

        right = QWidget()
        right.setLayout(right_layout)

        columns.addWidget(left, 0, 0)
        columns.addWidget(right, 0, 1)
        columns.setColumnStretch(0, 6)
        columns.setColumnStretch(1, 4)

        page.addLayout(columns, 1)
        page.addWidget(self._build_daemon_strip())

        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        root.addWidget(self._build_bottom_bar())

        self._build_legacy_aliases()

    def _build_top_bar(self):
        """Return the header with initial simulated link and packet readouts."""
        frame = QFrame()
        frame.setObjectName("topBar")

        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 5, 10, 5)
        row.setSpacing(8)

        brand = QLabel("⌘  BEE-BRAIN GCS")
        brand.setObjectName("brand")

        version = QLabel("Micro-UAV Research Lab v2.4")
        version.setObjectName("muted")

        row.addWidget(brand)
        row.addWidget(version)
        row.addStretch()

        self.link_badge = self._badge("● LINK: SIMULATED", "green")
        self.stream_badge = self._badge("SIMULATED STREAM", "amber")
        self.rate_badge = self._badge("RATE: 10 Hz", "neutral")
        self.rtt_badge = self._badge("RTT: 4.2 ms*", "neutral")
        self.packets_badge = self._badge("PKTS: 148", "neutral")

        for widget in (
            self.link_badge,
            self.stream_badge,
            self.rate_badge,
            self.rtt_badge,
            self.packets_badge,
        ):
            row.addWidget(widget)

        return frame

    def _build_readiness_bar(self):
        """Return demo readiness indicators and the demo self-check button."""
        frame = QFrame()
        frame.setObjectName("readinessPanel")

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(12)

        self.integrity_value = QLabel("■ DEMO MODE")
        self.integrity_value.setObjectName("greenValue")

        self.readiness_value = QLabel("8/8 DEMO INDICATORS")
        self.readiness_value.setObjectName("strongValue")

        self.buses_value = QLabel("I2C: DEMO  SPI: DEMO  UART: DEMO")
        self.buses_value.setObjectName("greenValue")

        self.rtos_value = QLabel("10.0 Hz")
        self.rtos_value.setObjectName("amberValue")

        for heading, value in (
            ("INTEGRITY DISPOSITION", self.integrity_value),
            ("READINESS MATRIX", self.readiness_value),
            ("HARDWARE BUSES", self.buses_value),
            ("DEMO UPDATE RATE", self.rtos_value),
        ):
            cell = QVBoxLayout()
            cell.setSpacing(3)

            label = QLabel(heading)
            label.setObjectName("microLabel")

            cell.addWidget(label)
            cell.addWidget(value)
            row.addLayout(cell)

        row.addStretch()

        self.run_button = QPushButton("⚙ RUN DEMO SELF-CHECK")
        self.run_button.setObjectName("actionButton")
        self.run_button.clicked.connect(self.run_system_check)
        row.addWidget(self.run_button)

        return frame

    # ==================================================
    # TOF PANEL
    # ==================================================

    def _build_tof_panel(self):
        """Return an illustrative ranging matrix and simulated ToF statistics."""
        panel = self._panel()

        panel.layout().addLayout(
            self._panel_header(
                "▦ ToF Subsystem [VL53L0X]",
                "NOMINAL · DEMO",
                "green",
            )
        )

        stats = QGridLayout()
        stats.setSpacing(5)

        for i, (title, value) in enumerate([
            ("I2C ADDRESS", "0x29*"),
            ("AMBIENT NOISE", "4.2 kcps*"),
            ("SIGNAL RETURN", "84.1 kcps*"),
            ("SENSOR FOV", "25°*"),
        ]):
            stats.addWidget(self._stat_cell(title, value), 0, i)

        panel.layout().addLayout(stats)

        body = QHBoxLayout()
        body.setSpacing(9)

        matrix_column = QVBoxLayout()

        heading = QLabel("MULTIZONE RANGING MATRIX (MM)")
        heading.setObjectName("microLabel")
        heading.setAlignment(Qt.AlignCenter)
        matrix_column.addWidget(heading)

        initial_matrix = [
            [419, 414, 380, 360, 356, 369, 409, 424],
            [411, 340, 291, 281, 286, 296, 334, 413],
            [386, 291, 241, 215, 221, 244, 292, 390],
            [360, 274, 210, 199, 201, 215, 269, 366],
            [355, 280, 211, 200, 204, 218, 281, 359],
            [374, 295, 244, 221, 224, 250, 299, 380],
            [404, 329, 285, 274, 281, 289, 339, 408],
            [429, 418, 391, 365, 361, 374, 415, 435],
        ]

        self._demo_matrix = [
            value for line in initial_matrix for value in line
        ]
        self.tof_cells = []
        matrix_grid = QGridLayout()
        matrix_grid.setSpacing(3)

        for index, value in enumerate(self._demo_matrix):
            cell = QLabel(str(value))
            cell.setAlignment(Qt.AlignCenter)
            cell.setMinimumSize(25, 24)
            cell.setObjectName(self._tof_tone(value))

            matrix_grid.addWidget(cell, index // 8, index % 8)
            self.tof_cells.append(cell)

        matrix_column.addLayout(matrix_grid)
        body.addLayout(matrix_column, 6)

        zones = QVBoxLayout()
        zones.setSpacing(7)

        zone_heading = QLabel("DISTANCE RAMP")
        zone_heading.setObjectName("microLabel")
        zones.addWidget(zone_heading)

        zones.addWidget(self._zone("NEAR (<210 mm)", "OBSTACLE", "orange"))
        zones.addWidget(self._zone("NOMINAL (250–350 mm)", "NORMAL", "green"))
        zones.addWidget(self._zone("FAR (>400 mm)", "CLEAR", "neutral"))

        focal = self._panel()
        focal.setObjectName("innerPanel")
        focal.layout().setContentsMargins(8, 8, 8, 8)

        title = QLabel("FOCAL APERTURE STATS")
        title.setObjectName("microLabel")
        focal.layout().addWidget(title)

        self.center_avg_label = QLabel("201.0 mm*")
        self.dev_jitter_label = QLabel("±1.2 mm*")
        self.frame_drift_label = QLabel("0.04%*")

        for name, value_label in (
            ("CENTER AVG", self.center_avg_label),
            ("DEV JITTER", self.dev_jitter_label),
            ("FRAME DRIFT", self.frame_drift_label),
        ):
            row = QHBoxLayout()
            label = QLabel(name)
            label.setObjectName("muted")
            value_label.setObjectName("greenValue")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(value_label)
            focal.layout().addLayout(row)

        zones.addSpacing(5)
        zones.addWidget(focal)
        zones.addStretch()

        body.addLayout(zones, 4)
        panel.layout().addLayout(body)

        note = QLabel(
            "DEMO MATRIX · ILLUSTRATIVE VALUES, NOT SENSOR MEASUREMENTS"
        )
        note.setObjectName("microLabel")
        note.setWordWrap(True)
        panel.layout().addWidget(note)

        return panel

    def _tof_tone(self, distance):
        """Return the heat style for a distance in millimeters.

        Distances below 210 are hot, 210 to below 350 are normal, and 350 or
        above are far.
        """
        if distance < 210:
            return "heatHot"
        if distance < 350:
            return "heatNormal"
        return "heatFar"

    def _zone(self, left, right, tone):
        """Return a distance-legend row styled with the supplied tone name."""
        frame = QFrame()
        frame.setObjectName(f"zone_{tone}")

        row = QHBoxLayout(frame)
        row.setContentsMargins(6, 5, 6, 5)

        a = QLabel(left)
        a.setObjectName("zoneText")
        b = QLabel(right)
        b.setObjectName("zoneText")

        row.addWidget(a, 1)
        row.addWidget(b)
        return frame

    # ==================================================
    # OPTICAL FLOW
    # ==================================================

    def _build_optical_panel(self):
        """Return simulated optical-flow confidence and displacement readouts."""
        panel = self._panel()

        panel.layout().addLayout(
            self._panel_header(
                "◉ PMW3901 Optical Flow Subsystem",
                "TRACKING · DEMO",
                "green",
            )
        )

        stats = QGridLayout()
        stats.setSpacing(5)

        for i, (title, value) in enumerate([
            ("BUS FREQUENCY", "SPI 8.0 MHz*"),
            ("SURFACE QUALITY", "84 / 100*"),
            ("SHUTTER EXPOSURE", "420 μs*"),
            ("VALID VECTORS", "9,410 /s*"),
        ]):
            stats.addWidget(self._stat_cell(title, value), 0, i)

        panel.layout().addLayout(stats)

        details = QHBoxLayout()
        details.setSpacing(10)

        confidence = QVBoxLayout()
        top = QHBoxLayout()

        label = QLabel("SURFACE TRACKING CONFIDENCE")
        label.setObjectName("microLabel")

        self.flow_confidence = QLabel("84%*")
        self.flow_confidence.setObjectName("greenValue")

        top.addWidget(label)
        top.addStretch()
        top.addWidget(self.flow_confidence)
        confidence.addLayout(top)

        self.flow_bar = QProgressBar()
        self.flow_bar.setRange(0, 100)
        self.flow_bar.setValue(84)
        self.flow_bar.setTextVisible(False)
        self.flow_bar.setFixedHeight(10)
        self.flow_bar.setObjectName("confidenceBar")
        confidence.addWidget(self.flow_bar)

        note = QLabel("TEXTURE SUFFICIENCY: DEMO")
        note.setObjectName("microLabel")
        confidence.addWidget(note)

        details.addLayout(confidence, 2)

        delta = QFrame()
        delta.setObjectName("innerPanel")
        delta_layout = QHBoxLayout(delta)

        self.delta_x_value = QLabel("+0.12 px*")
        self.delta_y_value = QLabel("-0.04 px*")

        for title, value in (
            ("DELTA X", self.delta_x_value),
            ("DELTA Y", self.delta_y_value),
        ):
            column = QVBoxLayout()
            heading = QLabel(title)
            heading.setObjectName("microLabel")
            heading.setAlignment(Qt.AlignCenter)

            value.setObjectName("bigValue")
            value.setAlignment(Qt.AlignCenter)

            column.addWidget(heading)
            column.addWidget(value)
            delta_layout.addLayout(column)

        details.addWidget(delta, 1)
        panel.layout().addLayout(details)

        return panel

    # ==================================================
    # POWER / MOTORS
    # ==================================================

    def _build_power_panel(self):
        """Return demo power and motor readouts and create legacy power labels."""
        panel = self._panel()

        panel.layout().addLayout(
            self._panel_header(
                "ϟ Power & Motor Driver Subsystem",
                "DEMO MONITOR",
                "amber",
            )
        )

        battery = QFrame()
        battery.setObjectName("innerPanel")

        row = QHBoxLayout(battery)
        row.setContentsMargins(9, 8, 9, 8)
        row.setSpacing(9)

        voltage = QVBoxLayout()

        heading = QLabel("CELL VOLTAGE")
        heading.setObjectName("microLabel")

        self.battery_number = QLabel("3.84")
        self.battery_number.setObjectName("batteryNumber")

        unit = QLabel("V · SIMULATED")
        unit.setObjectName("muted")

        voltage.addWidget(heading)
        voltage.addWidget(self.battery_number)
        voltage.addWidget(unit)
        row.addLayout(voltage, 2)

        self.ocp_value = self._small_value("OCP STATUS", "DEMO OK")
        self.resistance_value = self._small_value("INTERNAL RES.", "112 mΩ*")
        self.cutoff_value = self._small_value("CUTOFF LIMIT", "3.20 V*")

        row.addLayout(self.ocp_value)
        row.addLayout(self.resistance_value)
        row.addLayout(self.cutoff_value)

        panel.layout().addWidget(battery)

        heading = QLabel("INDEPENDENT ESC STAGE THERMALS")
        heading.setObjectName("microLabel")
        panel.layout().addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(5)

        self.motor_values = []

        for i, (name, position, temperature) in enumerate([
            ("M1", "FL", 34),
            ("M2", "FR", 35),
            ("M3", "RL", 33),
            ("M4", "RR", 36),
        ]):
            cell = QFrame()
            cell.setObjectName("motorThermal")

            layout = QVBoxLayout(cell)
            layout.setContentsMargins(3, 6, 3, 6)

            name_label = QLabel(f"{name} ({position})")
            name_label.setObjectName("muted")
            name_label.setAlignment(Qt.AlignCenter)

            temp_label = QLabel(f"{temperature}°C*")
            temp_label.setObjectName("greenValue")
            temp_label.setAlignment(Qt.AlignCenter)

            layout.addWidget(name_label)
            layout.addWidget(temp_label)

            grid.addWidget(cell, 0, i)
            self.motor_values.append(temp_label)

        panel.layout().addLayout(grid)

        # Legacy API attributes expected by the existing application.
        self.battery_status = QLabel("3.84 V")
        self.battery_level = QLabel("78%")
        self.power_status = QLabel("DEMO")

        return panel

    # ==================================================
    # MCU / RF
    # ==================================================

    def _build_mcu_panel(self):
        """Return illustrative MCU and radio-status readouts."""
        panel = self._panel()

        panel.layout().addLayout(
            self._panel_header("⚙ MCU & RF Transceiver", "SIMULATED", "neutral")
        )

        grid = QGridLayout()
        grid.setSpacing(5)

        for i, (title, value) in enumerate([
            ("PRIMARY CORE", "ESP32-S3*"),
            ("CORE TEMP", "38.5°C*"),
            ("CPU LOAD", "42%*"),
            ("HEAP FREE", "184 KB*"),
        ]):
            grid.addWidget(self._stat_cell(title, value), 0, i)

        panel.layout().addLayout(grid)

        radio = QHBoxLayout()

        self.rssi_value = QLabel("RF RSSI: -52 dBm*")
        self.packet_loss_value = QLabel("PKT LOSS: 0.006%*")
        self.latency_value = QLabel("RTT LATENCY: 4.2 ms*")

        for label in (
            self.rssi_value,
            self.packet_loss_value,
            self.latency_value,
        ):
            label.setObjectName("greenValue")
            radio.addWidget(label)

        panel.layout().addLayout(radio)
        return panel

    # ==================================================
    # EVENT LOG
    # ==================================================

    def _build_log_panel(self):
        """Return the subsystem event display with level filters and clear action."""
        panel = self._panel()
        panel.setMinimumHeight(240)

        header = QHBoxLayout()

        title = QLabel("▣ Subsystem Log")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()

        self.log_filter_buttons = {}

        for name in ("ALL", "INFO", "DEBUG", "WARN", "ERROR"):
            button = QPushButton(name)
            button.setObjectName("logFilterActive" if name == "ALL" else "logFilter")
            button.setMaximumHeight(27)
            button.clicked.connect(
                lambda checked=False, value=name: self._set_log_filter(value)
            )
            header.addWidget(button)
            self.log_filter_buttons[name] = button

        panel.layout().addLayout(header)

        self.event_log = QLabel()
        self.event_log.setObjectName("eventLog")
        self.event_log.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.event_log.setWordWrap(True)
        self.event_log.setMinimumHeight(130)
        self.event_log.setTextInteractionFlags(Qt.TextSelectableByMouse)

        panel.layout().addWidget(self.event_log, 1)

        controls = QHBoxLayout()

        self.autoscroll = QCheckBox("AUTO-SCROLL")
        self.autoscroll.setChecked(True)
        self.autoscroll.setObjectName("logCheckbox")

        self.log_buffer_label = QLabel("BUFFER: 0 / 1000 LINES")
        self.log_buffer_label.setObjectName("muted")

        clear_button = QPushButton("CLEAR BUFFER")
        clear_button.setObjectName("textButton")
        clear_button.clicked.connect(self.clear_status)

        controls.addWidget(self.autoscroll)
        controls.addWidget(self.log_buffer_label)
        controls.addStretch()
        controls.addWidget(clear_button)

        panel.layout().addLayout(controls)
        return panel

    def _set_log_filter(self, value):
        """Select an exact event level, or ALL, and refresh the filtered display."""
        self.log_filter = value

        for name, button in self.log_filter_buttons.items():
            button.setObjectName(
                "logFilterActive" if name == value else "logFilter"
            )
            button.style().unpolish(button)
            button.style().polish(button)

        self._render_log()

    def _append_event(self, level, message):
        """Append a timestamped event, retaining the latest 1000, and refresh."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_entries.append((timestamp, level, message))
        self._log_entries = self._log_entries[-1000:]
        self._render_log()

    def _render_log(self):
        """Display the latest 80 events matching the filter and total buffer size."""
        entries = self._log_entries

        if self.log_filter != "ALL":
            entries = [
                entry for entry in entries if entry[1] == self.log_filter
            ]

        if entries:
            text = "\n".join(
                f"[{time}] [{level}] {message}"
                for time, level, message in entries[-80:]
            )
        else:
            text = "No events for this filter."

        self.event_log.setText(text)
        self.log_buffer_label.setText(
            f"BUFFER: {len(self._log_entries)} / 1000 LINES"
        )

    # ==================================================
    # FOOTERS
    # ==================================================

    def _build_daemon_strip(self):
        """Return demo monitor, protocol, and unverified bus-status indicators."""
        frame = QFrame()
        frame.setObjectName("daemonStrip")

        row = QHBoxLayout(frame)
        row.setContentsMargins(6, 5, 6, 5)

        self.daemon_status = QLabel(
            "● DEMO MONITOR ACTIVE · HARDWARE NOT VERIFIED"
        )
        self.daemon_status.setObjectName("muted")

        self.protocol_status = QLabel("PROTOCOL: DEMO ONLY")
        self.protocol_status.setObjectName("amberValue")

        self.bus_integrity = QLabel("BUS INTEGRITY: UNKNOWN")
        self.bus_integrity.setObjectName("strongValue")

        row.addWidget(self.daemon_status)
        row.addStretch()
        row.addWidget(self.protocol_status)
        row.addSpacing(10)
        row.addWidget(self.bus_integrity)

        return frame

    def _build_bottom_bar(self):
        """Return the footer with demo flight, sensor, and clock readouts."""
        frame = QFrame()
        frame.setObjectName("bottomBar")

        row = QHBoxLayout(frame)
        row.setContentsMargins(9, 5, 9, 5)
        row.setSpacing(10)

        self.armed_status = QLabel("● DEMO [HOVER READY]")
        self.armed_status.setObjectName("greenValue")

        self.footer_battery = QLabel("BATT: 3.84 V*")
        self.footer_tof = QLabel("TOF: DEMO LOCK")
        self.footer_flow = QLabel("FLOW: DEMO TRACKING")
        self.footer_failsafe = QLabel("FAIL-SAFE: SIMULATION ONLY")
        self.clock_label = QLabel("SYS_CLK: --:--:--")

        for label in (
            self.footer_battery,
            self.footer_tof,
            self.footer_flow,
            self.footer_failsafe,
            self.clock_label,
        ):
            label.setObjectName("footerText")

        row.addWidget(self.armed_status)
        row.addWidget(self.footer_battery)
        row.addWidget(self.footer_tof)
        row.addWidget(self.footer_flow)
        row.addStretch()
        row.addWidget(self.footer_failsafe)
        row.addWidget(self.clock_label)

        return frame

    # ==================================================
    # COMPONENT HELPERS
    # ==================================================

    def _panel(self):
        """Return an empty styled panel with a vertical content layout."""
        frame = QFrame()
        frame.setObjectName("panel")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 10)
        layout.setSpacing(8)

        return frame

    def _panel_header(self, title, badge_text, tone):
        """Return a title row with a badge styled by the supplied tone name."""
        row = QHBoxLayout()

        label = QLabel(title)
        label.setObjectName("panelTitle")

        badge = QLabel(badge_text)
        badge.setObjectName(f"badge_{tone}")
        badge.setAlignment(Qt.AlignCenter)

        row.addWidget(label, 1)
        row.addWidget(badge)
        return row

    def _badge(self, text, tone):
        """Return a centered status badge styled by the supplied tone name."""
        label = QLabel(text)
        label.setObjectName(f"badge_{tone}")
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(29)
        return label

    def _stat_cell(self, title, value):
        """Return a compact panel containing a title and wrapping value label."""
        frame = QFrame()
        frame.setObjectName("statCell")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("microLabel")

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame

    def _small_value(self, title, value):
        """Return a vertical layout containing a heading and highlighted value."""
        column = QVBoxLayout()

        heading = QLabel(title)
        heading.setObjectName("microLabel")

        label = QLabel(value)
        label.setObjectName("greenValue")
        label.setWordWrap(True)

        column.addWidget(heading)
        column.addWidget(label)
        return column

    # ==================================================
    # LEGACY API COMPATIBILITY
    # ==================================================

    def _build_legacy_aliases(self):
        """Expose labels expected by legacy application callers.

        Some names alias visible readouts; sensor, packet-count, and power
        compatibility labels are separate from the visible panel contents.
        """
        # These labels are attached to visible widgets so legacy
        # code can safely call setText() on them.
        self.system_status = self.integrity_value
        self.app_status = self.daemon_status
        self.data_source = self.stream_badge

        self.tof_status = QLabel("DEMO")
        self.optical_flow_status = QLabel("DEMO")
        self.imu_status = QLabel("NOT CONFIGURED")

        self.link_status = self.link_badge
        self.packet_status = self.packets_badge
        self.packet_count = QLabel("148")

        # Preserve the power aliases created in the power panel.
        self.battery_status.setText("3.84 V")
        self.battery_level.setText("78%")
        self.power_status.setText("DEMO")

    # ==================================================
    # ANIMATED DEMO VALUES
    # ==================================================

    def _update_demo_values(self):
        """Advance simulated sensor, power, motor, and radio readouts.

        Do nothing once update_telemetry has selected packet-driven updates.
        Unparseable demo motor temperatures fall back to 35 degrees Celsius.
        """
        if self._has_telemetry:
            return

        self._demo_tick += 1

        # Slowly fluctuate battery voltage.
        self._demo_battery += random.uniform(-0.008, 0.006)
        self._demo_battery = max(3.45, min(4.18, self._demo_battery))
        battery = self._demo_battery

        charge = max(0, min(100, int((battery - 3.3) / 0.9 * 100)))

        self.battery_number.setText(f"{battery:.2f}")
        self.battery_status.setText(f"{battery:.2f} V")
        self.battery_level.setText(f"{charge}%")
        self.footer_battery.setText(f"BATT: {battery:.2f} V*")

        # Simulated battery condition.
        if battery >= 3.7:
            power_condition = "NOMINAL"
        elif battery >= 3.5:
            power_condition = "LOW"
        else:
            power_condition = "CRITICAL"

        self.power_status.setText(power_condition)

        # Update the ranging matrix with small, continuous changes.
        for index, cell in enumerate(self.tof_cells):
            old_value = self._demo_matrix[index]

            # A few center cells represent a simulated nearby object.
            row, col = divmod(index, 8)
            center_distance = math.sqrt(
                (row - 3.5) ** 2 + (col - 3.5) ** 2
            )

            target = 200 + int(center_distance * 40)
            if self._demo_tick % 12 < 6:
                target += 40

            new_value = int(
                old_value * 0.72
                + target * 0.28
                + random.uniform(-7, 7)
            )
            new_value = max(100, min(500, new_value))

            self._demo_matrix[index] = new_value
            cell.setText(str(new_value))

            tone = self._tof_tone(new_value)
            if cell.objectName() != tone:
                cell.setObjectName(tone)
                cell.style().unpolish(cell)
                cell.style().polish(cell)

        # Central distance estimate from the center four cells.
        center_indices = (27, 28, 35, 36)
        center_average = sum(
            self._demo_matrix[i] for i in center_indices
        ) / len(center_indices)

        self.center_avg_label.setText(f"{center_average:.1f} mm*")
        self.dev_jitter_label.setText(
            f"±{random.uniform(0.6, 2.5):.1f} mm*"
        )
        self.frame_drift_label.setText(
            f"{random.uniform(0.01, 0.12):.2f}%*"
        )

        # Optical flow confidence.
        confidence = random.randint(78, 98)
        self.flow_confidence.setText(f"{confidence}%*")
        self.flow_bar.setValue(confidence)

        self.delta_x_value.setText(
            f"{random.uniform(-0.4, 0.4):+.2f} px*"
        )
        self.delta_y_value.setText(
            f"{random.uniform(-0.4, 0.4):+.2f} px*"
        )

        # Motor temperatures drift gradually rather than jumping wildly.
        for motor in self.motor_values:
            previous_text = motor.text().replace("°C*", "")
            try:
                previous_temp = float(previous_text)
            except ValueError:
                previous_temp = 35.0

            new_temp = previous_temp + random.uniform(-0.7, 0.7)
            new_temp = max(29.0, min(45.0, new_temp))
            motor.setText(f"{new_temp:.1f}°C*")

        # Simulated radio, latency and packet statistics.
        self._demo_packet_count += random.randint(1, 3)

        rtt = random.uniform(3.2, 8.8)
        rssi = random.randint(48, 62)
        loss = random.uniform(0.0, 0.08)

        self.packets_badge.setText(
            f"PKTS: {self._demo_packet_count:,}"
        )
        self.packet_count.setText(str(self._demo_packet_count))
        self.rtt_badge.setText(f"RTT: {rtt:.1f} ms*")
        self.latency_value.setText(f"RTT LATENCY: {rtt:.1f} ms*")
        self.rssi_value.setText(f"RF RSSI: -{rssi} dBm*")
        self.packet_loss_value.setText(f"PKT LOSS: {loss:.3f}%*")

        self.rate_badge.setText(
            f"RATE: {random.randint(9, 11)} Hz"
        )
        self.rtos_value.setText(
            f"{random.uniform(9.7, 10.2):.1f} Hz"
        )

        # Animate the demo update counter in the readiness strip.
        self.readiness_value.setText(
            f"8/8 DEMO INDICATORS · FRAME {self._demo_tick}"
        )

        # Keep logs readable: add an event every five seconds.
        if self._demo_tick % 10 == 0:
            self._append_event(
                "DEBUG",
                "Simulated sensor frame refreshed; no hardware data.",
            )

    # ==================================================
    # EXISTING TELEMETRY API
    # ==================================================

    def update_telemetry(self, packet):
        """Update packet readouts from a dictionary or an attribute-based object.

        Disable further demo updates, including when fields are missing.
        Missing link and sensor flags default to false; absent battery data
        leaves its readouts unchanged. Up to four list or tuple PWM entries
        replace the motor readouts. Invalid battery formatting errors propagate.
        """

        # Stop animation so it cannot overwrite packet-driven updates.
        self._has_telemetry = True
        if hasattr(self, "demo_timer"):
            self.demo_timer.stop()

        def get(source, key, default=None):
            """Read a dictionary key or object attribute, using default if absent."""
            if isinstance(source, dict):
                return source.get(key, default)
            return getattr(source, key, default)

        link_ok = bool(get(packet, "link_ok", False))
        battery = get(packet, "battery_v")
        motor_pwm = get(packet, "motor_pwm", [])

        sensors = get(packet, "sensor_status", {})
        tof_ok = bool(get(sensors, "tof", False))
        flow_ok = bool(get(sensors, "optical_flow", False))

        self.link_badge.setText(
            "● LINK: CONNECTED" if link_ok else "● LINK: LOST"
        )

        self.tof_status.setText(
            "OK" if tof_ok else "UNAVAILABLE"
        )
        self.optical_flow_status.setText(
            "OK" if flow_ok else "UNAVAILABLE"
        )

        self.integrity_value.setText(
            "■ PACKET HEALTHY"
            if link_ok and tof_ok and flow_ok
            else "■ CHECK REQUIRED"
        )

        if battery is not None:
            self.battery_number.setText(f"{battery:.2f}")
            self.battery_status.setText(f"{battery:.2f} V")
            self.footer_battery.setText(f"BATT: {battery:.2f} V")

        if isinstance(motor_pwm, (list, tuple)):
            for index, pwm in enumerate(motor_pwm[:4]):
                self.motor_values[index].setText(f"{pwm} PWM*")

        self._append_event(
            "INFO",
            "Packet received by diagnostics panel.",
        )

    # ==================================================
    # BUTTON ACTIONS
    # ==================================================

    def run_system_check(self):
        """Display completion of a demo self-check without testing hardware."""
        self._append_event(
            "INFO",
            "Demo self-check completed; physical hardware not tested.",
        )
        self.daemon_status.setText(
            "DEMO CHECK COMPLETE · HARDWARE NOT VERIFIED"
        )

    def clear_status(self):
        """Clear the event buffer and acknowledge it in the monitor status."""
        self._log_entries.clear()
        self._render_log()
        self.daemon_status.setText("Log buffer cleared.")

    def _update_clock(self):
        """Refresh the clock label with local time when the label exists."""
        if hasattr(self, "clock_label"):
            self.clock_label.setText(
                f"SYS_CLK: {datetime.now().strftime('%H:%M:%S')}"
            )

    # ==================================================
    # STYLES
    # ==================================================

    def _apply_styles(self):
        """Apply the diagnostics palette and component styles to this panel."""
        c = self.C

        self.setStyleSheet(
            f"""
            QWidget#diagnosticsContent {{
                background: {c["bg"]};
                color: {c["text"]};
                font-family: Consolas, "Segoe UI", monospace;
                font-size: 11px;
            }}

            QWidget {{
                color: {c["text"]};
                font-family: Consolas, "Segoe UI", monospace;
                font-size: 11px;
            }}

            QScrollArea {{
                border: none;
                background: {c["bg"]};
            }}

            QFrame#topBar, QFrame#bottomBar {{
                background: #090B09;
                border: 1px solid {c["border"]};
            }}

            QLabel#brand {{
                color: {c["orange"]};
                font-size: 15px;
                font-weight: 800;
            }}

            QLabel#panelTitle {{
                color: {c["text"]};
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 700;
            }}

            QLabel#muted, QLabel#microLabel {{
                color: {c["muted"]};
            }}

            QLabel#microLabel {{
                font-size: 9px;
                letter-spacing: 1px;
            }}

            QFrame#readinessPanel {{
                background: {c["panel"]};
                border: 1px solid {c["border"]};
                border-radius: 5px;
            }}

            QFrame#panel {{
                background: {c["panel"]};
                border: 1px solid {c["border"]};
                border-radius: 5px;
            }}

            QFrame#innerPanel {{
                background: #242722;
                border: 1px solid {c["border"]};
            }}

            QFrame#statCell {{
                background: {c["inner"]};
                border: 1px solid #242822;
            }}

            QLabel#statValue {{
                color: {c["text"]};
                font-weight: 700;
            }}

            QLabel#greenValue {{
                color: {c["green"]};
                font-weight: 700;
            }}

            QLabel#amberValue {{
                color: {c["amber"]};
                font-weight: 700;
            }}

            QLabel#strongValue {{
                color: {c["text"]};
                font-weight: 700;
            }}

            QLabel#bigValue {{
                color: {c["orange"]};
                font-size: 19px;
                font-weight: 800;
            }}

            QLabel#batteryNumber {{
                color: {c["amber"]};
                font-size: 27px;
                font-weight: 800;
            }}

            QLabel#badge_green {{
                color: {c["green"]};
                background: #20352A;
                border: 1px solid #365745;
                padding: 5px 8px;
                font-weight: 700;
            }}

            QLabel#badge_amber {{
                color: #17120B;
                background: {c["orange"]};
                border: 1px solid {c["amber"]};
                padding: 5px 8px;
                font-weight: 800;
            }}

            QLabel#badge_neutral {{
                color: {c["text"]};
                background: #20231F;
                border: 1px solid {c["border"]};
                padding: 5px 8px;
            }}

            QFrame#zone_orange {{
                background: {c["orange"]};
                border: 1px solid #B96B2F;
            }}

            QFrame#zone_green {{
                background: #80AA94;
                border: 1px solid #5F8A73;
            }}

            QFrame#zone_neutral {{
                background: #3A3B35;
                border: 1px solid #4A4B44;
            }}

            QLabel#zoneText {{
                color: #10120F;
                font-weight: 700;
                font-size: 10px;
            }}

            QLabel#heatHot {{
                color: #18100A;
                background: {c["orange"]};
                border: 1px solid #BD7137;
                font-weight: 700;
            }}

            QLabel#heatNormal {{
                color: #101A14;
                background: #82B29B;
                border: 1px solid #648F79;
                font-weight: 700;
            }}

            QLabel#heatFar {{
                color: {c["text"]};
                background: #292C27;
                border: 1px solid #3B4039;
            }}

            QFrame#motorThermal {{
                background: #252822;
                border: 1px solid {c["border"]};
            }}

            QProgressBar#confidenceBar {{
                background: #343831;
                border: none;
                border-radius: 2px;
            }}

            QProgressBar#confidenceBar::chunk {{
                background: {c["green"]};
            }}

            QLabel#eventLog {{
                color: #D8D8CE;
                background: #0A0C0A;
                border: 1px solid #2B302A;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 10px;
            }}

            QCheckBox#logCheckbox {{
                color: {c["muted"]};
            }}

            QPushButton {{
                padding: 5px 7px;
                border-radius: 2px;
                font-weight: 700;
            }}

            QPushButton#actionButton {{
                color: #19130C;
                background: {c["orange"]};
                border: 1px solid #FFBD79;
                padding: 8px 12px;
            }}

            QPushButton#actionButton:hover {{
                background: #FFB56E;
            }}

            QPushButton#logFilter {{
                color: {c["muted"]};
                background: #171A16;
                border: 1px solid {c["border"]};
            }}

            QPushButton#logFilterActive {{
                color: #18120B;
                background: {c["orange"]};
                border: 1px solid {c["amber"]};
            }}

            QPushButton#textButton {{
                color: {c["text"]};
                background: transparent;
                border: none;
            }}

            QFrame#daemonStrip {{
                background: #0B0D0B;
                border-top: 1px solid {c["border"]};
            }}

            QLabel#footerText {{
                color: {c["muted"]};
                font-size: 10px;
            }}
            """
        )
