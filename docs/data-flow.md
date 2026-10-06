# Data Flow

1. The GPS receiver provides a location fix to the ESP8266.
2. The device sends a timestamped update to the backend over Wi-Fi.
3. The backend validates the payload and persists accepted data.
4. The web client requests bus and route information from the API.
5. ETA and deviation services derive status from recent locations and configured routes.

Clients should treat old timestamps and unavailable fixes as non-live data.