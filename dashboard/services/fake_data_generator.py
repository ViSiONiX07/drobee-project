import random
from typing import Callable, Optional

from PySide6.QtCore import QTimer, QObject

from dashboard.services.telemetry import TelemetryPacket, SensorStatus


class FakeTelemetryGenerator(QObject):
    """
    Simulates drone telemetry data for dashboard development without hardware or Webots.
    Provides QTimer-based periodic generation.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        self._callback: Optional[Callable[[str], None]] = None

        # Internal state
        self.altitude_cm = 50.0
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.battery_v = 4.2
        self.motor_pwm = [150, 150, 150, 150]
        self.link_ok = True
        self.tof_ok = True
        self.of_ok = True

    def start(self, callback: Callable[[str], None], interval_ms: int = 100) -> None:
        """Starts the periodic generation of fake telemetry."""
        self._callback = callback
        self.timer.start(interval_ms)

    def stop(self) -> None:
        """Stops the periodic generation."""
        self.timer.stop()
        self._callback = None

    def _on_timeout(self) -> None:
        if self._callback:
            self._callback(self.generate())

    def generate(self) -> str:
        """Generates a single telemetry payload string reflecting evolved internal state."""
        # 1. altitude_cm: stable hover, small realistic noise
        self.altitude_cm += random.uniform(-0.5, 0.5)
        self.altitude_cm = max(0.0, self.altitude_cm)

        # 2. drift_x and drift_y: keep near zero, occasional gentle drift
        if random.random() < 0.1:
            self.drift_x += random.uniform(-1.0, 1.0)
            self.drift_y += random.uniform(-1.0, 1.0)
        else:
            self.drift_x *= 0.9
            self.drift_y *= 0.9

        # 3. battery_v: decrease slowly, approach 3.5V
        if self.battery_v > 3.5:
            self.battery_v -= random.uniform(0.0001, 0.0005)

        # 4. motor_pwm: around hover baseline (150)
        self.motor_pwm = [
            max(0, min(255, int(150 + random.gauss(0, 5))))
            for _ in range(4)
        ]

        # 5. link_ok: occasionally simulate short communication dropout
        if self.link_ok:
            if random.random() < 0.01:
                self.link_ok = False
        else:
            if random.random() < 0.2:
                self.link_ok = True

        # 6. sensor_status: occasionally simulate brief sensor failure
        if self.tof_ok:
            if random.random() < 0.005:
                self.tof_ok = False
        else:
            if random.random() < 0.1:
                self.tof_ok = True

        if self.of_ok:
            if random.random() < 0.005:
                self.of_ok = False
        else:
            if random.random() < 0.1:
                self.of_ok = True

        packet = TelemetryPacket(
            altitude_cm=round(self.altitude_cm, 2),
            drift_x=round(self.drift_x, 2),
            drift_y=round(self.drift_y, 2),
            battery_v=round(self.battery_v, 3),
            motor_pwm=self.motor_pwm,
            link_ok=self.link_ok,
            sensor_status=SensorStatus(
                tof=self.tof_ok,
                optical_flow=self.of_ok
            )
        )
        return packet.model_dump_json()
