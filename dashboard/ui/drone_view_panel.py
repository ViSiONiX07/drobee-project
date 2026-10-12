
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class DroneCanvas(QWidget):
    """Lightweight 3D-style drone visualization using QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        self.setMinimumSize(420, 340)

    def set_orientation(self, roll, pitch, yaw):
        self.roll = float(roll)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor("#17191d"))

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2 + 10

        # Background grid
        grid_pen = QPen(QColor("#292e35"), 1)
        painter.setPen(grid_pen)

        spacing = 35

        for x in range(0, width, spacing):
            painter.drawLine(x, 0, x, height)

        for y in range(0, height, spacing):
            painter.drawLine(0, y, width, y)

        # Draw orientation axes
        painter.setPen(QPen(QColor("#00b894"), 2))
        painter.drawLine(
            int(center_x - 110),
            int(center_y),
            int(center_x + 110),
            int(center_y),
        )

        painter.setPen(QPen(QColor("#4b8bff"), 2))
        painter.drawLine(
            int(center_x),
            int(center_y - 90),
            int(center_x),
            int(center_y + 90),
        )

        # Drone projection with roll, pitch and yaw.
        roll = math.radians(self.roll)
        pitch = math.radians(self.pitch)
        yaw = math.radians(self.yaw)

        def project(x, y, z):
            # Roll rotation
            y1 = y * math.cos(roll) - z * math.sin(roll)
            z1 = y * math.sin(roll) + z * math.cos(roll)

            # Pitch rotation
            x2 = x * math.cos(pitch) + z1 * math.sin(pitch)
            z2 = -x * math.sin(pitch) + z1 * math.cos(pitch)

            # Yaw rotation
            x3 = x2 * math.cos(yaw) - y1 * math.sin(yaw)
            y3 = x2 * math.sin(yaw) + y1 * math.cos(yaw)

            perspective = 1.0 + z2 / 500.0

            return (
                int(center_x + x3 * perspective),
                int(center_y + y3 * perspective),
            )

        arm_length = 72

        # Four motor positions
        motor_positions = [
            (-arm_length, -arm_length, 0),
            (arm_length, -arm_length, 0),
            (-arm_length, arm_length, 0),
            (arm_length, arm_length, 0),
        ]

        # Draw drone arms
        body = project(0, 0, 0)

        for position in motor_positions:
            motor = project(*position)

            painter.setPen(QPen(QColor("#9ba6b5"), 7))
            painter.drawLine(body[0], body[1], motor[0], motor[1])

            painter.setPen(QPen(QColor("#d9e0e8"), 2))
            painter.setBrush(QColor("#303943"))
            painter.drawEllipse(
                motor[0] - 12,
                motor[1] - 12,
                24,
                24,
            )

            # Propeller
            painter.setPen(QPen(QColor("#00b894"), 3))
            painter.drawLine(
                motor[0] - 8,
                motor[1],
                motor[0] + 8,
                motor[1],
            )

        # Central drone body
        painter.setPen(QPen(QColor("#00d6a5"), 2))
        painter.setBrush(QColor("#176c59"))
        painter.drawEllipse(
            body[0] - 20,
            body[1] - 15,
            40,
            30,
        )

        # Forward direction indicator
        nose = project(0, -38, 0)

        painter.setPen(QPen(QColor("#ffcc66"), 3))
        painter.drawLine(body[0], body[1], nose[0], nose[1])

        painter.setPen(QColor("#dce3ea"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(15, 25, "BEE-BRAIN | 3D DRONE VIEW")

        painter.setPen(QColor("#9ba6b5"))
        painter.drawText(
            15,
            height - 18,
            f"ROLL {self.roll:.1f}°  "
            f"PITCH {self.pitch:.1f}°  "
            f"YAW {self.yaw:.1f}°",
        )

        painter.end()


class DroneViewPanel(QWidget):
    """Drone visualization, manual orientation controls and demo animation."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.demo_running = False
        self.demo_time = 0.0

        self.demo_timer = QTimer(self)
        self.demo_timer.setInterval(50)
        self.demo_timer.timeout.connect(self.update_demo)

        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        # Heading
        heading = QLabel("3D DRONE VIEW")
        heading.setStyleSheet(
            "font-size: 23px; font-weight: bold; color: #eeeeee;"
        )
        root.addWidget(heading)

        subtitle = QLabel(
            "Visual orientation preview and telemetry monitor"
        )
        subtitle.setStyleSheet("color: #929aa5; font-size: 12px;")
        root.addWidget(subtitle)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)

        self.canvas = DroneCanvas()
        content.addWidget(self.canvas, 3)

        # Right-side controls
        controls_frame = QFrame()
        controls_frame.setMinimumWidth(225)
        controls_frame.setMaximumWidth(300)
        controls_frame.setStyleSheet(
            "QFrame { background-color: #202328; "
            "border: 1px solid #343941; border-radius: 8px; }"
        )

        controls = QVBoxLayout(controls_frame)
        controls.setContentsMargins(16, 16, 16, 16)
        controls.setSpacing(12)

        controls_title = QLabel("ORIENTATION")
        controls_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #eeeeee;"
            "border: none;"
        )
        controls.addWidget(controls_title)

        self.roll_label = QLabel("Roll: 0°")
        self.pitch_label = QLabel("Pitch: 0°")
        self.yaw_label = QLabel("Yaw: 0°")

        self.roll_slider = self.create_slider(-45, 45)
        self.pitch_slider = self.create_slider(-45, 45)
        self.yaw_slider = self.create_slider(-180, 180)

        for label, slider in (
            (self.roll_label, self.roll_slider),
            (self.pitch_label, self.pitch_slider),
            (self.yaw_label, self.yaw_slider),
        ):
            label.setStyleSheet("color: #cbd2dc; border: none;")
            controls.addWidget(label)
            controls.addWidget(slider)

        self.roll_slider.valueChanged.connect(self.update_orientation)
        self.pitch_slider.valueChanged.connect(self.update_orientation)
        self.yaw_slider.valueChanged.connect(self.update_orientation)

        self.demo_button = QPushButton("START DEMO")
        self.reset_button = QPushButton("RESET ORIENTATION")

        self.demo_button.clicked.connect(self.toggle_demo)
        self.reset_button.clicked.connect(self.reset_orientation)

        for button in (self.demo_button, self.reset_button):
            button.setMinimumHeight(36)
            button.setStyleSheet(
                "QPushButton { background-color: #30363e; "
                "border: 1px solid #454d57; border-radius: 5px; "
                "padding: 6px; color: #eeeeee; }"
                "QPushButton:hover { background-color: #3b444d; }"
            )

        controls.addSpacing(8)
        controls.addWidget(self.demo_button)
        controls.addWidget(self.reset_button)
        controls.addStretch()

        content.addWidget(controls_frame, 1)
        root.addLayout(content, 1)

        # Telemetry cards
        metrics = QGridLayout()
        metrics.setSpacing(12)

        self.altitude_value = self.create_metric(
            metrics, 0, "ALTITUDE", "-- cm"
        )
        self.drift_x_value = self.create_metric(
            metrics, 1, "DRIFT X", "--"
        )
        self.drift_y_value = self.create_metric(
            metrics, 2, "DRIFT Y", "--"
        )
        self.battery_value = self.create_metric(
            metrics, 3, "BATTERY", "-- V"
        )

        root.addLayout(metrics)

    def create_slider(self, minimum, maximum):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(0)
        slider.setStyleSheet(
            "QSlider::groove:horizontal { height: 5px; "
            "background: #3b424b; border-radius: 2px; }"
            "QSlider::handle:horizontal { background: #00b894; "
            "width: 13px; margin: -5px 0; border-radius: 6px; }"
        )
        return slider

    def create_metric(self, layout, column, title, initial_value):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #202328; "
            "border: 1px solid #343941; border-radius: 7px; }"
        )

        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: #929aa5; font-size: 10px; border: none;"
        )

        value_label = QLabel(initial_value)
        value_label.setStyleSheet(
            "color: #00d6a5; font-size: 19px; "
            "font-weight: bold; border: none;"
        )

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        layout.addWidget(frame, 0, column)

        return value_label

    def update_orientation(self, value=None):
        roll = self.roll_slider.value()
        pitch = self.pitch_slider.value()
        yaw = self.yaw_slider.value()

        self.roll_label.setText(f"Roll: {roll}°")
        self.pitch_label.setText(f"Pitch: {pitch}°")
        self.yaw_label.setText(f"Yaw: {yaw}°")

        self.canvas.set_orientation(roll, pitch, yaw)

    def toggle_demo(self):
        self.demo_running = not self.demo_running

        if self.demo_running:
            self.demo_button.setText("STOP DEMO")
            self.demo_timer.start()
        else:
            self.demo_button.setText("START DEMO")
            self.demo_timer.stop()

    def update_demo(self):
        self.demo_time += 0.05

        self.roll_slider.setValue(
            int(20 * math.sin(self.demo_time * 1.2))
        )
        self.pitch_slider.setValue(
            int(15 * math.sin(self.demo_time * 0.8))
        )
        self.yaw_slider.setValue(
            int(40 * math.sin(self.demo_time * 0.4))
        )

    def reset_orientation(self):
        self.demo_timer.stop()
        self.demo_running = False
        self.demo_button.setText("START DEMO")
        self.demo_time = 0.0

        self.roll_slider.setValue(0)
        self.pitch_slider.setValue(0)
        self.yaw_slider.setValue(0)

        self.update_orientation()

    def update_telemetry(self, packet):
        """Update the metric cards from the existing telemetry packet."""
        try:
            self.altitude_value.setText(
                f"{float(packet.altitude_cm):.1f} cm"
            )
            self.drift_x_value.setText(
                f"{float(packet.drift_x):.2f}"
            )
            self.drift_y_value.setText(
                f"{float(packet.drift_y):.2f}"
            )
            self.battery_value.setText(
                f"{float(packet.battery_v):.2f} V"
            )
        except (AttributeError, TypeError, ValueError):
            # Keep the last valid readings if a packet is incomplete.
            pass
