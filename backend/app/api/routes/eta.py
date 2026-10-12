
from fastapi import APIRouter, HTTPException

from app.schemas.eta import ETAResponse
from app.services.eta_service import estimate_arrival

router = APIRouter(prefix="/eta", tags=["eta"])


@router.get(
    "/{bus_id}/{stop_id}",
    response_model=ETAResponse,
)
def get_eta(bus_id: str, stop_id: str) -> ETAResponse:
    try:
        return estimate_arrival(bus_id, stop_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve bus location",
        ) from None
