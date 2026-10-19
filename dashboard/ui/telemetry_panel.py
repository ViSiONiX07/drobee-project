
"""
Bee-Brain GCS — Live Telemetry Dashboard.

Live packet fields:
- Altitude
- Lateral drift X/Y
- Battery voltage
- Motor PWM
- Communication link
- ToF and optical-flow status

The angular-rate chart uses simulated data until real IMU
measurements are supplied by the telemetry source.
"""

import math
import random
from collections import deque

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)

from dashboard.ui.theme import Palette, get_mono_font, get_ui_font


# ============================================================
# Shared UI helpers
# ============================================================

def card_frame():
    """Return an empty frame styled as a telemetry card."""
    frame = QFrame()
    frame.setObjectName("telemetryCard")
    frame.setStyleSheet(
        f"""
        QFrame#telemetryCard {{
            background-color: {Palette.BG_CARD};
            border: 1px solid {Palette.BORDER_HAIRLINE};
            border-radius: 4px;
        }}
        """
    )
    return frame


def styled_label(
    text,
    font=None,
    color=None,
    alignment=Qt.AlignmentFlag.AlignLeft
    | Qt.AlignmentFlag.AlignVCenter,
):
    """Return an aligned label, defaulting to the UI font and primary text color."""
    label = QLabel(text)
    label.setFont(font or get_ui_font(9))
    label.setAlignment(alignment)
    label.setStyleSheet(
        f"color: {color or Palette.TEXT_PRIMARY}; border: none;"
    )
    return label


def card_header(title, badge):
    """Return a title-and-badge header widget and its badge label."""
    header = QWidget()
    header.setFixedHeight(30)

    row = QHBoxLayout(header)
    row.setContentsMargins(10, 0, 10, 0)
    row.setSpacing(8)

    title_label = styled_label(
        title,
        get_ui_font(9, bold=True),
        Palette.TEXT_SECONDARY,
    )
    row.addWidget(title_label, 1)

    badge_label = styled_label(
        badge,
        get_mono_font(8, bold=True),
        Palette.ACCENT_SAGE,
        Qt.AlignmentFlag.AlignCenter,
    )
    badge_label.setStyleSheet(
        f"""
        color: {Palette.ACCENT_SAGE};
        background-color: {Palette.BG_INSET};
        border: 1px solid {Palette.BORDER_SUBTLE};
        border-radius: 2px;
        padding: 2px 5px;
        """
    )
    row.addWidget(badge_label)

    return header, badge_label


def card_layout(widget):
    """Attach and return the standard telemetry-card vertical layout."""
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 8)
    layout.setSpacing(5)
    return layout


# ============================================================
# Altitude card
# ============================================================

class AltitudeCard(QFrame):
    def __init__(self, parent=None):
        """Build altitude, target, and vertical-velocity placeholder readouts."""
        super().__init__(parent)
        self.setStyleSheet(card_frame().styleSheet())
        self.setMinimumHeight(150)

        outer = card_layout(self)
        header, self.badge = card_header(
            "ALTITUDE & Z-VELOCITY", "WAITING"
        )
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(10, 0, 10, 0)
        body.setSpacing(5)

        value_row = QHBoxLayout()

        self.value_label = styled_label(
            "--.--", get_mono_font(25, bold=True)
        )
        value_row.addWidget(self.value_label)

        value_row.addWidget(
            styled_label("m", get_ui_font(11), Palette.TEXT_MUTED)
        )
        value_row.addStretch()
        body.addLayout(value_row)

        self.setpoint_label = styled_label(
            "TARGET: NOT PROVIDED",
            get_mono_font(8),
            Palette.TEXT_MUTED,
        )
        body.addWidget(self.setpoint_label)

        self.velocity_label = styled_label(
            "VERTICAL VELOCITY: DEMO",
            get_mono_font(8),
            Palette.TEXT_SECONDARY,
        )
        body.addWidget(self.velocity_label)

        self.raw_label = styled_label(
            "RAW ALTITUDE: -- cm",
            get_mono_font(8),
            Palette.TEXT_SECONDARY,
        )
        body.addWidget(self.raw_label)

        outer.addLayout(body)


# ============================================================
# Drift radar and card
# ============================================================

