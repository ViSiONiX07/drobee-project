"""
Unit tests for simulation.core.motor_model.MotorModel.
"""

import numpy as np
import pytest

from simulation.core.motor_model import MotorConfig, MotorModel


class TestMotorModel:
    def test_initial_speeds_zero(self):
        motors = MotorModel()
        np.testing.assert_array_equal(motors.motor_speeds, [0.0, 0.0, 0.0, 0.0])

    def test_direct_speed_setting(self):
        motors = MotorModel()
        motors.set_motor_speeds_direct([0.2, 0.4, 0.6, 0.8])
        np.testing.assert_array_equal(motors._target_speeds, [0.2, 0.4, 0.6, 0.8])

    def test_first_order_response_delay(self):
        config = MotorConfig(time_constant=0.1)
        motors = MotorModel(config)
        motors.set_motor_speeds_direct([1.0, 1.0, 1.0, 1.0])

        # Step for a fraction of time constant
        motors.step(dt=0.1)
        # With alpha = 0.1 / (0.1 + 0.1) = 0.5, speed should be ~0.5
        np.testing.assert_allclose(motors.motor_speeds, [0.5, 0.5, 0.5, 0.5], atol=1e-2)

    def test_mixer_throttle(self):
        motors = MotorModel()
        motors.set_commands(throttle=0.5, roll=0.0, pitch=0.0, yaw=0.0)
        np.testing.assert_allclose(motors._target_speeds, [0.5, 0.5, 0.5, 0.5])

    def test_total_thrust(self):
        config = MotorConfig(max_thrust=2.0, thrust_coefficient=1.0, time_constant=0.0)
        motors = MotorModel(config)
        motors.set_motor_speeds_direct([0.5, 0.5, 0.5, 0.5])
        motors.step(dt=0.01)

        # 4 motors * (0.5 * 2.0 * 1.0) = 4.0 N total thrust
        assert motors.get_total_thrust() == pytest.approx(4.0)

    def test_reset(self):
        motors = MotorModel()
        motors.set_motor_speeds_direct([1.0, 1.0, 1.0, 1.0])
        motors.step(dt=0.1)
        motors.reset()
        np.testing.assert_array_equal(motors.motor_speeds, [0.0, 0.0, 0.0, 0.0])