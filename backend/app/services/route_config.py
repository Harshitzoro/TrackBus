
"""Route configuration for the TrackBus Kota prototype."""

# Starting point: CP Tower, Road No. 1, IPIA, Kota.
ROUTE_START = {
    "stop_id": "CP_TOWER",
    "name": "CP Tower",
    "latitude": 25.1438291,
    "longitude": 75.8596856,
}

# Ordered student pickup stops.
# Coordinates are supplied by the project team and not independently verified.
ROUTE_STOPS = [
    {"stop_id": "STOP_01", "name": "Sophia School",
     "latitude": 25.2119369, "longitude": 75.8897055},
    {"stop_id": "STOP_02", "name": "Dadabari",
     "latitude": 25.1578864, "longitude": 75.8269505},
    {"stop_id": "STOP_03", "name": "Basant Vihar",
     "latitude": 25.1550327, "longitude": 75.8276261},
    {"stop_id": "STOP_04", "name": "Santoshi Nagar",
     "latitude": 25.1457237, "longitude": 75.8293526},
    {"stop_id": "STOP_05", "name": "Santoshi Nagar",
     "latitude": 25.1419184, "longitude": 75.8285269},
    {"stop_id": "STOP_06", "name": "Shiv Jyoti",
     "latitude": 25.1372505, "longitude": 75.8319138},
    {"stop_id": "STOP_07", "name": "Agni Shaman",
     "latitude": 25.1343766, "longitude": 75.8300814},
    {"stop_id": "STOP_08", "name": "TVS Circle",
     "latitude": 25.1389671, "longitude": 75.8264484},
    {"stop_id": "STOP_09", "name": "Gad Circle",
     "latitude": 25.1431319, "longitude": 75.8219599},
    {"stop_id": "STOP_10", "name": "Shivpura",
     "latitude": 25.1379512, "longitude": 75.8176959},
    {"stop_id": "STOP_11", "name": "Chawla Circle",
     "latitude": 25.1255943, "longitude": 75.8200124},
    {"stop_id": "STOP_12", "name": "Kota University",
     "latitude": 25.1178907, "longitude": 75.8221127},
    {"stop_id": "STOP_13", "name": "Kabir Circle",
     "latitude": 25.1182663, "longitude": 75.8320165},
    {"stop_id": "STOP_14", "name": "MBS Marg",
     "latitude": 25.1184071, "longitude": 75.8435796},
    {"stop_id": "STOP_15", "name": "Anantpura",
     "latitude": 25.1199095, "longitude": 75.8598613},
    {"stop_id": "STOP_16", "name": "CP University",
     "latitude": 25.0100259, "longitude": 75.9127784},
]

# Provisional settings retained from the existing prototype.
# Full-route geometry and ETA calculations will replace these assumptions.

ROUTE_CORRIDOR_M = 40.0

MAX_GPS_AGE_SECONDS = 300
MAX_FUTURE_GPS_SECONDS = 30

MIN_ETA_SPEED_KMPH = 1.0
MAX_ETA_SPEED_KMPH = 150.0
