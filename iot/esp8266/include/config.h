#ifndef CONFIG_H
#define CONFIG_H

// =============================
// Wi-Fi Configuration
// =============================

#define WIFI_SSID "redmi10 prime 5G"
#define WIFI_PASSWORD "11223344"


// =============================
// GPS Configuration
// =============================

// GPS connected to:
// NEO-6M TX -> ESP8266 D5
// NEO-6M RX -> ESP8266 D6

#define GPS_RX_PIN D5
#define GPS_TX_PIN D6

#define GPS_BAUD_RATE 9600


// =============================
// Serial Monitor
// =============================

#define SERIAL_BAUD_RATE 115200


// =============================
// Bus Information
// =============================

#define BUS_ID "BUS_001"

#endif