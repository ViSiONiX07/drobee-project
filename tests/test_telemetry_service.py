"""Unit tests for PR #5's extended telemetry contract and service statistics."""

import json

import pytest
from pydantic import ValidationError

from dashboard.services.telemetry import (
    BatteryTelemetry,
    CommunicationTelemetry,
    FlightTelemetry,
    IMUTelemetry,
    MotorTelemetry,
    OpticalFlowTelemetry,
    SensorStatus,
    SystemTelemetry,
    TelemetryPacket,
    TelemetryService,
    ToFTelemetry,
)


def test_original_contract_does_not_invent_optional_measurements(telemetry_data):
    packet = TelemetryPacket.model_validate_json(json.dumps(telemetry_data))

    assert packet.model_dump(exclude_none=True) == telemetry_data
    for field in (
        "timestamp_s", "sequence", "tof", "optical_flow", "imu", "flight",
        "battery", "motors", "communications", "system",
    ):
        assert getattr(packet, field) is None
    assert packet.sensor_status.imu is None
    assert packet.sensor_status.barometer is None


def test_extended_packet_round_trips_without_losing_measurements(telemetry_data):
    extended = {
        **telemetry_data,
        "timestamp_s": 123.5,
        "sequence": 17,
        "sensor_status": {
            "tof": True, "optical_flow": False, "imu": True, "barometer": False,
        },
        "tof": {"distance_mm": 1428, "signal_rate": 0.8, "measurement_valid": True},
        "optical_flow": {
            "delta_x": -2.5, "delta_y": 1.2,
            "velocity_x_cm_s": -3.5, "velocity_y_cm_s": 2,
            "quality": 0.75, "tracking_ok": False,
        },
        "imu": {
            "roll_deg": -12, "pitch_deg": 8, "yaw_deg": 350,
            "gyro_x_dps": -1, "gyro_y_dps": 2, "gyro_z_dps": 3,
            "accel_x_m_s2": -0.5, "accel_y_m_s2": 0, "accel_z_m_s2": 9.81,
        },
        "flight": {
            "target_altitude_cm": 150, "altitude_error_cm": -7.2,
            "vertical_velocity_cm_s": -2, "roll_deg": -12,
            "pitch_deg": 8, "yaw_deg": 350, "armed": False, "flight_mode": "HOVER",
        },
        "battery": {
            "voltage_v": 3.85, "current_a": 0.5, "power_w": 1.925,
            "state_of_charge_pct": 70, "temperature_c": -5,
        },
        "motors": {"pwm": [0, 1, 255, 65535], "rpm": [0, 120, 130, 140]},
        "communications": {
            "link_ok": False, "packet_rate_hz": 10, "latency_ms": 2.5,
            "rssi_dbm": -70, "packets_received": 10, "packets_dropped": 1,
            "packet_loss_pct": 10,
        },
        "system": {
            "uptime_s": 50, "loop_rate_hz": 100, "processing_time_ms": 2,
            "error_count": 1, "warning_count": 2,
        },
    }

    packet = TelemetryService().add_packet(json.dumps(extended))

    assert packet.model_dump(exclude_none=True) == extended
    assert TelemetryPacket.model_validate_json(packet.model_dump_json()) == packet


