import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt

from dashboard.services.telemetry import TelemetryService
from dashboard.services.fake_data_generator import FakeTelemetryGenerator

from dashboard.ui.telemetry_panel import TelemetryPanel
from dashboard.ui.control_panel import ControlPanel
from dashboard.ui.map_panel import MapPanel
from dashboard.ui.diagnostics_panel import DiagnosticsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bee-Brain")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)

        # ==================================================
        # SERVICES
        # ==================================================

        self.telemetry_service = TelemetryService()

        self.fake_telemetry = FakeTelemetryGenerator(
            self
        )

        # ==================================================
        # MAIN UI
        # ==================================================

        self.init_ui()

        # ==================================================
        # START FAKE TELEMETRY
        # ==================================================

        self.fake_telemetry.start(
            self.handle_telemetry,
            interval_ms=100,
        )

    # ======================================================
    # MAIN UI
    # ======================================================

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # ==================================================
        # SIDEBAR
        # ==================================================

        sidebar = self.create_sidebar()

        main_layout.addWidget(
            sidebar
        )

        # ==================================================
        # CONTENT AREA
        # ==================================================

        content_widget = QWidget()

        content_layout = QVBoxLayout(
            content_widget
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(0)

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        header = QFrame()

        header.setFixedHeight(70)

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            30,
            0,
            30,
            0,
        )

        self.page_title = QLabel(
            "TELEMETRY"
        )

        self.page_title.setObjectName(
            "pageTitle"
        )

        header_layout.addWidget(
            self.page_title
        )

        header_layout.addStretch()

        content_layout.addWidget(
            header
        )

        # --------------------------------------------------
        # STACKED PAGES
        # --------------------------------------------------

        self.pages = QStackedWidget()

        # Telemetry
        self.telemetry_panel = TelemetryPanel()

        # Flight Control
        self.control_panel = ControlPanel()

        # 3D Mapping
        self.map_panel = MapPanel()

        # Diagnostics
        self.diagnostics_panel = DiagnosticsPanel()

        # Add pages
        self.pages.addWidget(
            self.telemetry_panel
        )

        self.pages.addWidget(
            self.control_panel
        )

        self.pages.addWidget(
            self.map_panel
        )

        self.pages.addWidget(
            self.diagnostics_panel
        )

        content_layout.addWidget(
            self.pages
        )

        # --------------------------------------------------
        # STATUS BAR
        # --------------------------------------------------

        status_frame = QFrame()

        status_frame.setFixedHeight(35)

        status_layout = QHBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            25,
            0,
            25,
            0,
        )

        self.system_status = QLabel(
            "● SYSTEM ONLINE"
        )

        self.system_status.setStyleSheet(
            "color: #00ff99;"
        )

        status_layout.addWidget(
            self.system_status
        )

        status_layout.addStretch()

        self.data_status = QLabel(
            "FAKE TELEMETRY"
        )

        self.data_status.setStyleSheet(
            "color: #888888;"
        )

        status_layout.addWidget(
            self.data_status
        )

        content_layout.addWidget(
            status_frame
        )

        main_layout.addWidget(
            content_widget
        )

        # ==================================================
        # DEFAULT PAGE
        # ==================================================

        self.pages.setCurrentIndex(0)

        self.update_navigation(
            self.telemetry_button
        )

    # ======================================================
    # SIDEBAR
    # ======================================================

    def create_sidebar(self):
        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            200
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            15,
            20,
            15,
            15,
        )

        sidebar_layout.setSpacing(10)

        # --------------------------------------------------
        # LOGO
        # --------------------------------------------------

        logo = QLabel(
            "🛸 BEE-BRAIN"
        )

        logo.setObjectName(
            "logo"
        )

        logo.setFont(
            self.create_font(
                20,
                True,
            )
        )

        sidebar_layout.addWidget(
            logo
        )

        subtitle = QLabel(
            "AUTONOMOUS ROBOTICS"
        )

        subtitle.setObjectName(
            "sidebarSubtitle"
        )

        sidebar_layout.addWidget(
            subtitle
        )

        sidebar_layout.addSpacing(
            35
        )

        # --------------------------------------------------
        # NAVIGATION BUTTONS
        # --------------------------------------------------

        self.telemetry_button = self.create_nav_button(
            "Telemetry"
        )

        self.control_button = self.create_nav_button(
            "Flight Control"
        )

        self.map_button = self.create_nav_button(
            "3D Mapping"
        )

        self.diagnostics_button = self.create_nav_button(
            "Diagnostics"
        )

        sidebar_layout.addWidget(
            self.telemetry_button
        )

        sidebar_layout.addWidget(
            self.control_button
        )

        sidebar_layout.addWidget(
            self.map_button
        )

        sidebar_layout.addWidget(
            self.diagnostics_button
        )

        sidebar_layout.addStretch()

        return sidebar

    # ======================================================
    # NAVIGATION BUTTON
    # ======================================================

    def create_nav_button(
        self,
        text,
    ):
        button = QPushButton(
            text
        )

        button.setObjectName(
            "navButton"
        )

        button.setMinimumHeight(
            55
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        if text == "Telemetry":
            button.clicked.connect(
                lambda: self.show_page(
                    0,
                    "TELEMETRY",
                    button,
                )
            )

        elif text == "Flight Control":
            button.clicked.connect(
                lambda: self.show_page(
                    1,
                    "FLIGHT CONTROL",
                    button,
                )
            )

        elif text == "3D Mapping":
            button.clicked.connect(
                lambda: self.show_page(
                    2,
                    "3D MAPPING",
                    button,
                )
            )

        elif text == "Diagnostics":
            button.clicked.connect(
                lambda: self.show_page(
                    3,
                    "DIAGNOSTICS",
                    button,
                )
            )

        return button

    # ======================================================
    # SHOW PAGE
    # ======================================================

    def show_page(
        self,
        index,
        title,
        button,
    ):
        self.pages.setCurrentIndex(
            index
        )

        self.page_title.setText(
            title
        )

        self.update_navigation(
            button
        )

    # ======================================================
    # NAVIGATION STYLE
    # ======================================================

    def update_navigation(
        self,
        active_button,
    ):
        buttons = [
            self.telemetry_button,
            self.control_button,
            self.map_button,
            self.diagnostics_button,
        ]

        for button in buttons:
            if button == active_button:
                button.setProperty(
                    "active",
                    True,
                )
            else:
                button.setProperty(
                    "active",
                    False,
                )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

            button.update()

    # ======================================================
    # TELEMETRY HANDLER
    # ======================================================

    def handle_telemetry(
        self,
        raw_json,
    ):
        try:
            packet = (
                self.telemetry_service
                .add_packet(raw_json)
            )

            # Update telemetry page
            self.telemetry_panel.update_telemetry(
                packet
            )

            # Update diagnostics data source
            self.diagnostics_panel.data_source.setText(
                "FAKE DATA"
            )

            # Update diagnostics packet count
            packet_count = len(
                self.telemetry_service.get_history()
            )

            self.diagnostics_panel.packet_count.setText(
                str(packet_count)
            )

            # Update diagnostics link state
            if packet.link_ok:
                self.diagnostics_panel.link_status.setText(
                    "● CONNECTED"
                )

                self.diagnostics_panel.link_status.setStyleSheet(
                    "color: #00ff99;"
                )
            else:
                self.diagnostics_panel.link_status.setText(
                    "● DISCONNECTED"
                )

                self.diagnostics_panel.link_status.setStyleSheet(
                    "color: #ff4444;"
                )

            # Update ToF diagnostics
            if packet.sensor_status.tof:
                self.diagnostics_panel.tof_status.setText(
                    "● OK"
                )

                self.diagnostics_panel.tof_status.setStyleSheet(
                    "color: #00ff99;"
                )
            else:
                self.diagnostics_panel.tof_status.setText(
                    "● ERROR"
                )

                self.diagnostics_panel.tof_status.setStyleSheet(
                    "color: #ff4444;"
                )

            # Update optical-flow diagnostics
            if packet.sensor_status.optical_flow:
                self.diagnostics_panel.optical_flow_status.setText(
                    "● OK"
                )

                self.diagnostics_panel.optical_flow_status.setStyleSheet(
                    "color: #00ff99;"
                )
            else:
                self.diagnostics_panel.optical_flow_status.setText(
                    "● ERROR"
                )

                self.diagnostics_panel.optical_flow_status.setStyleSheet(
                    "color: #ff4444;"
                )

            # Update battery diagnostics
            battery = packet.battery_v

            self.diagnostics_panel.battery_status.setText(
                f"{battery:.2f} V"
            )

            if battery > 3.7:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #00ff99;"
                )

                self.diagnostics_panel.power_status.setText(
                    "HEALTHY"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #00ff99;"
                )

            elif battery > 3.4:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #ffff00;"
                )

                self.diagnostics_panel.power_status.setText(
                    "WARNING"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #ffff00;"
                )

            else:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #ff4444;"
                )

                self.diagnostics_panel.power_status.setText(
                    "CRITICAL"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #ff4444;"
                )

        except Exception as error:
            self.system_status.setText(
                "● SYSTEM ERROR"
            )

            self.system_status.setStyleSheet(
                "color: #ff4444;"
            )

            self.diagnostics_panel.system_status.setText(
                "ERROR"
            )

            self.diagnostics_panel.system_status.setStyleSheet(
                "color: #ff4444;"
            )

            self.diagnostics_panel.diagnostic_message.setText(
                str(error)
            )

            self.diagnostics_panel.diagnostic_message.setStyleSheet(
                "color: #ff4444;"
            )

    # ======================================================
    # FONT HELPER
    # ======================================================

    def create_font(
        self,
        size,
        bold=False,
    ):
        from PySide6.QtGui import QFont

        font = QFont(
            "Arial",
            size,
        )

        if bold:
            font.setBold(True)

        return font

    # ======================================================
    # CLOSE EVENT
    # ======================================================

    def closeEvent(
        self,
        event,
    ):
        self.fake_telemetry.stop()

        event.accept()


