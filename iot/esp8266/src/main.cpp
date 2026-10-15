#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFiMulti.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <time.h>

#include "config.h"
#include "wifi_networks.h"
ESP8266WiFiMulti wifiMulti;

// FastAPI address: use your computer's current IPv4 address.
const char* API_URL = "https://trackbus-api.onrender.com/api/v1/gps";

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
        Serial.print("Synchronizing device time");

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
            Serial.println("Time sync pending; GPS updates will wait for valid time.");
        }
    }

    Serial.println("Waiting for GPS location...");
}

void loop() {
    while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
    }

    if (gps.location.isUpdated()) {
        printGPSData();

        if (gps.location.isValid() && gps.location.age() < 5000) {
            sendGPSUpdate();
        } else {
            Serial.println("GPS fix invalid or stale; update skipped.");
        }
    }

    // Allow Wi-Fi to recover if the connection drops.
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Wi-Fi disconnected; reconnecting...");
        connectToWiFi();
    }
}

void connectToWiFi() {
    WiFi.mode(WIFI_STA);

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
        WiFi.status() == WL_CONNECTED ? "CONNECTED" : "DISCONNECTED"
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
        Serial.println("GPS update skipped: device time is not synchronized.");
        return;
    }

    WiFiClient client;
    HTTPClient http;

    if (!http.begin(client, API_URL)) {
        Serial.println("Could not initialize HTTP request.");
        return;
    }

    http.setTimeout(5000);
    http.addHeader("Content-Type", "application/json");

    // Coordinates are numeric JSON values; timestamp is UTC ISO 8601.
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

        Serial.print("API response: ");
        Serial.println(http.getString());

        if (statusCode == 200) {
            Serial.println("GPS update accepted by backend.");
        } else {
            Serial.println("Backend did not accept the update.");
        }
    } else {
        Serial.print("HTTP request failed: ");
        Serial.println(HTTPClient::errorToString(statusCode));
    }

    http.end();
}