@pytest.mark.parametrize("field", [
    "altitude_cm", "drift_x", "drift_y", "battery_v", "motor_pwm",
    "link_ok", "sensor_status",
])
def test_original_fields_remain_required(telemetry_data, field):
    del telemetry_data[field]
    with pytest.raises(ValidationError) as error:
        TelemetryPacket.model_validate(telemetry_data)
    assert error.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("model,required", [
    (SensorStatus, {"tof": True, "optical_flow": True}),
    (ToFTelemetry, {}),
    (OpticalFlowTelemetry, {}),
    (IMUTelemetry, {}),
    (FlightTelemetry, {}),
    (BatteryTelemetry, {"voltage_v": 3.8}),
    (MotorTelemetry, {"pwm": [0, 0, 0, 0]}),
    (CommunicationTelemetry, {"link_ok": True}),
    (SystemTelemetry, {}),
])
def test_nested_models_reject_unknown_fields(model, required):
    with pytest.raises(ValidationError) as error:
        model.model_validate({**required, "misspelled_measurement": 1})
    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_packet_rejects_unknown_top_level_fields(telemetry_data):
    with pytest.raises(ValidationError) as error:
        TelemetryPacket.model_validate({**telemetry_data, "altitdue_cm": 10})
    assert error.value.errors()[0]["loc"] == ("altitdue_cm",)
    assert error.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("field", ["tof", "optical_flow"])
def test_sensor_health_flags_remain_required(telemetry_data, field):
    del telemetry_data["sensor_status"][field]
    with pytest.raises(ValidationError) as error:
        TelemetryPacket.model_validate(telemetry_data)
    assert error.value.errors()[0]["loc"] == ("sensor_status", field)


@pytest.mark.parametrize("nested", [False, True], ids=["legacy", "extended"])
@pytest.mark.parametrize("pwm", [[], [0] * 3, [0] * 5, [-1, 0, 0, 0], [0, 0, 0, 65536]])
def test_motor_commands_require_four_unsigned_16_bit_values(make_packet, nested, pwm):
    overrides = {"motors": {"pwm": pwm}} if nested else {"motor_pwm": pwm}
    with pytest.raises(ValidationError):
        make_packet(**overrides)


def test_motor_command_endpoints_are_inclusive(make_packet):
    packet = make_packet(
        motor_pwm=[0, 65535, 1, 65534],
        motors={"pwm": [65535, 0, 65534, 1]},
    )
    assert packet.motor_pwm == [0, 65535, 1, 65534]
    assert packet.motors.pwm == [65535, 0, 65534, 1]
    assert packet.motors.rpm is None


@pytest.mark.parametrize("rpm", [[], [0] * 3, [0] * 5])
def test_optional_rpm_requires_four_readings(rpm):
    with pytest.raises(ValidationError):
        MotorTelemetry(pwm=[0] * 4, rpm=rpm)


@pytest.mark.parametrize("section,field,required", [
    (None, "timestamp_s", {}), (None, "sequence", {}),
    ("tof", "distance_mm", {}), ("tof", "signal_rate", {}),
    ("battery", "voltage_v", {}),
    ("battery", "current_a", {"voltage_v": 3.8}),
    ("battery", "power_w", {"voltage_v": 3.8}),
    ("communications", "packet_rate_hz", {"link_ok": True}),
    ("communications", "latency_ms", {"link_ok": True}),
    ("communications", "packets_received", {"link_ok": True}),
    ("communications", "packets_dropped", {"link_ok": True}),
    ("system", "uptime_s", {}), ("system", "loop_rate_hz", {}),
    ("system", "processing_time_ms", {}), ("system", "error_count", {}),
    ("system", "warning_count", {}),
])
def test_nonnegative_measurements_accept_zero_and_reject_negatives(
    make_packet, section, field, required,
):
    def overrides(value):
        return {section: {**required, field: value}} if section else {field: value}

    packet = make_packet(**overrides(0))
    target = getattr(packet, section) if section else packet
    assert getattr(target, field) == 0

    with pytest.raises(ValidationError) as error:
        make_packet(**overrides(-1))
    location = (section, field) if section else (field,)
    assert error.value.errors()[0]["loc"] == location


@pytest.mark.parametrize("section,field,maximum,required", [
    ("optical_flow", "quality", 1, {}),
    ("battery", "state_of_charge_pct", 100, {"voltage_v": 3.8}),
    ("communications", "packet_loss_pct", 100, {"link_ok": True}),
])
def test_bounded_measurements_accept_endpoints_and_reject_outside_values(
    make_packet, section, field, maximum, required,
):
    for value in (0, maximum):
        packet = make_packet(**{section: {**required, field: value}})
        assert getattr(getattr(packet, section), field) == value
    for value in (-0.01, maximum + 0.01):
        with pytest.raises(ValidationError):
            make_packet(**{section: {**required, field: value}})


