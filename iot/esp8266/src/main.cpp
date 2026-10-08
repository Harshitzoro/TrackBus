#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>

#include "C:\Users\rajva\OneDrive\Desktop\TrackBus\TrackBus\iot\esp8266\include\config.h"

// =====================================
// GPS
// =====================================

TinyGPSPlus gps;

SoftwareSerial gpsSerial(
    GPS_RX_PIN,
    GPS_TX_PIN
);
void connectToWiFi();
void printGPSData();

// =====================================
// Setup
// =====================================

void setup() {

    Serial.begin(SERIAL_BAUD_RATE);

    gpsSerial.begin(GPS_BAUD_RATE);

    Serial.println();
    Serial.println("================================");
    Serial.println("       TRACKBUS IoT DEVICE");
    Serial.println("================================");

    connectToWiFi();

    Serial.println();
    Serial.println("Waiting for GPS location...");
}


// =====================================
// Main Loop
// =====================================

void loop() {

    // Read GPS data
    while (gpsSerial.available()) {

        gps.encode(
            gpsSerial.read()
        );
    }

    // Check if location has changed
    if (gps.location.isUpdated()) {

        printGPSData();
    }
}


// =====================================
// Wi-Fi Connection
// =====================================

void connectToWiFi() {

    Serial.print("Connecting to Wi-Fi");

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    while (
        WiFi.status() != WL_CONNECTED
    ) {

        delay(500);

        Serial.print(".");
    }

    Serial.println();

    Serial.println("Wi-Fi Connected!");

    Serial.print("ESP8266 IP Address: ");

    Serial.println(
        WiFi.localIP()
    );
}


// =====================================
// GPS Data Output
// =====================================

void printGPSData() {

    Serial.println();
    Serial.println("--------- BUS LOCATION ---------");

    Serial.print("Bus ID: ");
    Serial.println(BUS_ID);

    Serial.print("Latitude: ");
    Serial.println(
        gps.location.lat(),
        6
    );

    Serial.print("Longitude: ");
    Serial.println(
        gps.location.lng(),
        6
    );

    Serial.print("Satellites: ");
    Serial.println(
        gps.satellites.value()
    );

    Serial.print("Wi-Fi: ");

    if (
        WiFi.status() == WL_CONNECTED
    ) {

        Serial.println("CONNECTED");

    } else {

        Serial.println("DISCONNECTED");
    }

    Serial.println(
        "--------------------------------"
    );
}