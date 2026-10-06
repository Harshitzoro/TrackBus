# GPS Data Format

GPS reports are JSON objects. The initial expected fields are:

| Field | Type | Description |
| --- | --- | --- |
| `bus_id` | string | Stable identifier for the bus |
| `latitude` | number | Latitude in decimal degrees, from -90 to 90 |
| `longitude` | number | Longitude in decimal degrees, from -180 to 180 |
| `timestamp` | string | UTC timestamp in ISO 8601 format |

Example:

```json
{
  "bus_id": "BUS-001",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "timestamp": "2026-01-01T08:30:00Z"
}
```