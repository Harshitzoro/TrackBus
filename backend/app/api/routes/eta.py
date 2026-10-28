
from fastapi import APIRouter, HTTPException

from app.schemas.eta import ETAResponse, RouteETAResponse
from app.services.eta_service import (
    estimate_arrival,
    estimate_route_arrivals,
)
from fastapi import Depends
from app.core.auth import require_assigned_bus

router = APIRouter(prefix="/eta", tags=["eta"])


@router.get(
    "/{bus_id}",
    response_model=RouteETAResponse,
)
def get_route_eta(bus_id: str, _student: dict = Depends(require_assigned_bus)) -> RouteETAResponse:
    try:
        return estimate_route_arrivals(bus_id)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve bus location",
        ) from None


@router.get(
    "/{bus_id}/{stop_id}",
    response_model=ETAResponse,
)
def get_eta(bus_id: str, stop_id: str, _student: dict = Depends(require_assigned_bus)) -> ETAResponse:
    try:
        return estimate_arrival(bus_id, stop_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve bus location",
        ) from None
