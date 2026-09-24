# Bee-Brain Telemetry Protocol Specification

This document defines the unified telemetry JSON contract used across the ESP32-S3 firmware, Webots simulator, and PySide6 Dashboard.

## Baseline Telemetry Schema

```json
{
    "altitude_cm": 0.0,
    "drift_x": 0.0,
    "drift_y": 0.0,
    "battery_v": 0.0,
    "motor_pwm": [0, 0, 0, 0],
    "link_ok": true,
    "sensor_status": {
        "tof": true,
        "optical_flow": true
    }
}
```

## Field Definitions

| Field Key | Type | Unit | Description |
|---|---|---|---|
| `altitude_cm` | `float` | cm | Distance to ground measured by downward VL53L0X / TOF200C ToF sensor |
| `drift_x` | `float` | px/s or cm/s | Horizontal displacement/flow vector along X-axis from ADNS3080 |
| `drift_y` | `float` | px/s or cm/s | Horizontal displacement/flow vector along Y-axis from ADNS3080 |
| `battery_v` | `float` | Volts | 1S LiPo voltage read via resistor divider on ESP32-S3 ADC pin |
| `motor_pwm` | `array[int]` | 0-255 | PWM duty cycle array for 4x 8520 coreless motors `[M1, M2, M3, M4]` |
| `link_ok` | `bool` | - | Health indicator of serial/Wi-Fi connection |
| `sensor_status.tof` | `bool` | - | Hardware initialization & range validity status of VL53L0X |
| `sensor_status.optical_flow` | `bool` | - | Hardware initialization & surface tracking status of ADNS3080 |

## Transmission Transport

- **Serial Mode**: 115200 baud newline-delimited JSON (`\n`).
- **UDP Broadcast / Wi-Fi**: JSON payload on port `8888`.
- **Frequency**: 20 Hz to 50 Hz.