class DriftRadar(QWidget):
    def __init__(self, parent=None):
        """Initialize a centered drift marker."""
        super().__init__(parent)
        self.setMinimumSize(78, 78)
        self.drift_x = 0.0
        self.drift_y = 0.0

    def set_drift(self, x, y):
        """Store drift components in their incoming units and request repaint.

        Float-conversion errors propagate; only the painted position is
        limited to the display corridor.
        """
        self.drift_x = float(x)
        self.drift_y = float(y)
        self.update()

    def paintEvent(self, event):
        """Paint a drift marker with each axis saturated at a magnitude of 0.20."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = max(1.0, min(self.width(), self.height()) / 2 - 5)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(
                QColor(Palette.BORDER_SUBTLE),
                1,
                Qt.PenStyle.DashLine,
            )
        )

        painter.drawEllipse(QPointF(cx, cy), radius, radius)
        painter.drawEllipse(
            QPointF(cx, cy), radius * 0.5, radius * 0.5
        )
        painter.drawLine(
            QPointF(cx - radius, cy),
            QPointF(cx + radius, cy),
        )
        painter.drawLine(
            QPointF(cx, cy - radius),
            QPointF(cx, cy + radius),
        )

        limit = 0.20
        nx = max(-1.0, min(1.0, self.drift_x / limit))
        ny = max(-1.0, min(1.0, self.drift_y / limit))

        point = QPointF(
            cx + nx * radius,
            cy - ny * radius,
        )

        painter.setPen(QPen(QColor(Palette.ACCENT_COPPER), 1))
        painter.setBrush(QBrush(QColor(Palette.ACCENT_COPPER)))
        painter.drawEllipse(point, 4, 4)
        painter.end()


class DriftCard(QFrame):
    def __init__(self, parent=None):
        """Build the drift radar and its displacement and corridor-status readouts."""
        super().__init__(parent)
        self.setStyleSheet(card_frame().styleSheet())
        self.setMinimumHeight(150)

        outer = card_layout(self)
        header, self.badge = card_header(
            "2D LATERAL DRIFT", "LIVE"
        )
        outer.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(8, 0, 8, 0)
        body.setSpacing(8)

        self.radar = DriftRadar()
        body.addWidget(self.radar)

        details = QVBoxLayout()

        self.position_label = styled_label(
            "POS DRIFT X / Y\n+0.00 / +0.00",
            get_mono_font(9, bold=True),
        )
        details.addWidget(self.position_label)

        self.status_label = styled_label(
            "WAITING FOR DATA",
            get_mono_font(8),
            Palette.TEXT_MUTED,
        )
        details.addWidget(self.status_label)
        details.addStretch()

        body.addLayout(details, 1)
        outer.addLayout(body)


# ============================================================
# Battery card
# ============================================================

class BatteryCard(QFrame):
    def __init__(self, parent=None):
        """Build voltage readouts and an initially empty visual battery bar."""
        super().__init__(parent)
        self.setStyleSheet(card_frame().styleSheet())
        self.setMinimumHeight(150)

        outer = card_layout(self)
        header, self.badge = card_header(
            "BATTERY VOLTAGE", "LIVE"
        )
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(10, 0, 10, 0)
        body.setSpacing(5)

        value_row = QHBoxLayout()
        self.value_label = styled_label(
            "--.--", get_mono_font(25, bold=True)
        )
        value_row.addWidget(self.value_label)
        value_row.addWidget(
            styled_label("V", get_ui_font(11), Palette.TEXT_MUTED)
        )
        value_row.addStretch()
        body.addLayout(value_row)

        self.status_label = styled_label(
            "WAITING FOR DATA",
            get_mono_font(8, bold=True),
            Palette.TEXT_MUTED,
        )
        body.addWidget(self.status_label)

        self.bar = QFrame()
        self.bar.setFixedHeight(7)
        self.bar.setStyleSheet(
            f"""
            background-color: {Palette.BG_INSET};
            border: 1px solid {Palette.BORDER_SUBTLE};
            border-radius: 2px;
            """
        )

        self.fill = QFrame(self.bar)
        self.fill.setGeometry(1, 1, 0, 5)
        body.addWidget(self.bar)

        self.extra_label = styled_label(
            "CURRENT / POWER: NOT PROVIDED",
            get_mono_font(8),
            Palette.TEXT_MUTED,
        )
        body.addWidget(self.extra_label)

        outer.addLayout(body)
        self._fraction = 0.0

    def resizeEvent(self, event):
        """Resize the battery fill after the card is resized."""
        super().resizeEvent(event)
        self._resize_fill()

    def _resize_fill(self):
        """Fit the battery fill to the available bar area using the stored fraction."""
        width = max(0, self.bar.width() - 2)
        height = max(0, self.bar.height() - 2)
        self.fill.setGeometry(
            1, 1, int(width * self._fraction), height
        )

    def update_voltage(self, voltage):
        """Display voltage in volts with status thresholds and a visual fill.

        Values above 3.7 are healthy, above 3.4 through 3.7 are warnings, and
        3.4 or below are critical. Fill scales linearly from empty at 3.0 V to
        full at 4.2 V, clamped at the ends; it is not calibrated state of charge.
        """
        self.value_label.setText(f"{voltage:.2f}")

        if voltage > 3.7:
            status = "HEALTHY"
            color = Palette.ACCENT_SAGE
        elif voltage > 3.4:
            status = "WARNING"
            color = Palette.ACCENT_AMBER
        else:
            status = "CRITICAL"
            color = Palette.ACCENT_CRIMSON

        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            f"color: {color}; border: none;"
        )

        # Approximate visual indicator only; not calibrated battery SOC.
        self._fraction = max(
            0.0, min(1.0, (voltage - 3.0) / 1.2)
        )
        self.fill.setStyleSheet(
            f"background-color: {color}; border: none;"
        )
        self._resize_fill()


# ============================================================
# Communication card
# ============================================================

class CommsCard(QFrame):
    def __init__(self, parent=None):
        """Build link status with placeholders for unavailable communication metrics."""
        super().__init__(parent)
        self.setStyleSheet(card_frame().styleSheet())
        self.setMinimumHeight(150)

        outer = card_layout(self)
        header, self.badge = card_header(
            "COMMUNICATION LINK", "SIMULATED"
        )
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(10, 0, 10, 0)
        body.setSpacing(5)

        self.status_label = styled_label(
            "WAITING FOR PACKET",
            get_mono_font(10, bold=True),
            Palette.TEXT_MUTED,
        )
        body.addWidget(self.status_label)

        body.addWidget(
            styled_label(
                "RSSI: NOT PROVIDED",
                get_mono_font(8),
                Palette.TEXT_MUTED,
            )
        )
        body.addWidget(
            styled_label(
                "LATENCY: NOT PROVIDED",
                get_mono_font(8),
                Palette.TEXT_MUTED,
            )
        )
        body.addWidget(
            styled_label(
                "PACKET LOSS: NOT PROVIDED",
                get_mono_font(8),
                Palette.TEXT_MUTED,
            )
        )

        outer.addLayout(body)

    def update_link(self, connected):
        """Display connected or disconnected status with the corresponding color."""
        if connected:
            self.status_label.setText("● CONNECTED")
            color = Palette.ACCENT_SAGE
        else:
            self.status_label.setText("● DISCONNECTED")
            color = Palette.ACCENT_CRIMSON

        self.status_label.setStyleSheet(
            f"color: {color}; border: none;"
        )


# ============================================================
# Live line chart
# ============================================================

class StaticLineChart(QWidget):
    """
    Custom rolling chart.

    Kept under the original class name so the page can be updated
    without changing its chart construction elsewhere.
    """

    def __init__(
        self,
        series_a=None,
        series_b=None,
        y_max=5.0,
        y_label_fmt=None,
        legend=None,
        parent=None,
        y_min=None,
    ):
        """Initialize up to two sample series and their vertical display range.

        When y_min is omitted it defaults to -y_max. y_label_fmt formats axis
        values; legend supplies (label, color) pairs. Samples are evenly spaced
        across the plot, without a timestamp axis.
        """
        super().__init__(parent)

        self.series_a = list(series_a or [])
        self.series_b = list(series_b or [])
        self.y_max = float(y_max)
        self.y_min = (
            float(y_min) if y_min is not None else -float(y_max)
        )
        self.y_label_fmt = y_label_fmt or (
            lambda value: f"{value:.1f}"
        )
        self.legend = list(legend or [])

        self.setMinimumHeight(190)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_series(self, series_a, series_b=None):
        """Copy samples and repaint, preserving the second series when omitted."""
        self.series_a = list(series_a)

        if series_b is not None:
            self.series_b = list(series_b)

        self.update()

    def paintEvent(self, event):
        """Paint series within the configured range, grid, and legend.

        Draw no chart when the plot area is too small or y_max is not greater
        than y_min. Values outside the range are drawn at its nearest edge.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor(Palette.BG_INSET))
        painter.setPen(QPen(QColor(Palette.BORDER_HAIRLINE), 1))
        painter.drawRect(0, 0, rect.width() - 1, rect.height() - 1)

        pad_left = 14
        pad_right = 68
        pad_top = 18
        pad_bottom = 25

        plot_width = rect.width() - pad_left - pad_right
        plot_height = rect.height() - pad_top - pad_bottom

        if plot_width <= 10 or plot_height <= 10:
            painter.end()
            return

        value_range = self.y_max - self.y_min
        if value_range <= 0:
            painter.end()
            return

        painter.setFont(get_mono_font(8))

        for index in range(5):
            fraction = index / 4
            y = pad_top + plot_height - fraction * plot_height
            value = self.y_min + fraction * value_range

            painter.setPen(
                QPen(
                    QColor(Palette.BORDER_SUBTLE),
                    1,
                    Qt.PenStyle.DashLine,
                )
            )
            painter.drawLine(
                pad_left,
                int(y),
                pad_left + plot_width,
                int(y),
            )

            painter.setPen(QPen(QColor(Palette.TEXT_MUTED)))
            painter.drawText(
                pad_left + plot_width + 5,
                int(y) + 4,
                self.y_label_fmt(value),
            )

        def draw_series(values, color):
            """Draw sample segments with positions clamped to the y range."""
            if not values:
                return

            count = len(values)
            points = []

            for index, value in enumerate(values):
                x = pad_left + (
                    index / max(1, count - 1)
                ) * plot_width

                normalized = (
                    (float(value) - self.y_min) / value_range
                )
                normalized = max(0.0, min(1.0, normalized))
                y = (
                    pad_top
                    + plot_height
                    - normalized * plot_height
                )
                points.append(QPointF(x, y))

            painter.setPen(
                QPen(QColor(color), 1.8, Qt.PenStyle.SolidLine)
            )

            for index in range(len(points) - 1):
                painter.drawLine(points[index], points[index + 1])

        draw_series(self.series_a, Palette.ACCENT_SAGE)
        draw_series(self.series_b, Palette.ACCENT_COPPER)

        legend_x = pad_left
        painter.setFont(get_mono_font(8, bold=True))

        for name, color in self.legend:
            painter.setPen(QPen(QColor(color)))
            painter.drawText(
                legend_x, rect.height() - 6, name
            )
            legend_x += len(name) * 7 + 16

        painter.end()


