# ESP8266 Device

The firmware reads GPS fixes and sends location updates to the TrackBus backend.

Configure Wi-Fi, API endpoint, and device identity in `include/config.h` before building. Do not commit real credentials. The firmware currently provides a starting point only; select and install a compatible GPS library for your hardware.