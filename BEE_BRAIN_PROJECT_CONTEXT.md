# Bee-Brain Project Context & Technical Baseline

## 1. Project Identity
Bee-Brain (Drobee) is a bio-inspired, GPS-free indoor micro-drone platform designed for autonomous hover, altitude hold, and horizontal drift stabilization.

## 2. Hardware Architecture
- **Microcontroller**: Seeed XIAO ESP32-S3 (Dual-core LX7, 240 MHz, Wi-Fi/BLE, mounted on female header perfboard carrier)
- **Altitude Sensor**: Downward VL53L0X / TOF200C Time-of-Flight (ToF) laser rangefinder
- **Optical-Flow Sensor**: Downward ADNS3080 optical-flow sensor
- **Actuators**: 4x 8520 coreless DC motors driven by N-channel MOSFET stage
- **Power**: 1S LiPo battery (3.7V nominal)
- **Bench Room Scanner**: SG90 servo pan-tilt scanner rig mounted on a **bench laboratory fixture** (NOT carried on the drone)

## 3. Sensing Architecture & Flight Ownership
- **Altitude Estimation**: VL53L0X downward distance measurements $\rightarrow$ Altitude PID loop
- **Drift Estimation**: ADNS3080 optical flow displacement $\rightarrow$ Lateral PID loop
- **Flight Control Ownership**: The ESP32-S3 microcontroller owns all real-time flight-critical control logic (sensor reading, altitude estimation, drift estimation, PID loops, motor mixing, failsafe safety logic).
- **Dashboard Role**: Visualization, telemetry monitoring, diagnostics, point-cloud mapping, and simulation interaction. The dashboard does NOT directly control flight motors.
- **IMU Policy**: An Inertial Measurement Unit (IMU) is an OPTIONAL future enhancement. The current dual-sensor architecture is intentionally sufficient for indoor hover stability and drift correction.

## 4. Bio-Inspired Algorithms
- **Reichardt / EMD Detector**: Spatio-temporal motion correlation model inspired by insect visual systems for optical flow filtering.
- **LGMD Looming Detector**: Angular expansion rate model inspired by locust visual neurons for proximity detection and emergency disarm.
- **Non-Overclaim Rule**: Bee-Brain utilizes visual motion algorithms inspired by insect vision. It does NOT simulate a 166,700-neuron insect brain or run a biological connectome on the ESP32-S3.

## 5. Software Stack & Interfaces
- **Firmware**: C++, PlatformIO, ESP32-S3, FreeRTOS
- **Simulation**: Webots simulator, Python controller (`simulation/controllers/drone_controller/drone_controller.py`)
- **Dashboard**: Python, PySide6 (`dashboard/app.py`)
- **Mapping**: Open3D sensor-based point-cloud acquisition and 3D reconstruction (`dashboard/mapping/`)
- **Database**: SQLite (`dashboard/database/db.py`)
- **Telemetry**: Unified JSON telemetry broadcast over Serial / Wi-Fi UDP at 20-50 Hz

## 6. Telemetry Contract Specification
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

## 7. Development Scaffold Policy
All source-code files in `firmware/src/`, `dashboard/`, `simulation/controllers/`, `cad/scripts/`, and `tests/integration/` serve as architectural placeholder scaffolds for modular developer implementation.