# ============================================================
# Sensor status table
# ============================================================

class SensorBusTable(QFrame):
    def __init__(self, parent=None):
        """Build sensor status rows and unavailable-sensor placeholders."""
        super().__init__(parent)
        self.setStyleSheet(card_frame().styleSheet())

        outer = card_layout(self)
        header, self.badge = card_header(
            "SENSOR STREAM HEALTH & BUS MATRIX", "LIVE STATUS"
        )
        outer.addWidget(header)

        grid = QGridLayout()
        grid.setContentsMargins(10, 4, 10, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        headers = [
            "SENSOR DEVICE",
            "BUS",
            "RATE",
            "STATE",
            "DIAGNOSTIC",
        ]

        for column, text in enumerate(headers):
            grid.addWidget(
                styled_label(
                    text, get_mono_font(8, bold=True),
                    Palette.TEXT_MUTED
                ),
                0,
                column,
            )

        rows = [
            ("ToF Rangefinder", "I2C", "SIM", "WAITING", "Packet status"),
            ("Optical Flow", "SPI", "SIM", "WAITING", "Packet status"),
            ("IMU", "SPI", "N/A", "NOT PROVIDED", "No IMU fields"),
            ("Barometer", "I2C", "N/A", "NOT PROVIDED", "No pressure field"),
        ]

        self.state_labels = {}

        for row_index, row in enumerate(rows, start=1):
            for column, text in enumerate(row):
                label = styled_label(
                    text,
                    get_mono_font(8),
                    Palette.TEXT_SECONDARY,
                )
                grid.addWidget(label, row_index, column)

                if row_index == 1 and column == 3:
                    self.state_labels["tof"] = label
                elif row_index == 2 and column == 3:
                    self.state_labels["flow"] = label

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 2)

        outer.addLayout(grid)

    def update_states(self, tof_ok, flow_ok):
        """Display nominal or error states for the ToF and optical-flow flags."""
        for key, is_ok in (
            ("tof", tof_ok),
            ("flow", flow_ok),
        ):
            label = self.state_labels[key]

            if is_ok:
                label.setText("NOMINAL")
                color = Palette.ACCENT_SAGE
            else:
                label.setText("ERROR")
                color = Palette.ACCENT_CRIMSON

            label.setStyleSheet(f"color: {color}; border: none;")


