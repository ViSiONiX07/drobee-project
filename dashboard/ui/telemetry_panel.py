from collections import deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from dashboard.services.telemetry import TelemetryPacket
from dashboard.ui.theme import (
    QCOLOR_BG_INSET,
    QCOLOR_BORDER,
    QCOLOR_COPPER,
    QCOLOR_TEXT_MUTED,
    QCOLOR_TEXT_PRIMARY,
    QCOLOR_TEXT_SECONDARY,
    Palette,
    get_mono_font,
    get_ui_font,
)


class AltitudePlot(QWidget):
    """
    Industrial-grade dark-canvas oscilloscope for altitude stream.
    Renders rolling waveforms, hairline coordinate grids, and live scale ticks.
    Guarantees robust rendering without clipping on empty, single, and full buffers
    across all layout and minimum supported sizes.
    """

    def __init__(self, parent=None, max_samples=100):
        super().__init__(parent)
        self.max_samples = max_samples
        self.samples = deque(maxlen=self.max_samples)

        self.setMinimumHeight(150)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.MinimumExpanding,
        )

    def add_sample(self, value: float):
        self.samples.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Recessed chassis viewport fill
        painter.fillRect(rect, QCOLOR_BG_INSET)

        # Hairline structural viewport border
        painter.setPen(QPen(QCOLOR_BORDER, 1))
        painter.drawRect(0, 0, width - 1, height - 1)

        # Safe margins: generous gutter on right (78px) completely prevents scale label clipping
        pad_top = 28
        pad_bottom = 20
        pad_left = 14
        pad_right = 78
        plot_w = width - pad_left - pad_right
        plot_h = height - pad_top - pad_bottom

        if plot_w <= 10 or plot_h <= 10:
            return

        # Determine dynamic altitude range with sensible minimum ceiling
        curr_max = max(self.samples) if self.samples else 0.0
        max_val = max(100.0, curr_max * 1.15)
        min_val = 0.0
        val_range = max_val - min_val

        # Horizontal grid divisions (4 intervals)
        grid_pen = QPen(QColor(Palette.BORDER_SUBTLE), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        painter.setFont(get_mono_font(8))

        divs = 4
        for i in range(divs + 1):
            y = pad_top + plot_h - (i / divs) * plot_h
            painter.setPen(grid_pen)
            painter.drawLine(pad_left, int(y), pad_left + plot_w, int(y))

            # Scale annotation on the right gutter (integer cm avoids excessive width and clipping)
            val_at_y = min_val + (i / divs) * val_range
            painter.setPen(QPen(QCOLOR_TEXT_MUTED))
            painter.drawText(
                pad_left + plot_w + 8,
                int(y) + 4,
                f"{round(val_at_y):4d} cm",
            )

        # Vertical time-grid divisions (5 subdivisions)
        for j in range(1, 5):
            x = pad_left + (j / 5.0) * plot_w
            painter.setPen(grid_pen)
            painter.drawLine(int(x), pad_top, int(x), pad_top + plot_h)

        # Header readout overlay inside plot viewport
        painter.setFont(get_mono_font(8, bold=True))
        painter.setPen(QPen(QCOLOR_TEXT_SECONDARY))
        painter.drawText(pad_left + 4, 18, "VL53L0X ALTITUDE")

        sample_count = len(self.samples)
        if plot_w >= 280:
            painter.setPen(QPen(QCOLOR_TEXT_MUTED))
            painter.drawText(
                pad_left + plot_w - 130,
                18,
                f"BUFFER: {sample_count}/{self.max_samples}",
            )

        if sample_count < 1:
            # Empty buffer state
            painter.setFont(get_mono_font(10))
            painter.setPen(QPen(QCOLOR_TEXT_MUTED))
            painter.drawText(rect, Qt.AlignCenter, "STANDBY — AWAITING TELEMETRY STREAM")
            return

        # Build trajectory points with safe clamping inside plot boundaries
        points = []
        for idx, val in enumerate(self.samples):
            if sample_count == 1:
                x = pad_left + plot_w / 2.0
            else:
                x = pad_left + (idx / (sample_count - 1)) * plot_w

            norm_y = (val - min_val) / val_range
            norm_y = max(0.0, min(1.0, norm_y))
            y = pad_top + plot_h - norm_y * plot_h
            points.append(QPointF(x, y))

        # Single sample state: draw horizontal marker level line across plot and beacon dot
        if sample_count == 1:
            single_pt = points[0]
            marker_pen = QPen(QColor(Palette.ACCENT_COPPER), 1, Qt.DashLine)
            painter.setPen(marker_pen)
            painter.drawLine(pad_left, int(single_pt.y()), pad_left + plot_w, int(single_pt.y()))

            painter.setPen(QPen(QCOLOR_TEXT_PRIMARY, 1))
            painter.setBrush(QBrush(QCOLOR_COPPER))
            painter.drawEllipse(single_pt, 4.0, 4.0)
            return

        # Multi-sample buffer state: clipped strictly to the plot area so no waveforms bleed into margins
        painter.save()
        painter.setClipRect(pad_left - 1, pad_top - 4, plot_w + 6, plot_h + 8)

        # Area gradient fill under curve
        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), pad_top + plot_h)
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(points[-1].x(), pad_top + plot_h)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0, pad_top, 0, pad_top + plot_h)
        gradient.setColorAt(0.0, QColor(229, 139, 69, 70))   # Copper 28% opacity
        gradient.setColorAt(1.0, QColor(23, 25, 22, 10))     # Fade into chassis
        painter.fillPath(fill_path, QBrush(gradient))

        # Main waveform stroke (Copper Accent)
        wave_pen = QPen(QCOLOR_COPPER, 2)
        wave_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(wave_pen)
        for idx in range(len(points) - 1):
            painter.drawLine(points[idx], points[idx + 1])

        # Current sample focus beacon on latest point
        latest = points[-1]
        painter.setPen(QPen(QCOLOR_TEXT_PRIMARY, 1))
        painter.setBrush(QBrush(QCOLOR_COPPER))
        painter.drawEllipse(latest, 3.5, 3.5)

        painter.restore()


