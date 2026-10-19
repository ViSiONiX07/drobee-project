
import math

from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QSlider, QCheckBox, QSizePolicy,
)

BG = "#191c18"
PANEL = "#252923"
PANEL_DARK = "#111410"
BORDER = "#3b4035"
TEXT = "#e7e5dc"
MUTED = "#96988a"
COPPER = "#e99048"
AMBER = "#efbf59"
MINT = "#9bcbb3"


class DroneCanvas(QWidget):
    """QPainter-based drone visualization; not a physical 3D engine."""

    CAMERA_MODES = ("ISO 3D", "TOP (Z)", "FRONT (X)", "SIDE (Y)")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.throttle = 100.0
        self.camera_mode = "ISO 3D"
        self.show_propellers = True
        self.show_thrust_vectors = True
        self.show_clearance = True
        self.show_grid = True
        self.demo_phase = 0.0
        self.setMinimumSize(320, 300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def set_orientation(self, roll, pitch, yaw):
        self.roll = float(roll)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.update()

    def set_camera_mode(self, mode):
        if mode in self.CAMERA_MODES:
            self.camera_mode = mode
            self.update()

    def set_throttle(self, value):
        self.throttle = max(0.0, min(200.0, float(value)))
        self.update()

    def set_layers(self, propellers=None, thrust=None,
                   clearance=None, grid=None):
        if propellers is not None:
            self.show_propellers = bool(propellers)
        if thrust is not None:
            self.show_thrust_vectors = bool(thrust)
        if clearance is not None:
            self.show_clearance = bool(clearance)
        if grid is not None:
            self.show_grid = bool(grid)
        self.update()

    def set_demo_phase(self, phase):
        self.demo_phase = float(phase)
        self.update()

    def _rotate(self, x, y, z):
        r = math.radians(self.roll)
        p = math.radians(self.pitch)
        ya = math.radians(self.yaw)

        y1 = y * math.cos(r) - z * math.sin(r)
        z1 = y * math.sin(r) + z * math.cos(r)
        x2 = x * math.cos(p) + z1 * math.sin(p)
        z2 = -x * math.sin(p) + z1 * math.cos(p)
        x3 = x2 * math.cos(ya) - y1 * math.sin(ya)
        y3 = x2 * math.sin(ya) + y1 * math.cos(ya)
        return x3, y3, z2

    def _screen(self, point, cx, cy, scale):
        x, y, z = self._rotate(*point)

        if self.camera_mode == "TOP (Z)":
            sx, sy, depth = x, -y, z
        elif self.camera_mode == "FRONT (X)":
            sx, sy, depth = y, -z, x
        elif self.camera_mode == "SIDE (Y)":
            sx, sy, depth = x, -z, y
        else:
            sx = (x - y) * 0.707
            sy = (x + y) * 0.30 - z * 0.90
            depth = x + y + z

        perspective = max(0.65, min(1.25, 1 + depth / 1600))
        return QPointF(
            cx + sx * scale * perspective,
            cy + sy * scale * perspective,
        )

    def _text(self, painter, x, y, text, color=MUTED,
              size=9, bold=False):
        painter.setPen(QColor(color))
        painter.setFont(QFont(
            "Consolas", size,
            QFont.Weight.Bold if bold else QFont.Weight.Normal,
        ))
        painter.drawText(int(x), int(y), str(text))

    def _line(self, painter, a, b, color, width=1,
              style=Qt.PenStyle.SolidLine):
        painter.setPen(QPen(
            QColor(color), width, style, Qt.PenCapStyle.RoundCap
        ))
        painter.drawLine(a, b)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PANEL_DARK))

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        scale = max(0.50, min(w / 760.0, h / 570.0))

        if self.show_grid:
            spacing = max(12, int(35 * scale))
            painter.setPen(QPen(QColor("#22271f"), 1))
            for x in range(0, w, spacing):
                painter.drawLine(x, 0, x, h)
            for y in range(0, h, spacing):
                painter.drawLine(0, y, w, y)

        arm = 105.0
        motors = [
            (-arm, -arm, 0), (arm, -arm, 0),
            (-arm, arm, 0), (arm, arm, 0),
        ]
        names = ["M1 FR CW", "M2 RR CCW", "M3 RL CW", "M4 FL CCW"]
        motor_points = [self._screen(p, cx, cy, scale) for p in motors]
        body = self._screen((0, 0, 0), cx, cy, scale)

        if self.show_clearance:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(
                QColor("#755a32"), 1, Qt.PenStyle.DashLine
            ))
            for point in motor_points:
                painter.drawEllipse(point, 44 * scale, 44 * scale)

        chassis = [
            (-30, -72, 0), (30, -72, 0),
            (30, 72, 0), (-30, 72, 0),
        ]
        painter.setPen(QPen(QColor("#656c5c"), 2))
        painter.setBrush(QBrush(QColor("#242a21")))
        painter.drawPolygon(QPolygonF([
            self._screen(p, cx, cy, scale) for p in chassis
        ]))

        for i, point in enumerate(motor_points):
            self._line(
                painter, body, point, "#4a5145",
                max(4, int(12 * scale)),
            )
            self._line(painter, body, point, "#78816e", 2)

            painter.setPen(QPen(QColor(COPPER), 2))
            painter.setBrush(QBrush(QColor("#393b2d")))
            painter.drawEllipse(point, 6 * scale, 6 * scale)
            painter.setBrush(QBrush(QColor(COPPER)))
            painter.drawEllipse(point, 2 * scale, 2 * scale)

            if self.show_propellers:
                painter.save()
                painter.translate(point)
                painter.rotate(self.yaw + self.demo_phase * 80)
                painter.setPen(QPen(QColor("#8cb9a4"), 1))
                painter.setBrush(QBrush(QColor("#83ad99")))
                painter.drawEllipse(
                    QPointF(0, 0), 31 * scale, 7 * scale
                )
                painter.restore()

            if self.show_thrust_vectors and self.throttle > 0:
                length = (12 + self.throttle / 200 * 30) * scale
                top = QPointF(point.x(), point.y() - length)
                self._line(painter, point, top, COPPER, 2)

            self._text(
                painter, point.x() - 34 * scale,
                point.y() + 29 * scale, names[i], AMBER, 7, True,
            )

        painter.setPen(QPen(QColor("#343b2f"), 1))
        painter.setBrush(QBrush(QColor("#303528")))
        painter.drawRoundedRect(
            cx - 18 * scale, cy - 25 * scale,
            36 * scale, 50 * scale, 3, 3,
        )
        self._text(
            painter, cx - 12 * scale, cy + 4 * scale,
            "BEE", COPPER, 8, True,
        )

        nose = self._screen((0, -76, 0), cx, cy, scale)
        self._line(painter, body, nose, COPPER, 2)

        axes = [
            ((0, -180, 0), "+X FWD", MINT),
            ((-180, 0, 0), "-Y PORT", AMBER),
            ((180, 0, 0), "+Y STBD", AMBER),
            ((0, 180, 0), "-X AFT", MUTED),
        ]
        for point, label, color in axes:
            pos = self._screen(point, cx, cy, scale)
            self._text(painter, pos.x() - 25, pos.y(), label, color, 7, True)

        self._draw_horizon(painter)
        self._text(
            painter, 14, 20,
            f"CAMERA: {self.camera_mode} | VISUAL MODEL",
            MUTED, 9, True,
        )
        self._text(
            painter, 14, 37,
            f"ROLL {self.roll:+.1f}°  "
            f"PITCH {self.pitch:+.1f}°  YAW {self.yaw:.1f}°",
            COPPER, 9, True,
        )

        box_x = max(10, w - 195)
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#1c201a")))
        painter.drawRoundedRect(
            box_x, max(10, h - 48), 180, 36, 4, 4
        )
        self._text(
            painter, box_x + 9, h - 28,
            "● VISUAL SIMULATION", MINT, 8, True,
        )
        self._text(
            painter, box_x + 9, h - 15,
            "QPainter projection", MUTED, 8,
        )
        painter.end()

    def _draw_horizon(self, painter):
        x, y, width, height = 14, self.height() - 125, 165, 108
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#171a15")))
        painter.drawRoundedRect(x, y, width, height, 4, 4)

        self._text(painter, x + 8, y + 14, "ADI-HORIZON", MUTED, 8, True)
        self._text(
            painter, x + width - 44, y + 14,
            f"{self.roll:+.1f}°", MINT, 8, True,
        )

        cx, cy = x + width / 2, y + 64
        self._line(
            painter, QPointF(cx - 54, cy),
            QPointF(cx + 54, cy), AMBER, 2,
        )
        self._line(
            painter, QPointF(cx, cy - 26),
            QPointF(cx, cy + 26), "#485044", 1,
        )
        painter.setPen(QPen(QColor(COPPER), 1))
        painter.setBrush(QBrush(QColor("#171a15")))
        painter.drawEllipse(QPointF(cx, cy), 17, 17)
        painter.setBrush(QBrush(QColor(COPPER)))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)


