
import math
import random
import time

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QSlider, QSizePolicy, QFileDialog,
    QComboBox, QPlainTextEdit, QProgressBar,
)


# ============================================================
# Theme
# ============================================================

BG = "#111411"
PANEL = "#1b1f1b"
PANEL_DARK = "#151815"
PANEL_LIGHT = "#252a25"
BORDER = "#303630"
COPPER = "#f29a50"
COPPER_LIGHT = "#ffb879"
MINT = "#a8d6c1"
MINT_DARK = "#739b87"
AMBER = "#e9c16a"
TEXT = "#e6e7df"
MUTED = "#a19b8e"
RED = "#df7669"


def mono(size=9, bold=False):
    """Return a Consolas font with size in points and optional bold weight."""
    return QFont("Consolas", size, QFont.Bold if bold else QFont.Normal)


def ui_font(size=9, bold=False):
    """Return an Arial font with size in points and optional bold weight."""
    return QFont("Arial", size, QFont.Bold if bold else QFont.Normal)


def make_label(text, color=TEXT, size=9, bold=False, monospace=False):
    """Return a colored label using the requested point size and font family."""
    label = QLabel(text)
    label.setFont(mono(size, bold) if monospace else ui_font(size, bold))
    label.setStyleSheet(f"color:{color}; background:transparent;")
    return label


def make_button(text, primary=False):
    """Return a styled action button, with copper emphasis when primary is true."""
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setMinimumHeight(31)
    button.setFont(ui_font(9, True))

    if primary:
        button.setStyleSheet(f"""
            QPushButton {{
                background:{COPPER}; color:#171914;
                border:1px solid {COPPER_LIGHT};
                border-radius:4px; padding:6px 9px; font-weight:bold;
            }}
            QPushButton:hover {{ background:{COPPER_LIGHT}; }}
            QPushButton:pressed {{ background:#d67e36; }}
        """)
    else:
        button.setStyleSheet(f"""
            QPushButton {{
                background:{PANEL_LIGHT}; color:{TEXT};
                border:1px solid {BORDER};
                border-radius:4px; padding:5px 8px;
            }}
            QPushButton:hover {{
                background:#30372f; border-color:{MINT_DARK};
            }}
            QPushButton:pressed {{ background:#101310; }}
        """)
    return button


def make_section(title, tag=None):
    """Return a section frame and its vertical layout with an optional header tag."""
    frame = QFrame()
    frame.setObjectName("mapSection")
    frame.setStyleSheet(f"""
        QFrame#mapSection {{
            background:{PANEL}; border:1px solid {BORDER};
            border-radius:5px;
        }}
    """)

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(11, 10, 11, 11)
    layout.setSpacing(9)

    # The heading row is a layout added directly to the section layout.
    # Do not attempt to retrieve a nested layout from its heading label.
    header = QHBoxLayout()
    heading = make_label(title, TEXT, 10, True)
    heading.setWordWrap(True)
    header.addWidget(heading, 1)

    if tag:
        badge = make_label(tag, MINT, 8, True, True)
        badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(badge)

    layout.addLayout(header)
    return frame, layout


def make_metric_card(title, value, detail="", value_color=TEXT):
    """Return a metric card, its value label, and its detail label."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background:{PANEL_LIGHT}; border:1px solid #292e28;
            border-radius:3px;
        }}
    """)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(7, 7, 7, 7)
    layout.setSpacing(4)

    title_label = make_label(title, MUTED, 8, False, True)
    title_label.setWordWrap(True)
    layout.addWidget(title_label)

    value_label = make_label(value, value_color, 11, True, True)
    value_label.setWordWrap(True)
    layout.addWidget(value_label)

    detail_label = make_label(detail, MINT, 8, False, True)
    detail_label.setWordWrap(True)
    layout.addWidget(detail_label)

    return card, value_label, detail_label


# ============================================================
# Interactive 3D-style point cloud
# ============================================================

