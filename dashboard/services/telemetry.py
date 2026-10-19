
"""
Bee-Brain GCS — Telemetry models and service.

Responsibilities:
- Validate incoming JSON telemetry packets with Pydantic.
- Preserve compatibility with the original telemetry contract.
- Support extended flight, sensor, battery, communication,
  motor, and system telemetry.
- Store recent valid packets in a bounded history.

Note:
Optional fields are measurements to be supplied by firmware,
simulation, or explicitly identified estimators. They are not
automatically measured by this service.
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# Sensor status
# ============================================================

class SensorStatus(BaseModel):
    """Health flags for sensors currently used by Bee-Brain."""

    model_config = ConfigDict(extra="forbid")

    tof: bool
    optical_flow: bool

    imu: bool | None = None
    barometer: bool | None = None


# ============================================================
# Sensor measurements
# ============================================================

class ToFTelemetry(BaseModel):
    """Downward time-of-flight sensor measurements."""

    model_config = ConfigDict(extra="forbid")

    distance_mm: float | None = Field(default=None, ge=0)
    signal_rate: float | None = Field(default=None, ge=0)
    measurement_valid: bool | None = None


class OpticalFlowTelemetry(BaseModel):
    """Optical-flow measurements and quality indicators."""

    model_config = ConfigDict(extra="forbid")

    delta_x: float | None = None
    delta_y: float | None = None
    velocity_x_cm_s: float | None = None
    velocity_y_cm_s: float | None = None
    quality: float | None = Field(default=None, ge=0, le=1)
    tracking_ok: bool | None = None


class IMUTelemetry(BaseModel):
    """IMU data; populated only when an IMU is available."""

    model_config = ConfigDict(extra="forbid")

    roll_deg: float | None = None
    pitch_deg: float | None = None
    yaw_deg: float | None = None

    gyro_x_dps: float | None = None
    gyro_y_dps: float | None = None
    gyro_z_dps: float | None = None

    accel_x_m_s2: float | None = None
    accel_y_m_s2: float | None = None
    accel_z_m_s2: float | None = None


# ============================================================
# Flight and altitude control
# ============================================================

class FlightTelemetry(BaseModel):
    """Flight state and altitude-control measurements."""

    model_config = ConfigDict(extra="forbid")

    target_altitude_cm: float | None = None
    altitude_error_cm: float | None = None
    vertical_velocity_cm_s: float | None = None

    # Values must come from an actual attitude estimator or IMU.
    roll_deg: float | None = None
    pitch_deg: float | None = None
    yaw_deg: float | None = None

    armed: bool | None = None
    flight_mode: str | None = None


# ============================================================
# Battery and electrical measurements
# ============================================================

class BatteryTelemetry(BaseModel):
    """Battery measurements and estimated battery state."""

    model_config = ConfigDict(extra="forbid")

    voltage_v: float = Field(ge=0)
    current_a: float | None = Field(default=None, ge=0)
    power_w: float | None = Field(default=None, ge=0)

    # Must come from a suitable estimator or battery monitor.
    state_of_charge_pct: float | None = Field(
        default=None, ge=0, le=100
    )

    temperature_c: float | None = None


# ============================================================
# Motor telemetry
# ============================================================

class MotorTelemetry(BaseModel):
    """Four-motor command and optional feedback information."""

    model_config = ConfigDict(extra="forbid")

    pwm: list[int] = Field(min_length=4, max_length=4)

    # Optional feedback; commands alone do not measure RPM.
    rpm: list[float] | None = Field(
        default=None, min_length=4, max_length=4
    )

    @field_validator("pwm")
    @classmethod
    def validate_pwm(cls, values: list[int]) -> list[int]:
        """Return PWM values unchanged if each is in the inclusive range 0–65535.

        Raise ValueError for an out-of-range value; Pydantic includes this
        failure in its model ValidationError.
        """
        if any(value < 0 or value > 65535 for value in values):
            raise ValueError("Motor PWM values must be between 0 and 65535.")
        return values


# ============================================================
# Communication statistics
# ============================================================

class CommunicationTelemetry(BaseModel):
    """Communication-layer statistics."""

    model_config = ConfigDict(extra="forbid")

    link_ok: bool

    packet_rate_hz: float | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    rssi_dbm: float | None = None

    packets_received: int | None = Field(default=None, ge=0)
    packets_dropped: int | None = Field(default=None, ge=0)
    packet_loss_pct: float | None = Field(
        default=None, ge=0, le=100
    )


# ============================================================
# System diagnostics
# ============================================================

class SystemTelemetry(BaseModel):
    """Runtime and diagnostic counters."""

    model_config = ConfigDict(extra="forbid")

    uptime_s: float | None = Field(default=None, ge=0)
    loop_rate_hz: float | None = Field(default=None, ge=0)
    processing_time_ms: float | None = Field(default=None, ge=0)

    error_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)


# ============================================================
# Complete telemetry packet
# ============================================================

class TelemetryPacket(BaseModel):
    """
    Unified Bee-Brain telemetry packet.

    The original fields remain required. Extended fields are
    optional to allow gradual migration of the simulator/firmware.
    """

    model_config = ConfigDict(extra="forbid")

    # Original protocol fields — retained for compatibility.
    altitude_cm: float
    drift_x: float
    drift_y: float
    battery_v: float
    motor_pwm: list[int]
    link_ok: bool
    sensor_status: SensorStatus

    # Extended measurements.
    timestamp_s: float | None = Field(default=None, ge=0)
    sequence: int | None = Field(default=None, ge=0)

    tof: ToFTelemetry | None = None
    optical_flow: OpticalFlowTelemetry | None = None
    imu: IMUTelemetry | None = None

    flight: FlightTelemetry | None = None
    battery: BatteryTelemetry | None = None
    motors: MotorTelemetry | None = None
    communications: CommunicationTelemetry | None = None
    system: SystemTelemetry | None = None

    @field_validator("motor_pwm")
    @classmethod
    def validate_legacy_pwm(cls, values: list[int]) -> list[int]:
        """Return four PWM values unchanged when each is in the range 0–65535.

        Raise ValueError for a different count or an out-of-range value;
        Pydantic includes these failures in its model ValidationError.
        """
        if len(values) != 4:
            raise ValueError("Exactly four motor PWM values are required.")

        if any(value < 0 or value > 65535 for value in values):
            raise ValueError("Motor PWM values must be between 0 and 65535.")

        return values


# ============================================================
# Telemetry service
# ============================================================

class TelemetryService:
    """Validate, store, and expose recent telemetry packets."""

    def __init__(self, maxlen: int = 500) -> None:
        """Create a history retaining at most maxlen valid packets.

        Raise ValueError if maxlen is less than one. Once full, the history
        discards the oldest packet when a new valid packet arrives.
        """
        if maxlen < 1:
            raise ValueError("maxlen must be at least 1.")

        self._history: deque[TelemetryPacket] = deque(maxlen=maxlen)
        self._validation_errors = 0
        self._received_count = 0
        self._last_received_monotonic: float | None = None

    def add_packet(self, raw_json: str) -> TelemetryPacket:
        """Validate JSON, store the packet, and return it.

        Raise ValueError for a non-string input, malformed JSON, or model
        validation failure, preserving the validation exception as its cause.
        Rejected packets increment the error count without changing history
        or the last valid receipt time. Accepted packets increment the received
        count and evict the oldest entry when history is full.
        """

        if not isinstance(raw_json, str):
            self._validation_errors += 1
            raise ValueError(
                "raw_json must be a string containing JSON telemetry."
            )

        try:
            packet = TelemetryPacket.model_validate_json(raw_json)
        except Exception as exc:
            self._validation_errors += 1
            raise ValueError(
                f"Malformed or invalid telemetry packet: {exc}"
            ) from exc

        self._history.append(packet)
        self._received_count += 1
        self._last_received_monotonic = time.monotonic()

        return packet

    def get_latest(self) -> TelemetryPacket | None:
        """Return the most recent valid packet, or None when history is empty."""

        return self._history[-1] if self._history else None

    def get_history(self) -> list[TelemetryPacket]:
        """Return stored packets in chronological order."""

        return list(self._history)

    def get_stats(self) -> dict[str, Any]:
        """Return history size and capacity, packet counters, and receipt age.

        received_count counts accepted packets and validation_errors counts
        rejected inputs since construction, even after history is cleared.
        last_packet_age_s is elapsed monotonic time in seconds since the last
        accepted packet, or None if no packet has been accepted.
        """

        age_s = None

        if self._last_received_monotonic is not None:
            age_s = time.monotonic() - self._last_received_monotonic

        return {
            "history_size": len(self._history),
            "history_capacity": self._history.maxlen,
            "received_count": self._received_count,
            "validation_errors": self._validation_errors,
            "last_packet_age_s": age_s,
        }

    def clear_history(self) -> None:
        """Clear stored packets without resetting service counters."""

        self._history.clear()
