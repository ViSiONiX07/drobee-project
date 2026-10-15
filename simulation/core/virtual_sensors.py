"""
Bee-Brain Virtual Sensors Module.

Simulates onboard hardware sensors for the micro-drone:
- VL53L0X downward-facing time-of-flight (ToF) distance sensor (in cm).
- ADNS3080 downward-facing optical-flow sensor (drift X/Y measurements).
- Battery voltage monitoring with load response.
- Generates telemetry dicts compatible with the existing Pydantic telemetry contract.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from simulation.core.drone_state import DroneState
from simulation.core.motor_model import MotorModel


@dataclass
class SensorConfig:
    """Configuration parameters and error models for virtual sensors."""
    tof_noise_std: float = 0.5          # ToF measurement noise standard deviation in cm
    tof_max_range_cm: float = 200.0     # Maximum measurable range for VL53L0X (2m)
    tof_failure_rate: float = 0.0       # Probability of sensor dropout/failure

    optical_flow_noise_std: float = 0.1 # Optical flow measurement noise standard deviation
    optical_flow_scale: float = 1.0     # Scaling factor mapping velocity to pixel displacement

    nominal_battery_v: float = 4.2      # Fully charged LiPo voltage
    depleted_battery_v: float = 3.3     # Cutoff voltage
    battery_sag_coefficient: float = 0.2# Voltage drop under motor load


class VirtualSensors:
    """Simulates physical sensors based on true drone state and motor load."""

    def __init__(self, config: SensorConfig | None = None, seed: int | None = None) -> None:
        self.config = config or SensorConfig()
        self._rng = np.random.default_rng(seed)
        self._current_voltage = self.config.nominal_battery_v

    def measure_tof(self, state: DroneState) -> float:
        """
        Simulates VL53L0X downward Time-of-Flight distance sensor.
        Returns distance to ground in centimetres.
        """
        # Altitude is in metres; convert to cm
        true_altitude_cm = state.altitude * 100.0

        # Check range limits
        if true_altitude_cm > self.config.tof_max_range_cm or true_altitude_cm < 0.0:
            return -1.0  # Out of range indicator

        # Simulate random failure/dropout if failure rate > 0
        if self.config.tof_failure_rate > 0.0 and self._rng.random() < self.config.tof_failure_rate:
            return -1.0

        # Add Gaussian noise
        noise = self._rng.normal(0.0, self.config.tof_noise_std)
        measured = true_altitude_cm + noise
        return float(max(0.0, measured))

    def measure_optical_flow(self, state: DroneState, dt: float) -> tuple[float, float]:
        """
        Simulates ADNS3080 downward optical flow sensor measuring drift (X, Y).
        Returns pixel/displacement deltas proportional to ground velocity.
        """
        # Optical flow measures surface displacement integrated over time (velocity * dt * scale)
        vx, vy = state.velocity[0], state.velocity[1]

        dx = vx * dt * self.config.optical_flow_scale + self._rng.normal(0.0, self.config.optical_flow_noise_std * dt)
        dy = vy * dt * self.config.optical_flow_scale + self._rng.normal(0.0, self.config.optical_flow_noise_std * dt)

        return float(dx), float(dy)

    def measure_battery(self, motors: MotorModel, dt: float) -> float:
        """
        Simulates battery discharge and voltage sag under motor load.
        """
        # Calculate total motor load [0.0 to 1.0 average]
        avg_throttle = float(np.mean(motors.motor_speeds))

        # Voltage sag proportional to load
        target_voltage = self.config.nominal_battery_v - (self.config.nominal_battery_v - self.config.depleted_battery_v) * 0.1 - (avg_throttle * self.config.battery_sag_coefficient)

        # Smooth voltage change over time
        self._current_voltage += (target_voltage - self._current_voltage) * min(1.0, dt * 2.0)
        return float(np.clip(self._current_voltage, self.config.depleted_battery_v, self.config.nominal_battery_v))

    def generate_telemetry_packet(self, state: DroneState, motors: MotorModel, dt: float) -> dict:
        """
        Generates a telemetry dictionary matching the exact project Pydantic contract:
        - altitude_cm
        - drift_x
        - drift_y
        - battery_v
        - motor_pwm (list or average PWM representation)
        - link_ok
        - sensor_status.tof
        - sensor_status.optical_flow
        """
        tof_cm = self.measure_tof(state)
        dx, dy = self.measure_optical_flow(state, dt)
        battery = self.measure_battery(motors, dt)

        # Convert normalized motor speeds [0, 1] to approximate PWM values [1000, 2000]
        motor_pwm_vals = [int(1000 + speed * 1000) for speed in motors.motor_speeds]

        return {
            "altitude_cm": tof_cm,
            "drift_x": dx,
            "drift_y": dy,
            "battery_v": battery,
            "motor_pwm": motor_pwm_vals,
            "link_ok": True,
            "sensor_status": {
                "tof": tof_cm >= 0.0,
                "optical_flow": True
            }
        }