class PointCloudView(QWidget):
    """Painted point-cloud viewport with camera, zoom and orbit controls."""

    def __init__(self, parent=None):
        """Initialize an isometric viewport with a demo cloud and trail."""
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.camera_mode = "Isometric"
        self.show_trail = True
        self.show_grid = True
        self.show_axes = True
        self.yaw = 0.0
        self.zoom = 1.0
        self.dragging = False
        self.last_mouse = None
        self.points = []
        self.path = []
        self.demo_mode = True

        self._generate_demo_points()

    def _generate_demo_points(self):
        """Replace the cloud and path with repeatable demo data and request repaint."""
        rng = random.Random(42)
        points = []

        # Demonstration floor samples.
        for _ in range(650):
            points.append((
                rng.uniform(-2, 2),
                rng.uniform(-2, 2),
                rng.uniform(-0.015, 0.015),
                "floor",
            ))

        # Demonstration wall samples.
        for _ in range(230):
            x = rng.uniform(-2, 2)
            y = rng.uniform(-2, 2)
            z = rng.uniform(0, 2.1)

            if rng.random() > 0.5:
                x = rng.choice([-2.0, 2.0]) + rng.uniform(-0.025, 0.025)
            else:
                y = rng.choice([-2.0, 2.0]) + rng.uniform(-0.025, 0.025)

            points.append((x, y, z, "wall"))

        # Demonstration object clusters.
        for cx, cy, cz in [
            (-1.1, -0.8, 0.55),
            (1.1, 0.7, 0.75),
            (0.6, -1.0, 0.35),
        ]:
            for _ in range(75):
                points.append((
                    rng.gauss(cx, 0.12),
                    rng.gauss(cy, 0.12),
                    max(0.02, rng.gauss(cz, 0.18)),
                    "object",
                ))

        self.points = points
        self.path = [
            (
                0.95 * math.cos(i * 2 * math.pi / 100),
                0.80 * math.sin(i * 2 * math.pi / 100),
                0.15 + 0.04 * math.sin(i / 7),
            )
            for i in range(101)
        ]
        self.demo_mode = True
        self.update()

    def set_points(self, points):
        """Replace the cloud with XYZ points and leave demo mode.

        Accept [(x, y, z), ...] or [(x, y, z, category), ...].
        Each point supplies x, y, z and an optional category, defaulting to
        "sensor". Entries shorter than three items are skipped; extra items
        beyond the category are ignored. Coordinates are converted to floats;
        TypeError, ValueError, or OverflowError from conversion propagate.
        The existing trail is retained.
        """
        converted = []
        for point in points:
            if len(point) >= 3:
                category = str(point[3]) if len(point) >= 4 else "sensor"
                converted.append((
                    float(point[0]),
                    float(point[1]),
                    float(point[2]),
                    category,
                ))

        self.points = converted
        self.demo_mode = False
        self.update()

    def set_camera_mode(self, mode):
        """Set the camera projection and request repaint.

        Modes are "Isometric", "Top (Z)", "Side (X)", and "First-Person";
        unknown names use the isometric projection.
        """
        self.camera_mode = mode
        self.update()

    def set_trail_visible(self, visible):
        """Set trail visibility and request repaint."""
        self.show_trail = visible
        self.update()

    def reset_view(self):
        """Restore zero orbit yaw, unit zoom, and the isometric projection."""
        self.yaw = 0.0
        self.zoom = 1.0
        self.camera_mode = "Isometric"
        self.update()

    def _project(self, x, y, z):
        """Return pixel coordinates after applying orbit, zoom, and projection."""
        width = max(1, self.width())
        height = max(1, self.height())
        cx, cy = width * 0.50, height * 0.55
        scale = min(width, height) * 0.22 * self.zoom

        rx = x * math.cos(self.yaw) - y * math.sin(self.yaw)
        ry = x * math.sin(self.yaw) + y * math.cos(self.yaw)

        if self.camera_mode == "Top (Z)":
            sx, sy = cx + rx * scale, cy + ry * scale
        elif self.camera_mode == "Side (X)":
            sx, sy = cx + ry * scale, cy - z * scale
        elif self.camera_mode == "First-Person":
            sx = cx + rx * scale * 1.15
            sy = cy - z * scale + ry * scale * 0.30
        else:
            sx = cx + (rx - ry) * scale * 0.72
            sy = cy + (rx + ry) * scale * 0.35 - z * scale

        return QPointF(sx, sy)

    def _line3d(self, painter, a, b, color, width=1, style=Qt.SolidLine):
        """Draw a styled line between projected XYZ endpoints using painter."""
        painter.setPen(QPen(QColor(color), width, style))
        painter.drawLine(self._project(*a), self._project(*b))

    def _draw_room(self, painter):
        """Draw the illustrative room outline on the supplied painter."""
        extent = 2.0
        floor = [
            (-extent, -extent, 0),
            (extent, -extent, 0),
            (extent, extent, 0),
            (-extent, extent, 0),
        ]
        roof = [(x, y, 2.5) for x, y, _ in floor]

        for i in range(4):
            self._line3d(
                painter, floor[i], floor[(i + 1) % 4], "#3a4037"
            )
            self._line3d(
                painter, roof[i], roof[(i + 1) % 4], "#242a23"
            )
            self._line3d(painter, floor[i], roof[i], "#252b24")

    def _draw_grid(self, painter):
        """Draw the projected ground grid on the supplied painter."""
        value = -2.0
        while value <= 2.001:
            self._line3d(
                painter, (value, -2, 0), (value, 2, 0), "#222720"
            )
            self._line3d(
                painter, (-2, value, 0), (2, value, 0), "#222720"
            )
            value += 0.25

    def _draw_axes(self, painter):
        """Draw labeled XYZ reference axes on the supplied painter."""
        axes = [
            ((0.85, 0, 0), COPPER_LIGHT, "X"),
            ((0, 0.85, 0), MINT, "Y"),
            ((0, 0, 0.85), AMBER, "Z"),
        ]
        for endpoint, color, label in axes:
            self._line3d(painter, (0, 0, 0), endpoint, color, 2)
            point = self._project(*endpoint)
            painter.setPen(QPen(QColor(color)))
            painter.setFont(mono(8, True))
            painter.drawText(int(point.x() + 4), int(point.y() - 3), label)

    def _draw_points(self, painter):
        """Draw the cloud with category-specific colors and marker sizes."""
        for x, y, z, category in sorted(self.points, key=lambda p: p[2]):
            point = self._project(x, y, z)

            if category == "floor":
                color, radius = "#719887", 1.15
            elif category == "wall":
                color, radius = "#a6c9b5", 1.4
            elif category == "object":
                color, radius = COPPER, 2.0
            else:
                color, radius = MINT, 1.6

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawEllipse(point, radius, radius)

    def _draw_path(self, painter):
        """Draw the trail when enabled and at least two path points exist."""
        if not self.show_trail or len(self.path) < 2:
            return

        painter.setPen(QPen(QColor(COPPER), 1.5))
        for i in range(1, len(self.path)):
            painter.drawLine(
                self._project(*self.path[i - 1]),
                self._project(*self.path[i]),
            )

        painter.setPen(QPen(QColor(AMBER), 1))
        painter.setBrush(QBrush(QColor("#121510")))
        for i in range(0, len(self.path), 12):
            painter.drawEllipse(self._project(*self.path[i]), 2.2, 2.2)

    def _draw_drone(self, painter):
        """Draw a fixed illustrative drone marker above the ground origin."""
        center = self._project(0, 0, 0.25)
        painter.setPen(QPen(QColor(COPPER_LIGHT), 1.6))
        painter.setBrush(QBrush(QColor("#22231d")))
        painter.drawEllipse(center, 8, 5)

        for dx, dy in [(-14, -8), (14, -8), (-14, 8), (14, 8)]:
            end = QPointF(center.x() + dx, center.y() + dy)
            painter.drawLine(center, end)
            painter.drawEllipse(end, 3, 3)

        painter.setPen(QPen(QColor(MINT_DARK), 1, Qt.DotLine))
        painter.drawLine(center, self._project(0, 0, 0))

    def paintEvent(self, event):
        """Paint the point-cloud scene and indicate when the cloud is demo data."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#0c0f0c"))

        if self.show_grid:
            self._draw_grid(painter)

        self._draw_room(painter)
        self._draw_points(painter)
        self._draw_path(painter)

        if self.show_axes:
            self._draw_axes(painter)

        self._draw_drone(painter)

        painter.setPen(QPen(QColor("#b5a694")))
        painter.setFont(mono(8))
        painter.drawText(14, 22, "LIVE 3D POINT STREAM")
        painter.drawText(14, 38, f"POINTS: {len(self.points):,}")

        painter.setPen(QPen(QColor(MINT)))
        painter.drawText(max(14, self.width() - 145), 22, "● SLAM VIEW")

        if self.demo_mode:
            painter.setPen(QPen(QColor(AMBER)))
            painter.drawText(
                14,
                self.height() - 14,
                "DEMO CLOUD | WAITING FOR SENSOR DATA",
            )

        painter.end()

    def wheelEvent(self, event):
        """Adjust zoom by a factor of 1.10, bounded to 0.45–2.5, and repaint."""
        self.zoom = (
            min(2.5, self.zoom * 1.10)
            if event.angleDelta().y() > 0
            else max(0.45, self.zoom / 1.10)
        )
        self.update()

    def mousePressEvent(self, event):
        """Begin an orbit drag on a left-button press."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_mouse = event.position()

    def mouseMoveEvent(self, event):
        """During a drag, change orbit yaw by 0.008 radians per horizontal pixel."""
        if self.dragging and self.last_mouse is not None:
            delta = event.position() - self.last_mouse
            self.yaw += delta.x() * 0.008
            self.last_mouse = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        """End an orbit drag on a left-button release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_mouse = None


# ============================================================
# Main mapping page
# ============================================================

class MapPanel(QWidget):
    """Bee-Brain mapping page. Preserves common existing public methods."""

    def __init__(self, parent=None):
        """Build an idle mapping console with a demo viewport and stopped scan timer."""
        super().__init__(parent)

        self.scanning = False
        self.point_count = 0
        self.total_point_count = 0
        self.voxel_mm = 20
        self.scan_started_at = None
        self.elapsed_seconds = 0
        self.logs = []
        self._log_sequence = 0

        self.scan_timer = QTimer(self)
        self.scan_timer.setInterval(250)
        self.scan_timer.timeout.connect(self._scan_tick)

        self.init_ui()
        self._log("INIT", "Spatial mapping console initialized.")
        self._log("CALIB", "Waiting for mapping stream.")

    def init_ui(self):
        """Build mapping readouts, the viewport, and local scan and export controls."""
        self.setObjectName("mapPanel")
        self.setStyleSheet(f"""
            QWidget#mapPanel {{ background:{BG}; color:{TEXT}; }}
            QLabel {{ background:transparent; }}
            QSlider::groove:horizontal {{
                background:#343a32; height:4px; border-radius:2px;
            }}
            QSlider::handle:horizontal {{
                background:{COPPER}; width:13px;
                margin:-5px 0; border-radius:6px;
            }}
            QComboBox {{
                background:{PANEL_DARK}; color:{TEXT};
                border:1px solid {BORDER}; border-radius:3px; padding:5px;
            }}
            QPlainTextEdit {{
                background:#0e110e; color:{MINT};
                border:1px solid #252b24;
                font-family:Consolas; font-size:9px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 8)
        root.setSpacing(7)
        root.addLayout(self._build_top_status())

        columns = QHBoxLayout()
        columns.setSpacing(8)

        # Left column.
        self.left_column = QWidget()
        self.left_column.setMinimumWidth(210)
        self.left_column.setMaximumWidth(290)
        left = QVBoxLayout(self.left_column)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)
        left.addWidget(self._build_slam_section())
        left.addWidget(self._build_sensor_section())
        left.addWidget(self._build_occupancy_section())
        left.addStretch(1)
        columns.addWidget(self.left_column, 24)

        # Center viewport.
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        center_layout.addWidget(self._build_camera_toolbar())

        self.point_cloud = PointCloudView()
        center_layout.addWidget(self.point_cloud, 1)
        center_layout.addWidget(self._build_view_footer())
        columns.addWidget(center, 52)

        # Right column.
        self.right_column = QWidget()
        self.right_column.setMinimumWidth(210)
        self.right_column.setMaximumWidth(300)
        right = QVBoxLayout(self.right_column)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        right.addWidget(self._build_scan_controls())
        right.addWidget(self._build_export_section())
        right.addWidget(self._build_diagnostics_section())
        right.addStretch(1)
        columns.addWidget(self.right_column, 24)

        root.addLayout(columns, 1)
        root.addWidget(self._build_bottom_status())
        self._refresh_stats()

    # --------------------------------------------------------
    # Header and left-side cards
    # --------------------------------------------------------

    def _build_top_status(self):
        """Return the mapping header row and create its voxel-size readout."""
        row = QHBoxLayout()
        row.setSpacing(9)
        row.addWidget(make_label(
            "● Spatial SLAM Engine v2.4", AMBER, 9, True, True
        ))
        row.addWidget(make_label(
            "Enclosure: Flight_Chamber_B4 (4.00m × 4.00m × 2.50m)",
            TEXT, 8, False, True
        ), 1)

        self.voxel_top_label = make_label(
            "Voxel Grid: 20mm Isotropic", AMBER, 8, True, True
        )
        row.addWidget(self.voxel_top_label)
        row.addWidget(make_label("SYNC: 250 Hz RTOS", MINT, 8, False, True))
        return row

    def _build_slam_section(self):
        """Return point-count readouts and illustrative registration statistics."""
        frame, layout = make_section("SLAM Registration", "CALIBRATED")
        layout.addWidget(make_label(
            "REGISTERED POINT COUNT", MUTED, 8, False, True
        ))

        count_card = QFrame()
        count_card.setStyleSheet(
            "QFrame {background:#0e110e;border:1px solid #242a23;border-radius:4px;}"
        )
        count_layout = QVBoxLayout(count_card)
        count_layout.setContentsMargins(10, 8, 10, 8)
        count_layout.setSpacing(3)

        self.point_count_label = make_label("0", TEXT, 23, True, True)
        count_layout.addWidget(self.point_count_label)
        self.point_rate_label = make_label("+0 pts/sec", MINT, 8, True, True)
        count_layout.addWidget(self.point_rate_label)
        layout.addWidget(count_card)

        grid = QGridLayout()
        grid.setSpacing(4)

        self.coverage_value = make_metric_card(
            "Voxelized Coverage", "0.0 m²", "0.0% Chamber", MINT
        )
        self.loop_value = make_metric_card(
            "Loop Closures", "0 Valid", "0 Drift Detected", AMBER
        )
        self.rmse_value = make_metric_card(
            "Residual RMSE", "0.0000 m", "σ = 0.0008", TEXT
        )
        self.keyframe_value = make_metric_card(
            "Keyframe Graph", "0 Vertices", "0 Edges", TEXT
        )

        cards = [
            self.coverage_value[0], self.loop_value[0],
            self.rmse_value[0], self.keyframe_value[0],
        ]
        for i, card in enumerate(cards):
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        memory_row = QHBoxLayout()
        memory_row.addWidget(make_label(
            "Octree Buffer Alloc:", MUTED, 8, False, True
        ))
        self.memory_label = make_label(
            "0.0 MB / 64.0 MB", TEXT, 8, False, True
        )
        memory_row.addWidget(self.memory_label, 1)
        layout.addLayout(memory_row)

        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        self.memory_bar.setTextVisible(False)
        self.memory_bar.setMaximumHeight(7)
        self.memory_bar.setStyleSheet(f"""
            QProgressBar {{background:#0d100d;border:none;border-radius:3px;}}
            QProgressBar::chunk {{background:{COPPER};border-radius:3px;}}
        """)
        layout.addWidget(self.memory_bar)
        return frame

    def _build_sensor_section(self):
        """Return sensor badges, an illustrative ToF grid, and velocity readouts."""
        frame, layout = make_section("Spatial Sensor Bus", "I2C / SPI")

        tof_row = QHBoxLayout()
        tof_row.addWidget(make_label("VL53L0X", COPPER_LIGHT, 9, True, True))
        tof_row.addStretch(1)
        self.tof_badge = make_label("● READY", MINT, 8, True, True)
        tof_row.addWidget(self.tof_badge)
        layout.addLayout(tof_row)

        layout.addWidget(make_label(
            "Multizone Time-of-Flight", TEXT, 9, True
        ))
        layout.addWidget(make_label(
            "Range: 0.12m – 3.84m · RMS Noise < 4mm",
            MUTED, 8, False, True
        ))

        self.tof_grid = QGridLayout()
        self.tof_grid.setSpacing(2)
        self.tof_cells = []

        for r in range(8):
            row_cells = []
            for c in range(8):
                cell = QFrame()
                cell.setFixedHeight(8)
                if 2 <= r <= 5 and 1 <= c <= 6:
                    color = "#d7a77b" if r in (3, 4) else "#9ccdb4"
                else:
                    color = "#547365"
                cell.setStyleSheet(
                    f"background:{color};border:1px solid #33483c;"
                )
                self.tof_grid.addWidget(cell, r, c)
                row_cells.append(cell)
            self.tof_cells.append(row_cells)
        layout.addLayout(self.tof_grid)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{BORDER};")
        layout.addWidget(divider)

        flow_row = QHBoxLayout()
        flow_row.addWidget(make_label("PMW3901", COPPER_LIGHT, 9, True, True))
        flow_row.addStretch(1)
        self.flow_badge = make_label("● GROUND LOCK", MINT, 8, True, True)
        flow_row.addWidget(self.flow_badge)
        layout.addLayout(flow_row)

        velocity_grid = QGridLayout()
        velocity_grid.addWidget(
            make_label("ΔX Velocity", MUTED, 8, False, True), 0, 0
        )
        velocity_grid.addWidget(
            make_label("ΔY Velocity", MUTED, 8, False, True), 0, 1
        )
        self.velocity_x_label = make_label("+0.00 m/s", TEXT, 9, True, True)
        self.velocity_y_label = make_label("+0.00 m/s", TEXT, 9, True, True)
        velocity_grid.addWidget(self.velocity_x_label, 1, 0)
        velocity_grid.addWidget(self.velocity_y_label, 1, 1)
        layout.addLayout(velocity_grid)
        return frame

    def _build_occupancy_section(self):
        """Return preset buttons that select the displayed voxel size in millimeters."""
        frame, layout = make_section("Occupancy Grid Density")
        row = QHBoxLayout()
        row.setSpacing(4)
        self.density_buttons = {}

        for text, value in [
            ("Low\n(50mm)", 50),
            ("Med\n(20mm)", 20),
            ("High\n(10mm)", 10),
        ]:
            button = QPushButton(text)
            button.setCheckable(True)
            button.setChecked(value == self.voxel_mm)
            button.setMinimumHeight(37)
            button.setStyleSheet(f"""
                QPushButton {{
                    background:{PANEL_DARK};color:{TEXT};
                    border:1px solid {BORDER};border-radius:3px;
                    padding:4px;font-family:Consolas;font-size:8px;
                }}
                QPushButton:checked {{
                    background:{COPPER};color:#171914;
                    border-color:{COPPER_LIGHT};font-weight:bold;
                }}
            """)
            button.clicked.connect(
                lambda checked=False, v=value: self.set_voxel_size(v)
            )
            self.density_buttons[value] = button
            row.addWidget(button)

        layout.addLayout(row)
        return frame

    # --------------------------------------------------------
    # Center toolbar and footer
    # --------------------------------------------------------

    def _build_camera_toolbar(self):
        """Return camera selection, reset, and trail-visibility controls."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{background:{PANEL};border:1px solid {BORDER};border-radius:4px;}}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(7, 6, 7, 6)
        layout.setSpacing(5)

        camera_row = QHBoxLayout()
        camera_row.setSpacing(4)
        self.camera_buttons = {}

        for mode in ["Isometric", "Top (Z)", "Side (X)", "First-Person"]:
            button = QPushButton(mode)
            button.setCheckable(True)
            button.setChecked(mode == "Isometric")
            button.setMinimumHeight(28)
            button.setStyleSheet(f"""
                QPushButton {{
                    background:{PANEL_DARK};color:{TEXT};
                    border:1px solid {BORDER};border-radius:3px;
                    padding:4px 7px;font-size:9px;
                }}
                QPushButton:checked {{
                    background:{COPPER};color:#171914;
                    border-color:{COPPER_LIGHT};font-weight:bold;
                }}
            """)
            button.clicked.connect(
                lambda checked=False, m=mode: self.set_camera_mode(m)
            )
            camera_row.addWidget(button)
            self.camera_buttons[mode] = button
        layout.addLayout(camera_row)

        controls = QHBoxLayout()
        self.camera_info = make_label(
            "Cam: Iso 45° / Elev 30°", MUTED, 8, False, True
        )
        controls.addWidget(self.camera_info)
        controls.addStretch(1)

        reset_button = make_button("↻ Reset")
        reset_button.clicked.connect(self.reset_view)
        controls.addWidget(reset_button)

        self.trail_button = make_button("Trail: ON")
        self.trail_button.setCheckable(True)
        self.trail_button.setChecked(True)
        self.trail_button.clicked.connect(self.toggle_trail)
        controls.addWidget(self.trail_button)

        layout.addLayout(controls)
        return frame

    def _build_view_footer(self):
        """Return the illustrative scale and XYZ direction legend."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{background:{PANEL};border:1px solid {BORDER};border-radius:4px;}}
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(8)
        layout.addWidget(make_label("Scale: 1.0 m", MUTED, 8, False, True))
        layout.addStretch(1)
        layout.addWidget(make_label("■ +X East", COPPER_LIGHT, 8, False, True))
        layout.addWidget(make_label("■ +Y North", MINT, 8, False, True))
        layout.addWidget(make_label("■ +Z Altitude", AMBER, 8, False, True))
        return frame

    # --------------------------------------------------------
    # Right column
    # --------------------------------------------------------

    def _build_scan_controls(self):
        """Return scan controls, buffer actions, and elapsed-time readouts."""
        frame, layout = make_section("Scan Controller")

        # FIX: create the status label directly instead of trying to
        # retrieve a nested layout from the heading widget.
        status_row = QHBoxLayout()
        status_row.addStretch(1)
        self.controller_state = make_label(
            "STATE: IDLE", MUTED, 8, True, True
        )
        status_row.addWidget(self.controller_state)
        layout.insertLayout(1, status_row)

        self.scan_button = make_button("◎ START MAPPING SCAN", True)
        self.scan_button.setMinimumHeight(40)
        self.scan_button.clicked.connect(self.toggle_scan)
        layout.addWidget(self.scan_button)

        self.pause_button = make_button("Ⅱ PAUSE / STOP SCAN")
        self.pause_button.clicked.connect(self.toggle_scan)
        layout.addWidget(self.pause_button)

        actions = QHBoxLayout()
        self.clear_button = make_button("▧ Clear Buffer")
        self.clear_button.clicked.connect(self.clear_map)
        actions.addWidget(self.clear_button)

        self.export_button = make_button("↓ Export PLY")
        self.export_button.clicked.connect(self.export_ply)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)

        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        self.scan_progress.setTextVisible(False)
        self.scan_progress.setMaximumHeight(6)
        self.scan_progress.setStyleSheet(f"""
            QProgressBar {{background:#0c0f0c;border:none;border-radius:3px;}}
            QProgressBar::chunk {{background:{MINT_DARK};border-radius:3px;}}
        """)
        layout.addWidget(self.scan_progress)

        self.scan_elapsed_label = make_label(
            "SCAN DURATION: 00:00", MUTED, 8, False, True
        )
        layout.addWidget(self.scan_elapsed_label)
        return frame

    def _build_export_section(self):
        """Return the export-format selector and display-only voxel-size slider."""
        frame, layout = make_section("Point Cloud Export")
        layout.addWidget(make_label("POINT CLOUD FORMAT", MUTED, 8, False, True))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Stanford PLY (.ply)", "XYZ Text (.xyz)"])
        layout.addWidget(self.format_combo)

        voxel_header = QHBoxLayout()
        voxel_header.addWidget(
            make_label("Octree Voxel Leaf Size", MUTED, 8, False, True)
        )
        voxel_header.addStretch(1)
        self.voxel_label = make_label(
            "20 mm", COPPER_LIGHT, 9, True, True
        )
        voxel_header.addWidget(self.voxel_label)
        layout.addLayout(voxel_header)

        self.voxel_slider = QSlider(Qt.Horizontal)
        self.voxel_slider.setRange(5, 50)
        self.voxel_slider.setValue(self.voxel_mm)
        self.voxel_slider.valueChanged.connect(self._voxel_slider_changed)
        layout.addWidget(self.voxel_slider)

        scales = QHBoxLayout()
        scales.addWidget(make_label("5mm (Dense)", MUTED, 8, False, True))
        scales.addStretch(1)
        scales.addWidget(make_label("50mm (Coarse)", MUTED, 8, False, True))
        layout.addLayout(scales)
        return frame

    def _build_diagnostics_section(self):
        """Return the diagnostic console and illustrative quality metrics."""
        frame, layout = make_section("Kernel Diagnostics", "STREAM: STDOUT")
        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        self.diagnostics.setMinimumHeight(160)
        self.diagnostics.setMaximumBlockCount(100)
        layout.addWidget(self.diagnostics)

        grid = QGridLayout()
        grid.setSpacing(4)
        self.rejection_card = make_metric_card(
            "Point Rejection", "< 1.2%", "Outliers", MINT
        )
        self.confidence_card = make_metric_card(
            "EKF Confidence", "99.1%", "(demo estimate)", AMBER
        )
        grid.addWidget(self.rejection_card[0], 0, 0)
        grid.addWidget(self.confidence_card[0], 0, 1)
        layout.addLayout(grid)
        return frame

    def _build_bottom_status(self):
        """Return scan-state, buffer-count, and clock readouts with demo anchor text."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{background:{PANEL};border:1px solid {BORDER};border-radius:3px;}}
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(9, 6, 9, 6)
        layout.setSpacing(12)

        self.bottom_scan_status = make_label("● IDLE", MUTED, 8, True, True)
        layout.addWidget(self.bottom_scan_status)

        self.bottom_count_label = make_label(
            "BUFFER: 0 PTS", TEXT, 8, False, True
        )
        layout.addWidget(self.bottom_count_label)
        layout.addStretch(1)

        layout.addWidget(make_label(
            "UWB Anchors: 4 Synced", MINT, 8, False, True
        ))
        self.clock_label = make_label(
            "SYS CLK: --:--:--", MUTED, 8, False, True
        )
        layout.addWidget(self.clock_label)
        return frame

    # --------------------------------------------------------
    # Scan operations
    # --------------------------------------------------------

    def toggle_scan(self):
        """Toggle the local demo scan timer and its status indicators."""
        self.stop_scan() if self.scanning else self.start_scan()

    def start_scan(self):
        """Start demo counter updates and timing unless already scanning.

        Existing counts are retained; the displayed point cloud is unchanged.
        """
        if self.scanning:
            return

        self.scanning = True
        self.scan_started_at = time.monotonic()
        self.scan_timer.start()

        self.scan_button.setText("● SCANNING — CLICK TO STOP")
        self.controller_state.setText("STATE: ACTIVE")
        self.controller_state.setStyleSheet(
            f"color:{MINT};background:transparent;"
        )
        self.bottom_scan_status.setText("● SCANNING")
        self.bottom_scan_status.setStyleSheet(
            f"color:{MINT};background:transparent;"
        )
        self._log("SLAM", "Mapping scan started.")
        self._refresh_stats()

    def stop_scan(self):
        """Stop demo counter updates and display idle status while retaining counts."""
        self.scanning = False
        self.scan_timer.stop()

        self.scan_button.setText("◎ START MAPPING SCAN")
        self.controller_state.setText("STATE: IDLE")
        self.controller_state.setStyleSheet(
            f"color:{MUTED};background:transparent;"
        )
        self.bottom_scan_status.setText("● IDLE")
        self.bottom_scan_status.setStyleSheet(
            f"color:{MUTED};background:transparent;"
        )
        self._log("SLAM", "Mapping scan stopped.")
        self._refresh_stats()

    def _scan_tick(self):
        """Advance demo scan readouts and counts without changing cloud data."""
        if not self.scanning:
            return

        # Demo-only counter; replace this with actual SLAM data.
        increment = random.randint(75, 150)
        self.point_count += increment
        self.total_point_count += increment

        self.elapsed_seconds = int(
            time.monotonic() - self.scan_started_at
        )
        self.scan_progress.setValue(self.elapsed_seconds % 101)
        self.scan_elapsed_label.setText(
            f"SCAN DURATION: {self.elapsed_seconds // 60:02d}:"
            f"{self.elapsed_seconds % 60:02d}"
        )
        self.clock_label.setText("SYS CLK: " + time.strftime("%H:%M:%S"))

        self.velocity_x_label.setText(
            f"{random.uniform(-0.04, 0.04):+.2f} m/s"
        )
        self.velocity_y_label.setText(
            f"{random.uniform(-0.04, 0.04):+.2f} m/s"
        )

        self._refresh_stats()

        if self.total_point_count % 1000 < increment:
            self._log(
                "VOXEL",
                f"Demo stream counter: {self.point_count:,} points.",
            )

    def add_points(self, count):
        """Add a count to current and total counters without adding cloud coordinates.

        Convert count to an integer and clamp negative counts to zero.
        Integer-conversion errors propagate to the caller.
        """
        count = max(0, int(count))
        self.point_count += count
        self.total_point_count += count
        self._refresh_stats()

    def set_point_cloud(self, points):
        """Set real XYZ data: [(x, y, z), ...] or [(x, y, z, category), ...].

        Require a sized sequence and use PointCloudView.set_points conversion
        rules, propagating its errors. The displayed count uses the supplied
        sequence length, even for entries the viewport skips. Preserve
        total_point_count if it already exceeds the supplied count.
        """
        self.point_cloud.set_points(points)
        self.point_count = len(points)
        self.total_point_count = max(self.total_point_count, self.point_count)
        self._refresh_stats()
        self._log("SLAM", f"External point cloud updated: {len(points):,} points.")

    def clear_map(self):
        """Stop scanning, reset counts and duration, and restore the demo cloud."""
        self.stop_scan()
        self.point_count = 0
        self.total_point_count = 0
        self.elapsed_seconds = 0

        # Reset to the visual demo cloud; it is not actual sensor data.
        self.point_cloud._generate_demo_points()
        self.scan_progress.setValue(0)
        self.scan_elapsed_label.setText("SCAN DURATION: 00:00")

        self._log("BUFFER", "Mapping counter and buffer cleared.")
        self._refresh_stats()

    # --------------------------------------------------------
    # Camera, voxel and sensor controls
    # --------------------------------------------------------

    def set_camera_mode(self, mode):
        """Apply a viewport projection and synchronize its button and caption."""
        self.point_cloud.set_camera_mode(mode)

        for name, button in self.camera_buttons.items():
            button.setChecked(name == mode)

        labels = {
            "Isometric": "Cam: Iso 45° / Elev 30°",
            "Top (Z)": "Cam: Top / Z Axis",
            "Side (X)": "Cam: Side / X Axis",
            "First-Person": "Cam: First-Person",
        }
        self.camera_info.setText(labels.get(mode, f"Cam: {mode}"))

    def reset_view(self):
        """Reset viewport orbit and zoom and select the isometric camera control."""
        self.point_cloud.reset_view()
        self.set_camera_mode("Isometric")
        self._log("VIEW", "Camera view reset.")

    def toggle_trail(self, checked):
        """Set viewport trail visibility and synchronize the toggle caption."""
        self.point_cloud.set_trail_visible(checked)
        self.trail_button.setText("Trail: ON" if checked else "Trail: OFF")

    def set_voxel_size(self, value):
        """Set the displayed voxel size in millimeters and synchronize controls.

        This changes local UI state without filtering the cloud. The slider
        clamps its own display to 5–50; voxel_mm retains the converted integer.
        Integer-conversion errors propagate to the caller.
        """
        self.voxel_mm = int(value)
        self.voxel_slider.blockSignals(True)
        self.voxel_slider.setValue(self.voxel_mm)
        self.voxel_slider.blockSignals(False)

        for size, button in self.density_buttons.items():
            button.setChecked(size == self.voxel_mm)

        self.voxel_label.setText(f"{self.voxel_mm} mm")
        self.voxel_top_label.setText(
            f"Voxel Grid: {self.voxel_mm}mm Isotropic"
        )
        self._log("VOXEL", f"Voxel leaf size set to {self.voxel_mm} mm.")

    def _voxel_slider_changed(self, value):
        """Update the displayed millimeter size and presets from the voxel slider."""
        self.voxel_mm = int(value)
        self.voxel_label.setText(f"{value} mm")
        self.voxel_top_label.setText(f"Voxel Grid: {value}mm Isotropic")

        for size, button in self.density_buttons.items():
            button.setChecked(size == value)

    def set_sensor_status(self, connected):
        """Compatibility method for ToF sensor status updates."""
        if connected:
            self.tof_badge.setText("● READY")
            self.tof_badge.setStyleSheet(
                f"color:{MINT};background:transparent;"
            )
            self._log("CALIB", "ToF sensor marked ready.")
        else:
            self.tof_badge.setText("● ERROR")
            self.tof_badge.setStyleSheet(
                f"color:{RED};background:transparent;"
            )
            self._log("CALIB", "ToF sensor connection error.")

    def set_optical_flow_status(self, connected):
        """Display ground-lock availability from the supplied optical-flow flag."""
        if connected:
            self.flow_badge.setText("● GROUND LOCK")
            self.flow_badge.setStyleSheet(
                f"color:{MINT};background:transparent;"
            )
        else:
            self.flow_badge.setText("● NO LOCK")
            self.flow_badge.setStyleSheet(
                f"color:{RED};background:transparent;"
            )

    def set_velocity(self, dx, dy):
        """Display X and Y velocities in meters per second.

        Float-conversion errors propagate to the caller.
        """
        self.velocity_x_label.setText(f"{float(dx):+.2f} m/s")
        self.velocity_y_label.setText(f"{float(dy):+.2f} m/s")

    # --------------------------------------------------------
    # Export
    # --------------------------------------------------------

    def export_ply(self):
        """Prompt for a path and write the current cloud as ASCII PLY or XYZ.

        Use the selected format, appending its extension when needed. Export
        XYZ coordinates only, including demo points when displayed, and
        overwrite the chosen file. Canceling writes nothing. OSError is caught
        and reported in the panel; other errors propagate to the caller.
        """
        is_xyz = self.format_combo.currentIndex() == 1
        extension = ".xyz" if is_xyz else ".ply"
        default_name = "bee_brain_map" + extension
        file_filter = (
            "XYZ point cloud (*.xyz)"
            if is_xyz
            else "Stanford PLY point cloud (*.ply)"
        )

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Point Cloud", default_name, file_filter
        )
        if not path:
            return

        if not path.lower().endswith(extension):
            path += extension

        try:
            points = self.point_cloud.points

            with open(path, "w", encoding="utf-8") as file:
                if is_xyz:
                    for x, y, z, _category in points:
                        file.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
                else:
                    file.write("ply\n")
                    file.write("format ascii 1.0\n")
                    file.write(f"element vertex {len(points)}\n")
                    file.write("property float x\n")
                    file.write("property float y\n")
                    file.write("property float z\n")
                    file.write("end_header\n")
                    for x, y, z, _category in points:
                        file.write(f"{x:.6f} {y:.6f} {z:.6f}\n")

            self._log("EXPORT", f"Exported {len(points):,} points to {path}.")

        except OSError as exc:
            self._log("ERROR", f"Export failed: {exc}")

    # --------------------------------------------------------
    # Statistics and diagnostics
    # --------------------------------------------------------

    def _refresh_stats(self):
        """Refresh counts and demo coverage, registration, and memory estimates."""
        self.point_count_label.setText(f"{self.point_count:,}")
        self.point_rate_label.setText(
            "+480 pts/sec" if self.scanning else "+0 pts/sec"
        )

        coverage = min(16.0, self.point_count * 0.00031)
        percentage = min(100.0, coverage / 16.0 * 100.0)
        self.coverage_value[1].setText(f"{coverage:.1f} m²")
        self.coverage_value[2].setText(f"{percentage:.1f}% Chamber")

        self.loop_value[1].setText(
            f"{min(14, self.point_count // 1500)} Valid"
        )
        self.loop_value[2].setText("0 Drift Detected")

        rmse = max(0.001, 0.0034 - self.point_count * 0.00000001)
        self.rmse_value[1].setText(f"{rmse:.4f} m")
        self.rmse_value[2].setText("σ = 0.0008")

        vertices = min(318, self.point_count // 150)
        self.keyframe_value[1].setText(f"{vertices} Vertices")
        self.keyframe_value[2].setText(f"{vertices * 4:,} Edges")

        memory = min(64.0, self.point_count * 0.00038)
        self.memory_label.setText(f"{memory:.1f} MB / 64.0 MB")
        self.memory_bar.setValue(int(memory / 64.0 * 100))
        self.bottom_count_label.setText(f"BUFFER: {self.point_count:,} PTS")

    def _log(self, category, message):
        """Append a timestamped event to history and the console when present."""
        self._log_sequence += 1
        timestamp = time.strftime("%H:%M:%S")
        line = (
            f"[{timestamp}.{self._log_sequence % 100:02d}] "
            f"{category}: {message}"
        )
        self.logs.append(line)

        if hasattr(self, "diagnostics"):
            self.diagnostics.appendPlainText(line)
