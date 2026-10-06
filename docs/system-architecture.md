# System Architecture

```text
ESP8266 + GPS -> Backend API -> Firebase Realtime Database -> Web client
                                  ^
                                  +-- Routes, stops, and bus metadata
```

The device reports a bus identifier, coordinates, and timestamp. The backend validates and stores updates, and exposes health, bus, ETA, and deviation endpoints. The frontend consumes the API and presents bus and route information.

This document describes the intended structure; deployment and authentication details remain environment-specific.