# ==========================================================
# APPLICATION STYLE
# ==========================================================

def apply_dark_style(
    app,
):
    app.setStyleSheet(
        """
        QWidget {
            background-color: #1e1e1e;
            color: #eeeeee;
            font-family: Arial;
        }

        QMainWindow {
            background-color: #1e1e1e;
        }

        #sidebar {
            background-color: #202020;
            border-right: 1px solid #303030;
        }

        #logo {
            color: #ffffff;
        }

        #sidebarSubtitle {
            color: #777777;
            font-size: 9px;
            padding-left: 5px;
        }

        #pageTitle {
            color: #eeeeee;
            font-size: 26px;
            font-weight: bold;
        }

        #navButton {
            background-color: transparent;
            color: #dddddd;
            border: none;
            border-radius: 6px;
            text-align: left;
            padding-left: 15px;
            font-size: 13px;
        }

        #navButton:hover {
            background-color: #2a2a2a;
        }

        #navButton[active="true"] {
            background-color: #00b894;
            color: #ffffff;
        }

        QFrame {
            border-color: #333333;
        }

        QFrame[frameShape="4"] {
            border: 1px solid #333333;
        }

        QPushButton {
            background-color: #303030;
            color: #eeeeee;
            border: 1px solid #444444;
            border-radius: 5px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #3a3a3a;
        }

        QPushButton:pressed {
            background-color: #252525;
        }

        QComboBox {
            background-color: #303030;
            color: #eeeeee;
            border: 1px solid #444444;
            border-radius: 5px;
            padding: 5px;
        }

        QComboBox:hover {
            border: 1px solid #00b894;
        }

        QComboBox QAbstractItemView {
            background-color: #292929;
            color: #eeeeee;
            selection-background-color: #00b894;
            selection-color: #ffffff;
            border: 1px solid #444444;
        }

        QProgressBar {
            background-color: #303030;
            border: 1px solid #444444;
            border-radius: 5px;
            text-align: center;
            color: #eeeeee;
        }

        QProgressBar::chunk {
            background-color: #00b894;
            border-radius: 4px;
        }

        QScrollBar:vertical {
            background-color: #1e1e1e;
            width: 10px;
        }

        QScrollBar::handle:vertical {
            background-color: #444444;
            border-radius: 5px;
        }
        """
    )


# ==========================================================
# MAIN
# ==========================================================

def main():
    app = QApplication(
        sys.argv
    )

    apply_dark_style(
        app
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()