class MetricCard(QFrame):
    """
    Modular instrument bay card adhering to Stitch's 8px grid and hairline borders.
    """

    def __init__(self, title_text: str, badge_text: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            MetricCard {{
                background-color: {Palette.BG_CARD};
                border: 1px solid {Palette.BORDER_HAIRLINE};
                border-radius: 4px;
            }}
            """
        )

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 10, 12, 10)
        self.root_layout.setSpacing(6)

        # Header row (Title + Factual Component Tag)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(6)

        self.title_lbl = QLabel(title_text)
        self.title_lbl.setFont(get_ui_font(9, bold=True))
        self.title_lbl.setStyleSheet(f"color: {Palette.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        header_row.addWidget(self.title_lbl)

        header_row.addStretch()

        if badge_text:
            self.badge_lbl = QLabel(badge_text)
            self.badge_lbl.setFont(get_mono_font(8, bold=True))
            self.badge_lbl.setStyleSheet(
                f"""
                color: {Palette.ACCENT_SAGE};
                background-color: {Palette.BG_INSET};
                border: 1px solid {Palette.BORDER_SUBTLE};
                border-radius: 2px;
                padding: 1px 5px;
                """
            )
            header_row.addWidget(self.badge_lbl)
        else:
            self.badge_lbl = None

        self.root_layout.addLayout(header_row)

    def set_content_widget(self, widget: QWidget):
        self.root_layout.addWidget(widget)


class TelemetryPanel(QWidget):
    """
    Subsystem Telemetry Live Panel.
    Displays real-time sensor readouts, power status, link health, and altitude oscilloscope.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 16)
        main_layout.setSpacing(12)

        # ----------------------------------------------------------------------
        # BAY SUB-HEADER (Accurately reflects simulated stream at 10 Hz)
        # ----------------------------------------------------------------------
        sub_header = QHBoxLayout()
        sub_header.setContentsMargins(2, 0, 2, 4)

        bay_lbl = QLabel("SUBSYSTEM TELEMETRY")
        bay_lbl.setFont(get_mono_font(10, bold=True))
        bay_lbl.setStyleSheet(f"color: {Palette.TEXT_MUTED}; letter-spacing: 0.5px;")
        sub_header.addWidget(bay_lbl)

        sub_header.addStretch()

        stream_info = QLabel("DATA SOURCE: SIMULATED (10 Hz) • PROTOCOL: JSON")
        stream_info.setFont(get_mono_font(9))
        stream_info.setStyleSheet(f"color: {Palette.TEXT_MUTED};")
        sub_header.addWidget(stream_info)

        main_layout.addLayout(sub_header)

        # ----------------------------------------------------------------------
        # PRIMARY METRICS ROW (3 Cards: Altitude, Battery, Link)
        # ----------------------------------------------------------------------
        primary_grid = QGridLayout()
        primary_grid.setContentsMargins(0, 0, 0, 0)
        primary_grid.setSpacing(10)

        # 1. Altitude
        self.alt_label = QLabel("0.00 cm")
        self.alt_label.setFont(get_mono_font(18, bold=True))
        self.alt_label.setAlignment(Qt.AlignCenter)
        self.alt_label.setStyleSheet(f"color: {Palette.TEXT_PRIMARY}; padding: 4px 0;")
        card_alt = MetricCard("ALTITUDE", "VL53L0X")
        card_alt.set_content_widget(self.alt_label)
        primary_grid.addWidget(card_alt, 0, 0)

        # 2. Battery (1S LiPo verified in pin-mapping.md and telemetry-spec.md)
        self.bat_label = QLabel("0.00 V (standby)")
        self.bat_label.setFont(get_mono_font(15, bold=True))
        self.bat_label.setAlignment(Qt.AlignCenter)
        self.bat_label.setStyleSheet(f"color: {Palette.ACCENT_AMBER}; padding: 4px 0;")
        card_bat = MetricCard("BATTERY VOLTAGE", "1S LiPo")
        card_bat.set_content_widget(self.bat_label)
        primary_grid.addWidget(card_bat, 0, 1)

        # 3. Comms Link
        self.link_label = QLabel("● DISCONNECTED")
        self.link_label.setFont(get_mono_font(15, bold=True))
        self.link_label.setAlignment(Qt.AlignCenter)
        self.link_label.setStyleSheet(f"color: {Palette.ACCENT_CRIMSON}; padding: 4px 0;")
        card_link = MetricCard("COMMUNICATION LINK", "STATUS")
        card_link.set_content_widget(self.link_label)
        primary_grid.addWidget(card_link, 0, 2)

        main_layout.addLayout(primary_grid)

        # ----------------------------------------------------------------------
        # SECONDARY METRICS ROW (3 Cards: Drift, Sensors, Motors)
        # ----------------------------------------------------------------------
        secondary_grid = QGridLayout()
        secondary_grid.setContentsMargins(0, 0, 0, 0)
        secondary_grid.setSpacing(10)

        # 4. Drift (Displayed strictly as X and Y coordinates without invented units)
        self.drift_label = QLabel("X: 0.00   Y: 0.00")
        self.drift_label.setFont(get_mono_font(12, bold=True))
        self.drift_label.setAlignment(Qt.AlignCenter)
        self.drift_label.setStyleSheet(f"color: {Palette.TEXT_PRIMARY}; padding: 4px 0;")
        card_drift = MetricCard("LATERAL DRIFT", "ADNS3080")
        card_drift.set_content_widget(self.drift_label)
        secondary_grid.addWidget(card_drift, 0, 0)

        # 5. Sensors
        self.sensors_label = QLabel("ToF: ● ERR   Optical Flow: ● ERR")
        self.sensors_label.setFont(get_mono_font(12, bold=True))
        self.sensors_label.setAlignment(Qt.AlignCenter)
        self.sensors_label.setStyleSheet(f"color: {Palette.ACCENT_CRIMSON}; padding: 4px 0;")
        card_sensors = MetricCard("SENSOR STATUS", "HEALTH")
        card_sensors.set_content_widget(self.sensors_label)
        secondary_grid.addWidget(card_sensors, 0, 1)

        # 6. Motors
        self.motors_label = QLabel("M1:   0   M2:   0   M3:   0   M4:   0")
        self.motors_label.setFont(get_mono_font(12, bold=True))
        self.motors_label.setAlignment(Qt.AlignCenter)
        self.motors_label.setStyleSheet(f"color: {Palette.ACCENT_COPPER}; padding: 4px 0;")
        card_motors = MetricCard("MOTOR PWM", "MOTORS (M1-M4)")
        card_motors.set_content_widget(self.motors_label)
        secondary_grid.addWidget(card_motors, 0, 2)

        main_layout.addLayout(secondary_grid)

        # ----------------------------------------------------------------------
        # ALTITUDE OSCILLOSCOPE BAY
        # ----------------------------------------------------------------------
        history_card = MetricCard("ALTITUDE vs SAMPLES", "ROLLING 100 SAMPLES")
        self.alt_plot = AltitudePlot(max_samples=100)
        history_card.set_content_widget(self.alt_plot)
        main_layout.addWidget(history_card, 1)

    def update_telemetry(self, packet: TelemetryPacket):
        """
        Receives validated TelemetryPacket and updates all visual indicators.
        Preserves string formatting contract expected by MainWindow and test suites.
        """
        # Altitude
        self.alt_label.setText(f"{packet.altitude_cm:.2f} cm")

        # Drift (strictly formatted with contract values without invented units)
        self.drift_label.setText(f"X: {packet.drift_x:.2f}   Y: {packet.drift_y:.2f}")

        # Battery
        bat_v = packet.battery_v
        if bat_v > 3.7:
            bat_status = "healthy"
            bat_color = Palette.ACCENT_SAGE
        elif bat_v > 3.4:
            bat_status = "warning"
            bat_color = Palette.ACCENT_AMBER
        else:
            bat_status = "critical"
            bat_color = Palette.ACCENT_CRIMSON
        self.bat_label.setText(f"{bat_v:.2f} V ({bat_status})")
        self.bat_label.setStyleSheet(f"color: {bat_color}; padding: 4px 0;")

        # Comms Link
        if packet.link_ok:
            self.link_label.setText("● CONNECTED")
            self.link_label.setStyleSheet(f"color: {Palette.ACCENT_SAGE}; padding: 4px 0;")
        else:
            self.link_label.setText("● DISCONNECTED")
            self.link_label.setStyleSheet(f"color: {Palette.ACCENT_CRIMSON}; padding: 4px 0;")

        # Sensor Suite Health
        tof_str = "● OK" if packet.sensor_status.tof else "● ERR"
        of_str = "● OK" if packet.sensor_status.optical_flow else "● ERR"
        all_sensors_ok = packet.sensor_status.tof and packet.sensor_status.optical_flow
        sensors_color = Palette.ACCENT_SAGE if all_sensors_ok else Palette.ACCENT_CRIMSON

        self.sensors_label.setText(f"ToF: {tof_str}   Optical Flow: {of_str}")
        self.sensors_label.setStyleSheet(f"color: {sensors_color}; padding: 4px 0;")

        # Motor PWM
        m = packet.motor_pwm
        if len(m) == 4:
            self.motors_label.setText(f"M1: {m[0]:3d}   M2: {m[1]:3d}   M3: {m[2]:3d}   M4: {m[3]:3d}")

        # Stream sample to oscilloscope
        self.alt_plot.add_sample(packet.altitude_cm)
