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
)


class MapPanel(QWidget):
    """Bee-Brain 3D Mapping interface."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scanning = False
        self.point_count = 0

        self.init_ui()

    # ==================================================
    # UI
    # ==================================================

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20, 20, 20, 20
        )

        layout.setSpacing(15)

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        title = QLabel("3D MAPPING")

        title.setFont(
            QFont("Arial", 18, QFont.Bold)
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(title)

        subtitle = QLabel(
            "Sensor-based spatial reconstruction"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet(
            "color: #888888;"
        )

        layout.addWidget(subtitle)

        # --------------------------------------------------
        # Point cloud view
        # --------------------------------------------------

        map_frame = self.create_section(
            "POINT CLOUD VIEW"
        )

        self.map_view = QLabel(
            "3D POINT CLOUD\n\n"
            "No mapping data available"
        )

        self.map_view.setAlignment(
            Qt.AlignCenter
        )

        self.map_view.setMinimumHeight(
            300
        )

        self.map_view.setStyleSheet(
            """
            QLabel {
                background-color: #111111;
                border: 1px solid #333333;
                color: #555555;
                font-size: 16px;
            }
            """
        )

        map_frame.layout().addWidget(
            self.map_view
        )

        layout.addWidget(
            map_frame
        )

        # --------------------------------------------------
        # Mapping status
        # --------------------------------------------------

        status_frame = self.create_section(
            "MAPPING STATUS"
        )

        status_layout = QGridLayout()

        status_layout.setSpacing(
            10
        )

        # Scan status
        status_layout.addWidget(
            QLabel("SCAN STATUS"),
            0,
            0
        )

        self.scan_status = QLabel(
            "IDLE"
        )

        self.scan_status.setAlignment(
            Qt.AlignCenter
        )

        self.scan_status.setStyleSheet(
            "color: #888888; "
            "font-weight: bold;"
        )

        status_layout.addWidget(
            self.scan_status,
            0,
            1
        )

        # Point count
        status_layout.addWidget(
            QLabel("POINTS"),
            1,
            0
        )

        self.point_count_label = QLabel(
            "0"
        )

        self.point_count_label.setAlignment(
            Qt.AlignCenter
        )

        status_layout.addWidget(
            self.point_count_label,
            1,
            1
        )

        # Sensor
        status_layout.addWidget(
            QLabel("SENSOR"),
            2,
            0
        )

        self.sensor_status = QLabel(
            "ToF: READY"
        )

        self.sensor_status.setAlignment(
            Qt.AlignCenter
        )

        self.sensor_status.setStyleSheet(
            "color: #00cc88; "
            "font-weight: bold;"
        )

        status_layout.addWidget(
            self.sensor_status,
            2,
            1
        )

        status_frame.layout().addLayout(
            status_layout
        )

        layout.addWidget(
            status_frame
        )

        # --------------------------------------------------
        # Controls
        # --------------------------------------------------

        controls_frame = self.create_section(
            "MAPPING CONTROLS"
        )

        controls_layout = QHBoxLayout()

        self.scan_button = QPushButton(
            "START SCAN"
        )

        self.scan_button.setMinimumHeight(
            40
        )

        self.scan_button.clicked.connect(
            self.toggle_scan
        )

        controls_layout.addWidget(
            self.scan_button
        )

        self.clear_button = QPushButton(
            "CLEAR MAP"
        )

        self.clear_button.setMinimumHeight(
            40
        )

        self.clear_button.clicked.connect(
            self.clear_map
        )

        controls_layout.addWidget(
            self.clear_button
        )

        controls_frame.layout().addLayout(
            controls_layout
        )

        layout.addWidget(
            controls_frame
        )

        layout.addStretch()

    # ==================================================
    # HELPERS
    # ==================================================

    def create_section(self, title):
        """Create a reusable section frame."""

        frame = QFrame()

        frame.setFrameStyle(
            QFrame.StyledPanel |
            QFrame.Raised
        )

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        layout.setSpacing(
            10
        )

        title_label = QLabel(title)

        title_label.setFont(
            QFont("Arial", 10, QFont.Bold)
        )

        title_label.setStyleSheet(
            "color: #888888;"
        )

        title_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            title_label
        )

        return frame

    # ==================================================
    # SCANNING
    # ==================================================

    def toggle_scan(self):
        if self.scanning:
            self.stop_scan()
        else:
            self.start_scan()

    def start_scan(self):
        self.scanning = True

        self.scan_status.setText(
            "SCANNING"
        )

        self.scan_status.setStyleSheet(
            "color: #00cc88; "
            "font-weight: bold;"
        )

        self.scan_button.setText(
            "STOP SCAN"
        )

        self.map_view.setText(
            "3D POINT CLOUD\n\n"
            "Scanning..."
        )

    def stop_scan(self):
        self.scanning = False

        self.scan_status.setText(
            "IDLE"
        )

        self.scan_status.setStyleSheet(
            "color: #888888; "
            "font-weight: bold;"
        )

        self.scan_button.setText(
            "START SCAN"
        )

        self.map_view.setText(
            "3D POINT CLOUD\n\n"
            "Scan stopped"
        )

    # ==================================================
    # MAP DATA
    # ==================================================

    def add_points(self, count):
        """Update displayed point count."""

        count = max(
            0,
            int(count)
        )

        self.point_count += count

        self.point_count_label.setText(
            str(self.point_count)
        )

    def clear_map(self):
        """Clear mapping state."""

        self.point_count = 0

        self.point_count_label.setText(
            "0"
        )

        self.scanning = False

        self.scan_status.setText(
            "IDLE"
        )

        self.scan_status.setStyleSheet(
            "color: #888888; "
            "font-weight: bold;"
        )

        self.scan_button.setText(
            "START SCAN"
        )

        self.map_view.setText(
            "3D POINT CLOUD\n\n"
            "No mapping data available"
        )

    def set_sensor_status(self, connected):
        """Update ToF sensor status."""

        if connected:
            self.sensor_status.setText(
                "ToF: READY"
            )

            self.sensor_status.setStyleSheet(
                "color: #00cc88; "
                "font-weight: bold;"
            )

        else:
            self.sensor_status.setText(
                "ToF: ERROR"
            )

            self.sensor_status.setStyleSheet(
                "color: #ff5555; "
                "font-weight: bold;"
            )