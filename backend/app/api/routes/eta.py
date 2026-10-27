
from fastapi import APIRouter, HTTPException

from app.schemas.eta import ETAResponse, RouteETAResponse
from app.services.eta_service import (
    estimate_arrival,
    estimate_route_arrivals,
)

router = APIRouter(prefix="/eta", tags=["eta"])


@router.get(
    "/{bus_id}",
    response_model=RouteETAResponse,
)
def get_route_eta(bus_id: str) -> RouteETAResponse:
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
def get_eta(bus_id: str, stop_id: str) -> ETAResponse:
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
