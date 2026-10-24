
"""Shared route configuration for the TrackBus Kota prototype."""

STOP_COORDINATES = {
    "STOP_A": (25.1386742, 75.8260137),
    "STOP_B": (25.1421876, 75.8284360),
}

# Approximate road distance reported for the two stops.
ROUTE_LENGTH_M = 500.0

# Provisional corridor for the straight-segment route model.
# This must be calibrated against the actual road geometry and GPS noise.
ROUTE_CORRIDOR_M = 40.0

# GPS older than this is not used for ETA or deviation.
MAX_GPS_AGE_SECONDS = 300

# Allow a small clock difference for device/server timestamps.
MAX_FUTURE_GPS_SECONDS = 30

# A bus needs a meaningful positive speed for a moving ETA.
MIN_ETA_SPEED_KMPH = 1.0
MAX_ETA_SPEED_KMPH = 150.0
