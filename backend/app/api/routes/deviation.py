
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_assigned_bus
from app.services.deviation_service import check_route_deviation

router = APIRouter(prefix="/deviation", tags=["deviation"])


@router.get("/{bus_id}")
def get_deviation(
    bus_id: str,
    _student: dict = Depends(require_assigned_bus),
) -> dict:
    try:
        return check_route_deviation(bus_id)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve bus location",
        ) from None
