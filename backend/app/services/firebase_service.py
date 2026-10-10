from app.core.firebase import get_database
from app.schemas.gps import GPSUpdate

def save_gps_update(update: GPSUpdate) -> dict:
    """Persist the latest GPS update for a bus."""
    database = get_database()

    location_data = {
        "latitude": update.latitude,
        "longitude": update.longitude,
        "timestamp": update.timestamp.isoformat(),
    }

    database.child("buses").child(update.bus_id).child(
        "location"
    ).set(location_data)

    return {
        "status": "saved",
        "bus_id": update.bus_id,
        "location": location_data,
    }
