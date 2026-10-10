from fastapi import APIRouter, HTTPException

from app.schemas.gps import GPSUpdate
from app.services.gps_service import accept_gps_update
from app.services.firebase_service import save_gps_update

router = APIRouter(prefix="/gps", tags=["gps"])

@router.post("")
def receive_gps_update(update: GPSUpdate) -> dict:
    """Validate and persist a bus GPS update."""
    accepted_update = accept_gps_update(update)

    try:
        return save_gps_update(accepted_update)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to save GPS update",
        ) from None