class DroneViewPanel(QWidget):
    """Drone geometry test bench with visual-only controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.demo_running = False
        self.demo_time = 0.0
        self.telemetry_packet = None

        self.demo_timer = QTimer(self)
        self.demo_timer.setInterval(40)
        self.demo_timer.timeout.connect(self.update_demo)

        self.build_ui()
        self.update_orientation()

    def card(self):
        frame = QFrame()
        frame.setObjectName("Card")
        return frame

    def section_heading(self, text, tag=None, tag_color=MINT):
        """Return a QWidget so layout.addWidget() receives a widget."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            "font-size:11px; font-weight:bold; color:#e7e5dc;"
        )
        row.addWidget(label, 1)

        if tag:
            badge = QLabel(tag)
            badge.setWordWrap(True)
            badge.setStyleSheet(
                f"color:{tag_color}; background:#171a15;"
                "border:1px solid #3b4035; border-radius:3px;"
                "padding:3px 5px; font-family:Consolas; font-size:8px;"
            )
            row.addWidget(badge)

        return container

    def build_ui(self):
        self.setObjectName("DroneViewPanel")
        self.setStyleSheet("""
            QWidget#DroneViewPanel {
                background:#191c18; color:#e7e5dc;
                font-family:'Segoe UI',Arial;
            }
            QLabel { background:transparent; border:none; color:#e7e5dc; }
            QFrame#Card {
                background:#252923; border:1px solid #3b4035;
                border-radius:5px;
            }
            QPushButton {
                background:#30352d; color:#e7e5dc;
                border:1px solid #484d40; border-radius:4px;
                padding:7px; font-size:10px; font-weight:600;
            }
            QPushButton:hover { background:#414538; border-color:#e99048; }
            QCheckBox { spacing:8px; color:#c6c6b9; font-size:10px; }
            QSlider::groove:horizontal {
                height:5px; background:#3c4037; border-radius:2px;
            }
            QSlider::handle:horizontal {
                background:#e99048; border:1px solid #ffc58f;
                width:13px; margin:-5px 0; border-radius:7px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        root.addWidget(self.build_header())

        content = QHBoxLayout()
        content.setSpacing(8)

        # IMPORTANT: create the canvas BEFORE building camera controls.
        # build_camera_card() calls set_camera_mode(), which uses self.canvas.
        self.canvas = DroneCanvas()
        self.canvas.setStyleSheet(
            "border:1px solid #3b4035; border-radius:4px;"
        )

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(self.build_camera_card())
        left.addWidget(self.build_attitude_card())
        left.addWidget(self.build_motor_card())
        left.addWidget(self.build_layers_card())
        left.addStretch()
        left.addWidget(self.build_left_actions())

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(self.build_override_card())
        right.addWidget(self.build_step_card())
        right.addWidget(self.build_geometry_card())
        right.addStretch()

        content.addLayout(left, 25)
        content.addWidget(self.canvas, 50)
        content.addLayout(right, 25)
        root.addLayout(content, 1)

    def build_header(self):
        frame = self.card()
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)

        brand = QLabel("BB")
        brand.setStyleSheet(
            "color:#e99048; border:1px solid #805b3b;"
            "border-radius:3px; padding:6px; font-weight:bold;"
        )
        row.addWidget(brand)

        title_col = QVBoxLayout()
        title = QLabel("BEE-BRAIN GCS")
        title.setStyleSheet("font-size:13px; font-weight:bold;")
        subtitle = QLabel(
            "FRAME GEOMETRY & PROPELLER DYNAMICS TEST BENCH"
        )
        subtitle.setStyleSheet(
            "color:#96988a; font-family:Consolas; font-size:8px;"
        )
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        row.addLayout(title_col, 1)

        self.link_badge = QLabel("● VISUAL SIMULATION")
        self.link_badge.setStyleSheet(
            "color:#9bcbb3; font-family:Consolas; font-size:9px;"
        )
        row.addWidget(self.link_badge)

        self.battery_badge = QLabel("BATT: -- V")
        self.battery_badge.setStyleSheet(
            "color:#efbf59; font-family:Consolas; font-size:9px;"
        )
        row.addWidget(self.battery_badge)

        self.bench_badge = QLabel("TEST BENCH ACTIVE")
        self.bench_badge.setStyleSheet(
            "color:#e99048; border:1px solid #765338;"
            "border-radius:3px; padding:6px; font-size:9px;"
        )
        row.addWidget(self.bench_badge)
        return frame

    def build_camera_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(self.section_heading("CAMERA PERSPECTIVE"))

        grid = QGridLayout()
        grid.setSpacing(5)
        self.camera_buttons = {}

        for index, mode in enumerate(DroneCanvas.CAMERA_MODES):
            button = QPushButton(mode)
            button.clicked.connect(
                lambda checked=False, selected=mode:
                self.set_camera_mode(selected)
            )
            self.camera_buttons[mode] = button
            grid.addWidget(button, index // 2, index % 2)

        layout.addLayout(grid)
        # self.canvas already exists before this method is called.
        self.set_camera_mode("ISO 3D")
        return frame

    def build_attitude_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(
            self.section_heading("ATTITUDE STATE", "LIVE OVERRIDE", MINT)
        )

        grid = QGridLayout()
        grid.setSpacing(5)
        self.roll_value = self.metric_tile(
            grid, 0, "ROLL (φ)", "+0.0°", MINT
        )
        self.pitch_value = self.metric_tile(
            grid, 1, "PITCH (θ)", "+0.0°", AMBER
        )
        self.yaw_value = self.metric_tile(
            grid, 2, "YAW (ψ)", "0.0°", COPPER
        )
        layout.addLayout(grid)
        return frame

    def metric_tile(self, layout, column, title, initial, color):
        frame = self.card()
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(7, 7, 7, 7)
        inner.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color:#96988a; font-family:Consolas; font-size:8px;"
        )
        value_label = QLabel(initial)
        value_label.setStyleSheet(
            f"color:{color}; font-family:Consolas;"
            "font-size:14px; font-weight:bold;"
        )
        inner.addWidget(title_label)
        inner.addWidget(value_label)
        layout.addWidget(frame, 0, column)
        return value_label

    def build_motor_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(
            self.section_heading("MOTOR MOUNTS", "ILLUSTRATIVE", MINT)
        )

        mounts = [
            ("M1 (FR CW)", "(+145, -112)", "1,580 µs"),
            ("M2 (RR CCW)", "(+162, +128)", "1,605 µs"),
            ("M3 (RL CW)", "(-162, +128)", "1,590 µs"),
            ("M4 (FL CCW)", "(-145, -112)", "1,575 µs"),
        ]
        self.motor_mount_labels = []

        for name, coordinates, pulse in mounts:
            item = QFrame()
            item.setStyleSheet(
                "background:#191c18; border:1px solid #30352b;"
                "border-radius:3px;"
            )
            row = QHBoxLayout(item)
            row.setContentsMargins(5, 5, 5, 5)
            row.setSpacing(3)

            name_label = QLabel(name)
            name_label.setStyleSheet(
                "font-family:Consolas; font-size:8px;"
            )
            coord_label = QLabel(coordinates)
            coord_label.setStyleSheet(
                "color:#efbf59; font-family:Consolas; font-size:8px;"
            )
            pulse_label = QLabel(pulse)
            pulse_label.setStyleSheet(
                "color:#9bcbb3; font-family:Consolas; font-size:8px;"
            )
            row.addWidget(name_label, 1)
            row.addWidget(coord_label)
            row.addWidget(pulse_label)
            layout.addWidget(item)
            self.motor_mount_labels.append(pulse_label)

        note = QLabel(
            "Illustrative values, not sensor measurements or verified CAD."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#96988a; font-size:8px;")
        layout.addWidget(note)
        return frame

    def build_layers_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(self.section_heading("LAYER VISUALIZERS"))

        self.propellers_check = QCheckBox("Show Propellers")
        self.thrust_check = QCheckBox("Show Thrust Vectors")
        self.clearance_check = QCheckBox("Show Clearance Circles")
        self.grid_check = QCheckBox("Show Grid")

        for checkbox in (
            self.propellers_check,
            self.thrust_check,
            self.clearance_check,
            self.grid_check,
        ):
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            checkbox.stateChanged.connect(self.update_layers)

        return frame

    def build_left_actions(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        reset = QPushButton("RESET TO ZERO (LEVEL)")
        reset.clicked.connect(self.reset_orientation)
        layout.addWidget(reset)

        self.demo_button = QPushButton("START GIMBAL SWEEP")
        self.demo_button.clicked.connect(self.toggle_demo)
        layout.addWidget(self.demo_button)
        return widget

    def build_override_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(8)
        layout.addWidget(
            self.section_heading("TEST BENCH HARNESS", "SIMULATION", COPPER)
        )

        description = QLabel(
            "Adjust the displayed attitude and visual throttle. "
            "No physical motor commands are sent."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color:#96988a; font-size:9px;")
        layout.addWidget(description)

        self.roll_slider, self.roll_override_value = self.add_override(
            layout, "Roll (φ)", -45, 45, 0,
            "-45°", "0°", "+45°"
        )
        self.pitch_slider, self.pitch_override_value = self.add_override(
            layout, "Pitch (θ)", -45, 45, 0,
            "-45°", "0°", "+45°"
        )
        self.yaw_slider, self.yaw_override_value = self.add_override(
            layout, "Yaw (ψ)", 0, 360, 0,
            "0°", "180°", "360°"
        )
        self.throttle_slider, self.throttle_override_value = self.add_override(
            layout, "Visual Throttle", 0, 200, 100,
            "0%", "100%", "200%"
        )

        self.roll_slider.valueChanged.connect(self.update_orientation)
        self.pitch_slider.valueChanged.connect(self.update_orientation)
        self.yaw_slider.valueChanged.connect(self.update_orientation)
        self.throttle_slider.valueChanged.connect(self.update_throttle)
        return frame

    def add_override(self, parent_layout, title, minimum, maximum,
                     initial, left_text, center_text, right_text):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(5)

        row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:9px; font-weight:bold;")
        value_label = QLabel(str(initial))
        value_label.setStyleSheet(
            "color:#e99048; font-family:Consolas; font-size:10px;"
        )
        row.addWidget(title_label, 1)
        row.addWidget(value_label)
        layout.addLayout(row)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(initial)
        layout.addWidget(slider)

        labels = QHBoxLayout()
        for text in (left_text, center_text, right_text):
            label = QLabel(text)
            label.setStyleSheet(
                "color:#96988a; font-family:Consolas; font-size:8px;"
            )
            labels.addWidget(label, 1)
        layout.addLayout(labels)

        parent_layout.addWidget(frame)
        return slider, value_label

    def build_step_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(self.section_heading("STEP RESPONSE"))

        row = QHBoxLayout()
        roll_button = QPushButton("+15° ROLL")
        pitch_button = QPushButton("+15° PITCH")
        roll_button.clicked.connect(lambda: self.apply_step("roll"))
        pitch_button.clicked.connect(lambda: self.apply_step("pitch"))
        row.addWidget(roll_button)
        row.addWidget(pitch_button)
        layout.addLayout(row)
        return frame

    def build_geometry_card(self):
        frame = self.card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)
        layout.addWidget(self.section_heading("GEOMETRY CHECKS"))

        for text in (
            "✓ Four motor hubs",
            "✓ Propeller placement",
            "✓ Attitude projection",
            "✓ Multiple camera projections",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(
                "color:#9bcbb3; font-family:Consolas; font-size:9px;"
            )
            layout.addWidget(label)

        note = QLabel(
            "Visual geometry only; not verified CAD or hardware dimensions."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#96988a; font-size:8px;")
        layout.addWidget(note)
        return frame

    def set_camera_mode(self, mode):
        self.canvas.set_camera_mode(mode)

        for name, button in self.camera_buttons.items():
            active = name == mode
            button.setStyleSheet(
                "QPushButton {"
                f"background:{'#e99048' if active else '#30352d'};"
                f"color:{'#191c18' if active else '#e7e5dc'};"
                f"border:1px solid {'#ffc58f' if active else '#484d40'};"
                "border-radius:4px; padding:7px; font-size:9px;"
                "font-weight:bold;}"
            )

    def update_layers(self, *args):
        self.canvas.set_layers(
            propellers=self.propellers_check.isChecked(),
            thrust=self.thrust_check.isChecked(),
            clearance=self.clearance_check.isChecked(),
            grid=self.grid_check.isChecked(),
        )

    def update_orientation(self, value=None):
        self.roll = float(self.roll_slider.value())
        self.pitch = float(self.pitch_slider.value())
        self.yaw = float(self.yaw_slider.value())

        self.roll_override_value.setText(f"{self.roll:+.1f}°")
        self.pitch_override_value.setText(f"{self.pitch:+.1f}°")
        self.yaw_override_value.setText(f"{self.yaw:.1f}°")

        self.roll_value.setText(f"{self.roll:+.1f}°")
        self.pitch_value.setText(f"{self.pitch:+.1f}°")
        self.yaw_value.setText(f"{self.yaw:.1f}°")

        self.canvas.set_orientation(self.roll, self.pitch, self.yaw)

    def update_throttle(self, value):
        self.throttle_override_value.setText(f"{value}%")
        self.canvas.set_throttle(value)

    def apply_step(self, axis):
        if axis == "roll":
            self.roll_slider.setValue(
                min(45, self.roll_slider.value() + 15)
            )
        else:
            self.pitch_slider.setValue(
                min(45, self.pitch_slider.value() + 15)
            )

    def toggle_demo(self):
        self.demo_running = not self.demo_running

        if self.demo_running:
            self.demo_button.setText("STOP GIMBAL SWEEP")
            self.demo_timer.start()
        else:
            self.demo_button.setText("START GIMBAL SWEEP")
            self.demo_timer.stop()

    def update_demo(self):
        self.demo_time += 0.04
        self.roll_slider.setValue(
            int(20 * math.sin(self.demo_time * 1.2))
        )
        self.pitch_slider.setValue(
            int(15 * math.sin(self.demo_time * 0.8))
        )
        self.yaw_slider.setValue(
            int((self.demo_time * 25) % 360)
        )
        self.canvas.set_demo_phase(self.demo_time)

    def reset_orientation(self):
        self.demo_timer.stop()
        self.demo_running = False
        self.demo_time = 0.0
        self.demo_button.setText("START GIMBAL SWEEP")

        self.roll_slider.setValue(0)
        self.pitch_slider.setValue(0)
        self.yaw_slider.setValue(0)
        self.throttle_slider.setValue(100)

        self.update_orientation()
        self.update_throttle(100)
        self.canvas.set_demo_phase(0.0)

    def update_telemetry(self, packet):
        """Update battery display from a compatible telemetry packet."""
        self.telemetry_packet = packet
        try:
            self.battery_badge.setText(
                f"BATT: {float(packet.battery_v):.2f} V"
            )
        except (AttributeError, TypeError, ValueError):
            pass
