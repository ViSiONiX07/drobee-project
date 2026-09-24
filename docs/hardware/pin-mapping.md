# Bee-Brain Hardware Pin Mapping

This document details the physical hardware connections between the Seeed XIAO ESP32-S3 micro-controller, downward sensors, motor drivers, battery monitor, and bench-mounted scanning rig.

## Hardware Summary

- **Microcontroller**: Seeed XIAO ESP32-S3 (Dual-core LX7, Wi-Fi/BLE)
- **Altitude Sensor**: VL53L0X / TOF200C downward laser Time-of-Flight sensor
- **Optical Flow Sensor**: ADNS3080 downward optical flow sensor
- **Actuators**: 4x 8520 coreless DC motors with MOSFET gate drivers
- **Power**: 1S LiPo (3.7V nominal, 4.2V max)
- **Scanning Rig**: SG90 servo for BENCH-MOUNTED room-scanning rig (NOT mounted on flying frame)

## Pin Assignment Table

| Subsystem | Peripheral / Pin | Seeed XIAO ESP32-S3 Pin | GPIO Number | Function / Notes |
|---|---|---|---|---|
| **VL53L0X ToF** | I2C SDA | D4 | GPIO 5 | I2C Data line for altitude estimation |
| | I2C SCL | D5 | GPIO 6 | I2C Clock line |
| **ADNS3080 Flow** | SPI SCK | D8 | GPIO 7 | SPI Clock line |
| | SPI MISO | D9 | GPIO 8 | SPI Master In Slave Out |
| | SPI MOSI | D10 | GPIO 9 | SPI Master Out Slave In |
| | SPI CS | D3 | GPIO 4 | SPI Chip Select (Active Low) |
| | RESET | D2 | GPIO 3 | Hardware reset line |
| **Motors (MOSFET)**| Motor 1 (Front-Left) | D0 | GPIO 1 | LEDC PWM Channel 0 |
| | Motor 2 (Front-Right)| D1 | GPIO 2 | LEDC PWM Channel 1 |
| | Motor 3 (Rear-Right) | - | GPIO 41 | LEDC PWM Channel 2 |
| | Motor 4 (Rear-Left)  | - | GPIO 42 | LEDC PWM Channel 3 |
| **Battery Sensing** | Batt Voltage Divider| A0 | GPIO 1 | ADC Channel for 1S LiPo monitoring |
| **Bench Scanner Rig**| SG90 Servo PWM | - | GPIO 44 | PWM control for bench-mounted ToF pan-tilt rig |

## Notes & Electrical Constraints

1. **Perfboard Socket Arrangement**: The XIAO ESP32-S3 is mounted using female header sockets on a custom perfboard carrier for clean component swapping.
2. **Downward Sensors**: VL53L0X and ADNS3080 are mounted rigidly on the underside of the frame pointing downwards.
3. **Bench Scanner Rig**: The SG90 servo is part of a bench-top room scanning test fixture only, keeping the flying frame weight strictly minimized.
