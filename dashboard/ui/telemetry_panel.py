from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from dashboard.services.telemetry import TelemetryPacket

class AltitudePlot(QWidget):
    def __init__(self, parent=None, max_samples=100):
        super().__init__(parent)
        self.max_samples = max_samples
        self.samples = deque(maxlen=self.max_samples)

        self.setMinimumHeight(150)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.MinimumExpanding
        )

    def add_sample(self, value: float):
        self.samples.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(
            self.rect(),
            QColor("#1e1e1e")
        )

        # Border
        painter.setPen(
            QPen(QColor("#3a3a3a"), 1)
        )

        painter.drawRect(
            0,
            0,
            self.width() - 1,
            self.height() - 1
        )

        # Nothing to draw yet
        if len(self.samples) < 1:
            return

        width = self.width()
        height = self.height()

        # Altitude scale
        min_val = 0.0
        max_val = max(
            100.0,
            max(self.samples) * 1.2
        )

        value_range = max_val - min_val

        if value_range <= 0:
            return

        # Graph line
        painter.setPen(
            QPen(QColor("#00ffcc"), 2)
        )

        points = []
        sample_count = len(self.samples)

        for i, value in enumerate(self.samples):

            if sample_count == 1:
                x = width / 2
            else:
                x = (
                    i / (sample_count - 1)
                ) * width

            y = height - (
                (value - min_val)
                / value_range
                * height
            )

            # Keep graph inside widget
            y = max(
                0,
                min(height, y)
            )

            points.append(
                QPointF(x, y)
            )

        # Connect points
        for i in range(len(points) - 1):
            painter.drawLine(
                points[i],
                points[i + 1]
            )

class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("TELEMETRY")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Top metrics layout
        metrics_layout = QGridLayout()
        
        # Altitude
        self.alt_label = self._create_value_label("0 cm")
        metrics_layout.addWidget(self._create_group("ALTITUDE", self.alt_label), 0, 0)
        
        # Battery
        self.bat_label = self._create_value_label("0.00 V")
        metrics_layout.addWidget(self._create_group("BATTERY", self.bat_label), 0, 1)
        
        # Link
        self.link_label = self._create_value_label("🔴 DISCONNECTED")
        metrics_layout.addWidget(self._create_group("LINK", self.link_label), 0, 2)
        
        layout.addLayout(metrics_layout)
        
        # Drift
        self.drift_label = self._create_value_label("X: 0.00   Y: 0.00")
        layout.addWidget(self._create_group("DRIFT", self.drift_label))
        
        # Sensors
        self.sensors_label = self._create_value_label("ToF: 🔴 ERR   Optical Flow: 🔴 ERR")
        layout.addWidget(self._create_group("SENSOR STATUS", self.sensors_label))
        
        # Motors
        self.motors_label = self._create_value_label("M1: 0   M2: 0   M3: 0   M4: 0")
        layout.addWidget(self._create_group("MOTOR PWM", self.motors_label))
        
        # Altitude History
        history_group = QFrame()
        history_group.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        history_layout = QVBoxLayout(history_group)
        hist_title = QLabel("ALTITUDE HISTORY")
        hist_title.setFont(QFont("Arial", 10, QFont.Bold))
        history_layout.addWidget(hist_title)
        
        self.alt_plot = AltitudePlot(max_samples=100)
        history_layout.addWidget(self.alt_plot)
        layout.addWidget(history_group)
        
    def _create_group(self, title_text, value_label):
        group = QFrame()
        group.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setStyleSheet("color: #888888;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(value_label)
        return group
        
    def _create_value_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 12))
        lbl.setAlignment(Qt.AlignCenter)
        return lbl
        
    def update_telemetry(self, packet: TelemetryPacket):
        # Altitude
        self.alt_label.setText(f"{packet.altitude_cm:.2f} cm")
        
        # Drift
        self.drift_label.setText(f"X: {packet.drift_x:.2f}   Y: {packet.drift_y:.2f}")
        
        # Battery
        bat_v = packet.battery_v
        if bat_v > 3.7:
            bat_status = "healthy"
            bat_color = "#00ff00"
        elif bat_v > 3.4:
            bat_status = "warning"
            bat_color = "#ffff00"
        else:
            bat_status = "critical"
            bat_color = "#ff0000"
        self.bat_label.setText(f"{bat_v:.2f} V ({bat_status})")
        self.bat_label.setStyleSheet(f"color: {bat_color};")
        
        # Link
        if packet.link_ok:
            self.link_label.setText("🟢 CONNECTED")
            self.link_label.setStyleSheet("color: #00ff00;")
        else:
            self.link_label.setText("🔴 DISCONNECTED")
            self.link_label.setStyleSheet("color: #ff0000;")
            
        # Sensor status
        tof_str = "🟢 OK" if packet.sensor_status.tof else "🔴 ERR"
        of_str = "🟢 OK" if packet.sensor_status.optical_flow else "🔴 ERR"
        self.sensors_label.setText(f"ToF: {tof_str}   Optical Flow: {of_str}")
        
        # Motors
        m = packet.motor_pwm
        if len(m) == 4:
            self.motors_label.setText(f"M1: {m[0]:3d}   M2: {m[1]:3d}   M3: {m[2]:3d}   M4: {m[3]:3d}")
            
        # History
        self.alt_plot.add_sample(packet.altitude_cm)
