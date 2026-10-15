#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiClientSecure.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <time.h>

#include "config.h"
#include "wifi_networks.h"

ESP8266WiFiMulti wifiMulti;

// Hosted TrackBus FastAPI endpoint (HTTPS).
const char* API_URL =
    "https://trackbus-api.onrender.com/api/v1/gps";

TinyGPSPlus gps;
SoftwareSerial gpsSerial(GPS_RX_PIN, GPS_TX_PIN);

void connectToWiFi();
bool getTimestamp(char* buffer, size_t bufferSize);
void printGPSData();
void sendGPSUpdate();

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    gpsSerial.begin(GPS_BAUD_RATE);

    Serial.println();
    Serial.println("================================");
    Serial.println("       TRACKBUS IoT DEVICE");
    Serial.println("================================");

    connectToWiFi();

    if (WiFi.status() == WL_CONNECTED) {
        // Synchronize the device clock to UTC.
        configTime(0, 0, "pool.ntp.org", "time.nist.gov");

        Serial.print("Synchronizing device time...");

        char timestamp[25];
        unsigned long start = millis();

        while (!getTimestamp(timestamp, sizeof(timestamp))
               && millis() - start < 15000) {
            delay(500);
            Serial.print(".");
        }

        Serial.println();

        if (getTimestamp(timestamp, sizeof(timestamp))) {
            Serial.println("Clock synchronized.");
        } else {
            Serial.println(
                "Time sync pending; GPS updates will wait for valid time."
            );
        }
    }

    Serial.println("Waiting for GPS location...");
}

void loop() {
    // Read incoming GPS data.
    while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
    }

    // Process each newly updated GPS location.
    if (gps.location.isUpdated()) {
        printGPSData();

        if (gps.location.isValid() && gps.location.age() < 5000) {
            sendGPSUpdate();
        } else {
            Serial.println(
                "GPS fix invalid or stale; update skipped."
            );
        }
    }

    // Attempt Wi-Fi recovery if disconnected.
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Wi-Fi disconnected; reconnecting...");
        connectToWiFi();
    }
}

void connectToWiFi() {
    WiFi.mode(WIFI_STA);

    // Register the configured Wi-Fi networks.
    for (int i = 0; i < WIFI_NETWORK_COUNT; i++) {
        wifiMulti.addAP(
            WIFI_NETWORKS[i].ssid,
            WIFI_NETWORKS[i].password
        );
    }

    Serial.println("Searching for saved Wi-Fi networks...");

    while (wifiMulti.run() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("Wi-Fi connected!");

    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

bool getTimestamp(char* buffer, size_t bufferSize) {
    time_t now = time(nullptr);

    // Reject an unsynchronized clock.
    if (now < 1700000000) {
        return false;
    }

    struct tm timeInfo;
    gmtime_r(&now, &timeInfo);

    return strftime(
        buffer,
        bufferSize,
        "%Y-%m-%dT%H:%M:%SZ",
        &timeInfo
    ) > 0;
}

void printGPSData() {
    Serial.println();
    Serial.println("--------- BUS LOCATION ---------");

    Serial.print("Bus ID: ");
    Serial.println(BUS_ID);

    Serial.print("Latitude: ");
    Serial.println(gps.location.lat(), 6);

    Serial.print("Longitude: ");
    Serial.println(gps.location.lng(), 6);

    Serial.print("Satellites: ");
    Serial.println(gps.satellites.value());

    Serial.print("Wi-Fi: ");
    Serial.println(
        WiFi.status() == WL_CONNECTED
            ? "CONNECTED"
            : "DISCONNECTED"
    );

    Serial.println("--------------------------------");
}

void sendGPSUpdate() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("GPS update skipped: Wi-Fi unavailable.");
        return;
    }

    char timestamp[25];

    if (!getTimestamp(timestamp, sizeof(timestamp))) {
        Serial.println(
            "GPS update skipped: device time is not synchronized."
        );
        return;
    }

    // HTTPS client for the hosted Render endpoint.
    WiFiClientSecure client;

    // TEMPORARY CONNECTIVITY TEST ONLY:
    // This disables TLS certificate verification.
    // Replace with proper certificate verification before production.
    client.setInsecure();

    HTTPClient http;

    if (!http.begin(client, API_URL)) {
        Serial.println("Could not initialize HTTPS request.");
        return;
    }

    http.setTimeout(15000);
    http.addHeader("Content-Type", "application/json");

    // Construct the GPS update JSON payload.
    String payload = "{\"bus_id\":\"";
    payload += BUS_ID;
    payload += "\",\"latitude\":";
    payload += String(gps.location.lat(), 6);
    payload += ",\"longitude\":";
    payload += String(gps.location.lng(), 6);
    payload += ",\"timestamp\":\"";
    payload += timestamp;
    payload += "\"}";

    Serial.println("Sending GPS update to TrackBus...");
    Serial.println(payload);

    int statusCode = http.POST(payload);

    if (statusCode > 0) {
        Serial.print("HTTP status: ");
        Serial.println(statusCode);

        String response = http.getString();

        Serial.print("API response: ");
        Serial.println(response);

        if (statusCode >= 200 && statusCode < 300) {
            Serial.println("GPS update accepted by backend.");
        } else {
            Serial.println("Backend returned an error response.");
        }
    } else {
        Serial.print("HTTPS request failed: ");
        Serial.println(
            HTTPClient::errorToString(statusCode)
        );
    }

    http.end();
}
