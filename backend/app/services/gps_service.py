from app.schemas.gps import GPSUpdate


def accept_gps_update(update: GPSUpdate) -> GPSUpdate:
    """Validate at the schema boundary; persistence will be added separately."""
    return update