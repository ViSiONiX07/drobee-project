import sys

from PySide6.QtCore import Qt
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

from dashboard.services.fake_data_generator import FakeTelemetryGenerator
from dashboard.services.telemetry import TelemetryService
from dashboard.ui.control_panel import ControlPanel
from dashboard.ui.diagnostics_panel import DiagnosticsPanel
from dashboard.ui.drone_view_panel import DroneViewPanel
from dashboard.ui.keyboard_control_panel import KeyboardControlPanel
from dashboard.ui.map_panel import MapPanel
from dashboard.ui.telemetry_panel import TelemetryPanel


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
        header.setObjectName("header")
        header.setFixedHeight(58)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        header_layout.setSpacing(8)

        breadcrumb = QLabel("BREADCRUMB  /")
        breadcrumb.setObjectName("headerBreadcrumb")
        header_layout.addWidget(breadcrumb)

        self.page_title = QLabel("TELEMETRY")
        self.page_title.setObjectName("pageTitle")
        self.page_title.setMinimumWidth(132)
        header_layout.addWidget(self.page_title)

        header_layout.addStretch(1)

        self.header_link_status = QLabel("● LINK: SIMULATED")
        self.header_link_status.setObjectName("headerReadout")
        self.header_link_status.setProperty("state", "nominal")
        header_layout.addWidget(self.header_link_status)

        self.header_mode_status = QLabel("SIMULATED STREAM")
        self.header_mode_status.setObjectName("headerMode")
        header_layout.addWidget(self.header_mode_status)

        self.header_rate_status = QLabel("RATE: 10 Hz")
        self.header_rate_status.setObjectName("headerReadout")
        header_layout.addWidget(self.header_rate_status)

        self.header_rtt_status = QLabel("RTT: -- ms")
        self.header_rtt_status.setObjectName("headerReadout")
        header_layout.addWidget(self.header_rtt_status)

        content_layout.addWidget(header)

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

        # 3D Drone View
        self.drone_view_panel = DroneViewPanel()

        # Separate keyboard test; existing fake-data view remains unchanged.
        self.keyboard_control_panel = KeyboardControlPanel()

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

        # Keep the existing page indexes unchanged by adding this page last.
        self.pages.addWidget(
            self.drone_view_panel
        )

        self.pages.addWidget(
            self.keyboard_control_panel
        )

        content_layout.addWidget(
            self.pages
        )

        # --------------------------------------------------
        # STATUS BAR
        # --------------------------------------------------

        status_frame = QFrame()
        status_frame.setObjectName("statusBar")

        status_frame.setFixedHeight(32)

        status_layout = QHBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            12,
            0,
            12,
            0,
        )

        self.system_status = QLabel("● ARMED [SIMULATION READY]")
        self.system_status.setObjectName("statusPrimary")
        self.system_status.setStyleSheet("color: #8CB7A1;")
        status_layout.addWidget(self.system_status)

        self.status_battery = QLabel("BATT: SIMULATED")
        self.status_battery.setObjectName("statusMetric")
        status_layout.addWidget(self.status_battery)

        self.status_tof = QLabel("TOF/OF: SIMULATED")
        self.status_tof.setObjectName("statusMetric")
        status_layout.addWidget(self.status_tof)

        status_layout.addStretch()

        self.data_status = QLabel("DATA SOURCE: FAKE TELEMETRY")
        self.data_status.setObjectName("statusMetric")
        status_layout.addWidget(self.data_status)

        self.status_failsafe = QLabel("FAIL-SAFE: SIMULATION ONLY")
        self.status_failsafe.setObjectName("statusWarning")
        status_layout.addWidget(self.status_failsafe)

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

        sidebar.setFixedWidth(248)

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            12,
            14,
            12,
            12,
        )

        sidebar_layout.setSpacing(6)

        # --------------------------------------------------
        # LOGO
        # --------------------------------------------------

        logo = QLabel("⌘  BEE-BRAIN GCS")

        logo.setObjectName(
            "logo"
        )

        logo.setFont(
            self.create_font(
                16,
                True,
            )
        )

        sidebar_layout.addWidget(
            logo
        )

        subtitle = QLabel(
            "Micro-UAV Research Lab v2.4"
        )

        subtitle.setObjectName(
            "sidebarSubtitle"
        )

        sidebar_layout.addWidget(
            subtitle
        )

        subsystem_label = QLabel("SUBSYSTEMS")
        subsystem_label.setObjectName("sidebarSectionLabel")
        sidebar_layout.addSpacing(12)
        sidebar_layout.addWidget(subsystem_label)
        sidebar_layout.addSpacing(4)

        # --------------------------------------------------
        # NAVIGATION BUTTONS
        # --------------------------------------------------

        self.telemetry_button = self.create_nav_button(
            "Telemetry"
        )

        self.control_button = self.create_nav_button(
            "Flight Control"
        )

        self.keyboard_test_button = self.create_nav_button(
            "Keyboard Test"
        )

        self.drone_view_button = self.create_nav_button(
            "3D Drone View"
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

        sidebar_layout.addWidget(
            self.drone_view_button
        )

        sidebar_layout.addWidget(
            self.keyboard_test_button
        )

        sidebar_layout.addStretch()

        # Persistent hardware identity block, matching the Stitch shell.
        sidebar_footer = QFrame()
        sidebar_footer.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(sidebar_footer)
        footer_layout.setContentsMargins(8, 10, 8, 8)
        footer_layout.setSpacing(3)

        node_label = QLabel("NODE ID:  BEE-UAV_0x7A")
        node_label.setObjectName("sidebarFooterValue")
        firmware_label = QLabel("FIRMWARE:  SIMULATED")
        firmware_label.setObjectName("sidebarFooterValue")
        uptime_label = QLabel("UPTIME:  TELEMETRY ACTIVE")
        uptime_label.setObjectName("sidebarFooterValue")
        footer_layout.addWidget(node_label)
        footer_layout.addWidget(firmware_label)
        footer_layout.addWidget(uptime_label)
        sidebar_layout.addWidget(sidebar_footer)

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
            36
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

        elif text == "3D Drone View":
            button.clicked.connect(
                lambda: self.show_page(
                    4,
                    "3D DRONE VIEW",
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
        elif text == "Keyboard Test":
            button.clicked.connect(
                lambda: self.show_page(
                    5,
                    "KEYBOARD CONTROL TEST",
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

        self.page_title.setText(title.upper())

        self.update_navigation(
            button
        )
        if index == 5:
            self.keyboard_control_panel.activate_controls()

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
            self.drone_view_button,
            self.keyboard_test_button,
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

            # Keep shell readouts synchronized with the existing telemetry packet.
            link_label = "● LINK: CONNECTED" if packet.link_ok else "● LINK: DISCONNECTED"
            self.header_link_status.setText(link_label)
            self.header_link_status.setProperty(
                "state", "nominal" if packet.link_ok else "fault"
            )
            self.header_link_status.style().unpolish(self.header_link_status)
            self.header_link_status.style().polish(self.header_link_status)

            self.header_rate_status.setText("RATE: 10 Hz")
            self.status_battery.setText(f"BATT: {packet.battery_v:.2f} V")
            tof_state = "LOCK" if packet.sensor_status.tof else "ERROR"
            flow_state = "TRACKING" if packet.sensor_status.optical_flow else "ERROR"
            self.status_tof.setText(f"TOF: {tof_state}  |  FLOW: {flow_state}")

            # Update telemetry page
            self.telemetry_panel.update_telemetry(
                packet
            )

            # Update Flight Control with the latest validated packet.
            self.control_panel.update_telemetry(packet)

            # Keep the drone-view metrics synchronized with telemetry.
            self.drone_view_panel.update_telemetry(packet)

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
                    "color: #8CB7A1;"
                )
            else:
                self.diagnostics_panel.link_status.setText(
                    "● DISCONNECTED"
                )

                self.diagnostics_panel.link_status.setStyleSheet(
                    "color: #D95D50;"
                )

            # Update ToF diagnostics
            if packet.sensor_status.tof:
                self.diagnostics_panel.tof_status.setText(
                    "● OK"
                )

                self.diagnostics_panel.tof_status.setStyleSheet(
                    "color: #8CB7A1;"
                )
            else:
                self.diagnostics_panel.tof_status.setText(
                    "● ERROR"
                )

                self.diagnostics_panel.tof_status.setStyleSheet(
                    "color: #D95D50;"
                )

            # Update optical-flow diagnostics
            if packet.sensor_status.optical_flow:
                self.diagnostics_panel.optical_flow_status.setText(
                    "● OK"
                )

                self.diagnostics_panel.optical_flow_status.setStyleSheet(
                    "color: #8CB7A1;"
                )
            else:
                self.diagnostics_panel.optical_flow_status.setText(
                    "● ERROR"
                )

                self.diagnostics_panel.optical_flow_status.setStyleSheet(
                    "color: #D95D50;"
                )

            # Update battery diagnostics
            battery = packet.battery_v

            self.diagnostics_panel.battery_status.setText(
                f"{battery:.2f} V"
            )

            if battery > 3.7:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #8CB7A1;"
                )

                self.diagnostics_panel.power_status.setText(
                    "HEALTHY"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #8CB7A1;"
                )

            elif battery > 3.4:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #E6BD67;"
                )

                self.diagnostics_panel.power_status.setText(
                    "WARNING"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #E6BD67;"
                )

            else:
                self.diagnostics_panel.battery_status.setStyleSheet(
                    "color: #D95D50;"
                )

                self.diagnostics_panel.power_status.setText(
                    "CRITICAL"
                )

                self.diagnostics_panel.power_status.setStyleSheet(
                    "color: #D95D50;"
                )

        except Exception as error:  # noqa: BLE001
            self.system_status.setText(
                "● SYSTEM ERROR"
            )

            self.system_status.setStyleSheet(
                "color: #D95D50;"
            )

            self.diagnostics_panel.system_status.setText(
                "ERROR"
            )

            self.diagnostics_panel.system_status.setStyleSheet(
                "color: #D95D50;"
            )

            self.diagnostics_panel.diagnostic_message.setText(
                str(error)
            )

            self.diagnostics_panel.diagnostic_message.setStyleSheet(
                "color: #D95D50;"
            )

    # ======================================================
    # FONT HELPER
    # ======================================================

    def create_font(
        self,
        size,
        bold=False,
    ):
        from dashboard.ui.theme import get_ui_font
        return get_ui_font(size, bold)

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
    from dashboard.ui.theme import apply_theme
    apply_theme(app)


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