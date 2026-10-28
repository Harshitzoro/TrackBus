
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_student
from app.core.firebase import get_database

router = APIRouter(prefix="/buses", tags=["buses"])


@router.get("")
def list_buses(
    student: dict = Depends(get_current_student),
) -> dict[str, list[dict]]:
    """Return only the authenticated student's assigned bus."""
    bus_id = student["bus_id"]

    try:
        bus_data = get_database().child("buses").child(bus_id).get()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve buses from Firebase",
        ) from None

    if not isinstance(bus_data, dict):
        return {"buses": []}

    return {
        "buses": [
            {
                "bus_id": bus_id,
                **bus_data,
            }
        ]
    }
