# Database Schema

The Firebase Realtime Database is expected to organize data by concern:

```text
buses/{bus_id}
  name, route_id, active
locations/{bus_id}/latest
  latitude, longitude, timestamp
routes/{route_id}
  name, stop_ids, path
stops/{stop_id}
  name, latitude, longitude
```

This is a starter proposal. Keep credentials out of this repository and validate all client-provided data in the backend.