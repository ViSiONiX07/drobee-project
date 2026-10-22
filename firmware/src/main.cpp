// Bee-Brain firmware entry point goes here.
#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println();
    Serial.println("================================");
    Serial.println("       BEE-BRAIN FIRMWARE       ");
    Serial.println("================================");
    Serial.println("ESP32-S3 initialized.");
    Serial.println("Sensor integration is pending.");
}

void loop() {
    // Sensor acquisition and telemetry
    // will be integrated in later stages.
    delay(1000);
}