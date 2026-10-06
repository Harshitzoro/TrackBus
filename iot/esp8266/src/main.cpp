#include <Arduino.h>
#include "config.h"

void setup() {
  Serial.begin(115200);
  Serial.println("TrackBus device starting");
}

void loop() {
  // GPS and network reporting will be implemented for the selected hardware.
  delay(1000);
}