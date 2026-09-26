from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class DiagnosticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # ==================================================
        # TITLE
        # ==================================================

        title = QLabel("DIAGNOSTICS")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)

        subtitle = QLabel(
            "Bee-Brain system diagnostics"
        )

        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888888;")

        layout.addWidget(subtitle)

        # ==================================================
        # SYSTEM STATUS
        # ==================================================

        system_frame = self.create_section(
            "SYSTEM STATUS"
        )

        system_layout = QGridLayout()
        system_layout.setContentsMargins(5, 5, 5, 5)
        system_layout.setVerticalSpacing(8)

        self.system_status = self.create_value("READY")
        self.system_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.app_status = self.create_value("RUNNING")
        self.app_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.data_source = self.create_value(
            "FAKE DATA"
        )
        self.data_source.setStyleSheet(
            "color: #00ccff;"
        )

        system_layout.addWidget(
            QLabel("SYSTEM"),
            0,
            0,
        )

        system_layout.addWidget(
            self.system_status,
            0,
            1,
            alignment=Qt.AlignRight,
        )

        system_layout.addWidget(
            QLabel("APPLICATION"),
            1,
            0,
        )

        system_layout.addWidget(
            self.app_status,
            1,
            1,
            alignment=Qt.AlignRight,
        )

        system_layout.addWidget(
            QLabel("DATA SOURCE"),
            2,
            0,
        )

        system_layout.addWidget(
            self.data_source,
            2,
            1,
            alignment=Qt.AlignRight,
        )

        system_frame.layout().addLayout(
            system_layout
        )

        layout.addWidget(system_frame)

        # ==================================================
        # SENSOR DIAGNOSTICS
        # ==================================================

        sensor_frame = self.create_section(
            "SENSOR DIAGNOSTICS"
        )

        sensor_layout = QGridLayout()
        sensor_layout.setContentsMargins(5, 5, 5, 5)
        sensor_layout.setVerticalSpacing(8)

        self.tof_status = self.create_value("● OK")
        self.tof_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.optical_flow_status = self.create_value(
            "● OK"
        )
        self.optical_flow_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.imu_status = self.create_value(
            "● NOT CONNECTED"
        )
        self.imu_status.setStyleSheet(
            "color: #888888;"
        )

        sensor_layout.addWidget(
            QLabel("ToF SENSOR"),
            0,
            0,
        )

        sensor_layout.addWidget(
            self.tof_status,
            0,
            1,
            alignment=Qt.AlignRight,
        )

        sensor_layout.addWidget(
            QLabel("OPTICAL FLOW"),
            1,
            0,
        )

        sensor_layout.addWidget(
            self.optical_flow_status,
            1,
            1,
            alignment=Qt.AlignRight,
        )

        sensor_layout.addWidget(
            QLabel("IMU"),
            2,
            0,
        )

        sensor_layout.addWidget(
            self.imu_status,
            2,
            1,
            alignment=Qt.AlignRight,
        )

        sensor_frame.layout().addLayout(
            sensor_layout
        )

        layout.addWidget(sensor_frame)

        # ==================================================
        # COMMUNICATION
        # ==================================================

        communication_frame = self.create_section(
            "COMMUNICATION"
        )

        communication_layout = QGridLayout()
        communication_layout.setContentsMargins(
            5, 5, 5, 5
        )
        communication_layout.setVerticalSpacing(8)

        self.link_status = self.create_value(
            "● CONNECTED"
        )
        self.link_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.packet_status = self.create_value(
            "NORMAL"
        )
        self.packet_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.packet_count = self.create_value("0")

        communication_layout.addWidget(
            QLabel("LINK"),
            0,
            0,
        )

        communication_layout.addWidget(
            self.link_status,
            0,
            1,
            alignment=Qt.AlignRight,
        )

        communication_layout.addWidget(
            QLabel("PACKET STATUS"),
            1,
            0,
        )

        communication_layout.addWidget(
            self.packet_status,
            1,
            1,
            alignment=Qt.AlignRight,
        )

        communication_layout.addWidget(
            QLabel("PACKETS RECEIVED"),
            2,
            0,
        )

        communication_layout.addWidget(
            self.packet_count,
            2,
            1,
            alignment=Qt.AlignRight,
        )

        communication_frame.layout().addLayout(
            communication_layout
        )

        layout.addWidget(
            communication_frame
        )

        # ==================================================
        # POWER
        # ==================================================

        power_frame = self.create_section(
            "POWER DIAGNOSTICS"
        )

        power_layout = QGridLayout()
        power_layout.setContentsMargins(
            5, 5, 5, 5
        )
        power_layout.setVerticalSpacing(8)

        self.battery_status = self.create_value(
            "4.20 V"
        )
        self.battery_status.setStyleSheet(
            "color: #00ff99;"
        )

        self.power_status = self.create_value(
            "HEALTHY"
        )
        self.power_status.setStyleSheet(
            "color: #00ff99;"
        )

        power_layout.addWidget(
            QLabel("BATTERY"),
            0,
            0,
        )

        power_layout.addWidget(
            self.battery_status,
            0,
            1,
            alignment=Qt.AlignRight,
        )

        power_layout.addWidget(
            QLabel("POWER STATUS"),
            1,
            0,
        )

        power_layout.addWidget(
            self.power_status,
            1,
            1,
            alignment=Qt.AlignRight,
        )

        power_frame.layout().addLayout(
            power_layout
        )

        layout.addWidget(power_frame)

        # ==================================================
        # DIAGNOSTIC ACTIONS
        # ==================================================

        actions_frame = self.create_section(
            "DIAGNOSTIC ACTIONS"
        )

        actions_layout = QVBoxLayout()
        actions_layout.setContentsMargins(
            5, 5, 5, 5
        )
        actions_layout.setSpacing(10)

        # --------------------------------------------------
        # BUTTON ROW
        # --------------------------------------------------

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.run_button = QPushButton(
            "RUN SYSTEM CHECK"
        )

        self.run_button.setMinimumHeight(40)

        self.run_button.clicked.connect(
            self.run_system_check
        )

        self.clear_button = QPushButton(
            "CLEAR STATUS"
        )

        self.clear_button.setMinimumHeight(40)

        self.clear_button.clicked.connect(
            self.clear_status
        )

        button_layout.addWidget(
            self.run_button
        )

        button_layout.addWidget(
            self.clear_button
        )

        actions_layout.addLayout(
            button_layout
        )

        # --------------------------------------------------
        # STATUS MESSAGE
        # --------------------------------------------------

        self.diagnostic_message = QLabel(
            "No diagnostic test running."
        )

        self.diagnostic_message.setMinimumHeight(
            24
        )

        self.diagnostic_message.setAlignment(
            Qt.AlignCenter
        )

        self.diagnostic_message.setStyleSheet(
            "color: #888888;"
        )

        actions_layout.addWidget(
            self.diagnostic_message
        )

        actions_frame.layout().addLayout(
            actions_layout
        )

        layout.addWidget(
            actions_frame
        )

        layout.addStretch()

    # ======================================================
    # SECTION CREATOR
    # ======================================================

    def create_section(self, title_text):
        frame = QFrame()

        frame.setFrameStyle(
            QFrame.StyledPanel |
            QFrame.Raised
        )

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(
            10, 8, 10, 8
        )

        layout.setSpacing(6)

        title = QLabel(title_text)

        title.setFont(
            QFont(
                "Arial",
                10,
                QFont.Bold,
            )
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            "color: #888888;"
        )

        layout.addWidget(title)

        return frame

    # ======================================================
    # VALUE LABEL
    # ======================================================

    def create_value(self, text):
        label = QLabel(text)

        label.setFont(
            QFont(
                "Arial",
                11,
            )
        )

        label.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        return label

    # ======================================================
    # RUN SYSTEM CHECK
    # ======================================================

    def run_system_check(self):
        self.diagnostic_message.setText(
            "SYSTEM CHECK COMPLETE — NO ACTIVE ERRORS"
        )

        self.diagnostic_message.setStyleSheet(
            "color: #00ff99;"
        )

        self.system_status.setText(
            "HEALTHY"
        )

        self.system_status.setStyleSheet(
            "color: #00ff99;"
        )

    # ======================================================
    # CLEAR STATUS
    # ======================================================

    def clear_status(self):
        self.diagnostic_message.setText(
            "Diagnostic status cleared."
        )

        self.diagnostic_message.setStyleSheet(
            "color: #888888;"
        )