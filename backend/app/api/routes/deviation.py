
from fastapi import APIRouter, HTTPException

from app.services.deviation_service import check_route_deviation

router = APIRouter(prefix="/deviation", tags=["deviation"])


@router.get("/{bus_id}")
def get_deviation(bus_id: str) -> dict:
    try:
        return check_route_deviation(bus_id)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve bus location",
        ) from None
