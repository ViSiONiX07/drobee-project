from collections import deque
from pydantic import BaseModel, ConfigDict

class SensorStatus(BaseModel):
    """Pydantic model representing individual sensor status indicators."""
    model_config = ConfigDict(extra="forbid")

    tof: bool
    optical_flow: bool


class TelemetryPacket(BaseModel):
    """Pydantic model representing a unified Bee-Brain telemetry packet.
    
    Matches the official protocol specification in docs/telemetry/telemetry-spec.md.
    """
    model_config = ConfigDict(extra="forbid")

    altitude_cm: float
    drift_x: float
    drift_y: float
    battery_v: float
    motor_pwm: list[int]
    link_ok: bool
    sensor_status: SensorStatus


class TelemetryService:
    """Service for processing, validating, and storing telemetry packets."""

    def __init__(self, maxlen: int = 500) -> None:
        self._history: deque[TelemetryPacket] = deque(maxlen=maxlen)

    def add_packet(self, raw_json: str) -> TelemetryPacket:
        """Parses a raw JSON telemetry string, validates it using TelemetryPacket,

        appends it to history if valid, and returns the parsed TelemetryPacket.

        Raises:
            ValueError: If the raw JSON is malformed or violates the telemetry spec.
        """
        if not isinstance(raw_json, str):
            raise ValueError("raw_json must be a string containing JSON telemetry data.")
        try:
            packet = TelemetryPacket.model_validate_json(raw_json)
        except Exception as e:
            raise ValueError(f"Malformed or invalid telemetry packet: {e}") from e

        self._history.append(packet)
        return packet

    def get_latest(self) -> TelemetryPacket | None:
        """Returns the most recent valid TelemetryPacket, or None if history is empty."""
        return self._history[-1] if self._history else None

    def get_history(self) -> list[TelemetryPacket]:
        """Returns a list of stored valid TelemetryPackets in chronological order."""
        return list(self._history)