# ============================================================
# Complete telemetry panel
# ============================================================

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        """Build telemetry cards and charts with 100-sample rolling buffers."""
        super().__init__(parent)

        self.altitude_history = deque(maxlen=100)
        self.roll_rate_history = deque(maxlen=100)
        self.pitch_rate_history = deque(maxlen=100)

        self.sample_count = 0
        self.previous_altitude_m = None
        self.previous_packet_time = None

        self.setObjectName("telemetryPage")
        self.setStyleSheet(
            f"""
            QWidget#telemetryPage {{
                background-color: {Palette.BG_CANVAS};
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(9)

        # Heading
        heading = QHBoxLayout()

        title = styled_label(
            "SUBSYSTEM TELEMETRY",
            get_ui_font(14, bold=True),
        )
        heading.addWidget(title)
        heading.addStretch()

        self.session_label = styled_label(
            "SOURCE: SIMULATED   BUFFER: 0 / 100",
            get_mono_font(8),
            Palette.TEXT_MUTED,
        )
        heading.addWidget(self.session_label)

        root.addLayout(heading)

        # Metric cards
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(8)
        metrics.setVerticalSpacing(8)

        self.altitude_card = AltitudeCard()
        self.drift_card = DriftCard()
        self.battery_card = BatteryCard()
        self.comms_card = CommsCard()

        metrics.addWidget(self.altitude_card, 0, 0)
        metrics.addWidget(self.drift_card, 0, 1)
        metrics.addWidget(self.battery_card, 0, 2)
        metrics.addWidget(self.comms_card, 0, 3)

        for column in range(4):
            metrics.setColumnStretch(column, 1)

        root.addLayout(metrics)

        # Altitude chart
        altitude_card = card_frame()
        altitude_layout = card_layout(altitude_card)

        header, self.altitude_badge = card_header(
            "ALTITUDE vs TIME", "ROLLING 100 SAMPLES"
        )
        altitude_layout.addWidget(header)

        self.altitude_chart = StaticLineChart(
            [],
            [],
            2.0,
            lambda value: f"{value:.2f} m",
            [("ALTITUDE (m)", Palette.ACCENT_SAGE)],
            y_min=0.0,
        )
        altitude_layout.addWidget(self.altitude_chart, 1)

        # Angular-rate chart
        rate_card = card_frame()
        rate_layout = card_layout(rate_card)

        header, self.rate_badge = card_header(
            "BODY ANGULAR RATES", "SIMULATED DATA"
        )
        rate_layout.addWidget(header)

        self.rate_chart = StaticLineChart(
            [],
            [],
            5.0,
            lambda value: f"{value:+.1f} °/s",
            [
                ("ROLL — DEMO", Palette.ACCENT_SAGE),
                ("PITCH — DEMO", Palette.ACCENT_COPPER),
            ],
            y_min=-5.0,
        )
        rate_layout.addWidget(self.rate_chart, 1)

        charts = QGridLayout()
        charts.setHorizontalSpacing(8)
        charts.addWidget(altitude_card, 0, 0)
        charts.addWidget(rate_card, 0, 1)
        charts.setColumnStretch(0, 1)
        charts.setColumnStretch(1, 1)

        root.addLayout(charts, 1)

        self.sensor_table = SensorBusTable()
        root.addWidget(self.sensor_table)

    # --------------------------------------------------------
    # Live telemetry update
    # --------------------------------------------------------

    def update_telemetry(self, packet):
        """Update cards and charts whenever a validated packet arrives.

        Convert altitude from centimeters to meters and estimate vertical
        velocity in meters per second after the first packet, using local
        receipt intervals with a 1 ms minimum. Retain the latest 100 altitude
        and synthetic angular-rate samples; angular rates are demo values,
        regardless of any extended IMU fields in the packet.
        """

        now = __import__("time").monotonic()

        # Altitude is provided in centimetres by the current contract.
        altitude_cm = float(packet.altitude_cm)
        altitude_m = altitude_cm / 100.0

        self.altitude_card.value_label.setText(
            f"{altitude_m:.2f}"
        )
        self.altitude_card.raw_label.setText(
            f"RAW ALTITUDE: {altitude_cm:.1f} cm"
        )

        # Estimate vertical velocity from successive altitude samples.
        if self.previous_altitude_m is not None:
            dt = max(0.001, now - self.previous_packet_time)
            vertical_velocity = (
                altitude_m - self.previous_altitude_m
            ) / dt

            self.altitude_card.velocity_label.setText(
                f"VERTICAL VELOCITY: {vertical_velocity:+.3f} m/s (EST.)"
            )

        self.previous_altitude_m = altitude_m
        self.previous_packet_time = now

        # Altitude history and autoscaling.
        self.altitude_history.append(altitude_m)
        altitude_values = list(self.altitude_history)

        if len(altitude_values) >= 2:
            low = min(altitude_values)
            high = max(altitude_values)
            center = (low + high) / 2.0
            half_range = max((high - low) * 1.5, 0.05)

            self.altitude_chart.y_min = max(
                0.0, center - half_range
            )
            self.altitude_chart.y_max = center + half_range
        else:
            self.altitude_chart.y_min = max(
                0.0, altitude_m - 0.1
            )
            self.altitude_chart.y_max = altitude_m + 0.1

        if self.altitude_chart.y_max <= self.altitude_chart.y_min:
            self.altitude_chart.y_max = (
                self.altitude_chart.y_min + 0.1
            )

        self.altitude_chart.set_series(altitude_values)

        self.session_label.setText(
            "SOURCE: SIMULATED TELEMETRY   "
            f"BUFFER: {len(self.altitude_history)} / 100"
        )

        # Drift
        drift_x = float(packet.drift_x)
        drift_y = float(packet.drift_y)

        self.drift_card.position_label.setText(
            f"POS DRIFT X / Y\n{drift_x:+.3f} / {drift_y:+.3f}"
        )
        self.drift_card.radar.set_drift(drift_x, drift_y)

        if abs(drift_x) <= 0.20 and abs(drift_y) <= 0.20:
            drift_text = "WITHIN DISPLAY CORRIDOR"
            drift_color = Palette.ACCENT_SAGE
        else:
            drift_text = "OUTSIDE DISPLAY CORRIDOR"
            drift_color = Palette.ACCENT_AMBER

        self.drift_card.status_label.setText(drift_text)
        self.drift_card.status_label.setStyleSheet(
            f"color: {drift_color}; border: none;"
        )

        # Battery
        self.battery_card.update_voltage(float(packet.battery_v))

        # Link
        self.comms_card.update_link(bool(packet.link_ok))

        # Sensor states
        tof_ok = bool(packet.sensor_status.tof)
        flow_ok = bool(packet.sensor_status.optical_flow)
        self.sensor_table.update_states(tof_ok, flow_ok)

        # ----------------------------------------------------
        # Angular rates: SIMULATION ONLY
        #
        # These values deliberately change on each incoming
        # packet. They are not readings from a physical IMU.
        # ----------------------------------------------------
        self.sample_count += 1
        t = self.sample_count * 0.1

        roll_rate = (
            2.2 * math.sin(2.0 * math.pi * 0.45 * t)
            + random.gauss(0.0, 0.08)
        )
        pitch_rate = (
            1.6 * math.sin(2.0 * math.pi * 0.35 * t + 0.8)
            + random.gauss(0.0, 0.08)
        )

        self.roll_rate_history.append(roll_rate)
        self.pitch_rate_history.append(pitch_rate)

        # This call triggers repainting of the graph.
        self.rate_chart.set_series(
            list(self.roll_rate_history),
            list(self.pitch_rate_history),
        )
