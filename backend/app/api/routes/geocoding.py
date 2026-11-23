"""Authenticated reverse-geocoding endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_student
from app.services.geocoding_service import (
    GeocodingError,
    GeocodingTimeoutError,
    reverse_geocode,
)

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


class ReverseGeocodingResponse(BaseModel):
    address: str
    source: str
    latitude: float
    longitude: float


@router.get("/reverse", response_model=ReverseGeocodingResponse)
def get_reverse_geocoding(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    _student: dict = Depends(get_current_student),
) -> ReverseGeocodingResponse:
    try:
        result = reverse_geocode(latitude, longitude)
    except GeocodingTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Address lookup timed out",
        ) from None
    except GeocodingError:
        raise HTTPException(
            status_code=502,
            detail="Address lookup is temporarily unavailable",
        ) from None

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No address found for these coordinates",
        )

    return ReverseGeocodingResponse(
        address=result.address,
        source=result.source,
        latitude=latitude,
        longitude=longitude,
    )