@pytest.mark.parametrize("maxlen", [0, -1])
def test_history_capacity_must_be_positive(maxlen):
    with pytest.raises(ValueError, match="maxlen must be at least 1"):
        TelemetryService(maxlen=maxlen)


def test_empty_service_statistics():
    service = TelemetryService()
    assert service.get_latest() is None
    assert service.get_history() == []
    assert service.get_stats() == {
        "history_size": 0, "history_capacity": 500, "received_count": 0,
        "validation_errors": 0, "last_packet_age_s": None,
    }


@pytest.mark.parametrize("capacity", [1, 2])
def test_bounded_history_is_chronological_and_counts_all_valid_packets(telemetry_data, capacity):
    service = TelemetryService(maxlen=capacity)
    packets = [
        service.add_packet(json.dumps({**telemetry_data, "sequence": index}))
        for index in range(4)
    ]

    assert service.get_history() == packets[-capacity:]
    assert service.get_latest() is packets[-1]
    assert service.get_stats()["received_count"] == 4
    assert service.get_stats()["history_size"] == capacity
    assert service.get_stats()["history_capacity"] == capacity

    history = service.get_history()
    history.clear()
    assert service.get_history() == packets[-capacity:]


@pytest.mark.parametrize("invalid", [None, b"{}", {}, 42, "", "not-json", "[]", "null", "{}"])
def test_rejected_input_preserves_latest_packet_and_arrival_time(
    telemetry_data, monkeypatch, invalid,
):
    now = 10.0
    monkeypatch.setattr("dashboard.services.telemetry.time.monotonic", lambda: now)
    service = TelemetryService()
    packet = service.add_packet(json.dumps(telemetry_data))
    now = 12.5

    with pytest.raises(ValueError, match="JSON telemetry|Malformed or invalid telemetry packet"):
        service.add_packet(invalid)

    assert service.get_latest() is packet
    assert service.get_history() == [packet]
    assert service.get_stats() == {
        "history_size": 1, "history_capacity": 500, "received_count": 1,
        "validation_errors": 1, "last_packet_age_s": 2.5,
    }


def test_validation_failure_preserves_cause_and_next_valid_packet_recovers(telemetry_data):
    service = TelemetryService()
    with pytest.raises(ValueError) as error:
        service.add_packet(json.dumps({**telemetry_data, "motor_pwm": [0, 0, 0, -1]}))
    assert isinstance(error.value.__cause__, ValidationError)
    assert service.get_latest() is None
    assert service.get_stats()["last_packet_age_s"] is None

    packet = service.add_packet(json.dumps(telemetry_data))
    assert service.get_latest() is packet
    assert service.get_stats()["received_count"] == 1
    assert service.get_stats()["validation_errors"] == 1


def test_clear_history_preserves_counters_and_age_until_next_packet(telemetry_data, monkeypatch):
    now = 100.0
    monkeypatch.setattr("dashboard.services.telemetry.time.monotonic", lambda: now)
    service = TelemetryService(maxlen=1)
    service.add_packet(json.dumps(telemetry_data))
    with pytest.raises(ValueError):
        service.add_packet("invalid")
    now = 103.0

    service.clear_history()
    service.clear_history()

    assert service.get_latest() is None
    assert service.get_history() == []
    assert service.get_stats() == {
        "history_size": 0, "history_capacity": 1, "received_count": 1,
        "validation_errors": 1, "last_packet_age_s": 3.0,
    }
    service.add_packet(json.dumps(telemetry_data))
    assert service.get_stats()["last_packet_age_s"] == 0.0
    assert service.get_stats()["received_count"] == 2
