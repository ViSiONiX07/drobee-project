# Main PySide6 dashboard window implementation goes here.
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow

from dashboard.services.fake_data_generator import FakeTelemetryGenerator
from dashboard.services.telemetry import TelemetryService
from dashboard.ui.telemetry_panel import TelemetryPanel


class MainWindow(QMainWindow):
    """Main window for the Bee-Brain dashboard."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bee-Brain")
        self.resize(1000, 700)

        # -----------------------------------------
        # Telemetry components
        # -----------------------------------------

        self.telemetry_service = TelemetryService()

        self.telemetry_generator = FakeTelemetryGenerator(self)

        self.telemetry_panel = TelemetryPanel()

        self.setCentralWidget(self.telemetry_panel)

        # -----------------------------------------
        # Telemetry update timer
        # -----------------------------------------

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(100)

    def update_telemetry(self):
        """
        Generate fake telemetry, validate it through
        TelemetryService, then update the UI.
        """

        # Fake generator produces raw JSON
        raw_json = self.telemetry_generator.generate()

        # TelemetryService validates and converts JSON
        # into the official TelemetryPacket model.
        packet = self.telemetry_service.add_packet(raw_json)

        # Send validated packet to the UI.
        self.telemetry_panel.update_telemetry(packet)

    def closeEvent(self, event):
        """Cleanly stop telemetry updates when the window closes."""

        if self.telemetry_timer.isActive():
            self.telemetry_timer.stop()

        event.accept()


def main():
    """Application entry point."""

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()