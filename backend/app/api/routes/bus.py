
from fastapi import APIRouter, HTTPException

from app.core.firebase import get_database

router = APIRouter(prefix="/buses", tags=["buses"])


@router.get("")
def list_buses() -> dict[str, list[dict]]:
    """Return bus records from Firebase."""
    try:
        buses_data = get_database().child("buses").get()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve buses from Firebase",
        ) from None

    if not isinstance(buses_data, dict):
        return {"buses": []}

    buses = []

    for bus_id, bus_data in buses_data.items():
        if not isinstance(bus_data, dict):
            continue

        buses.append({
            "bus_id": bus_id,
            **bus_data,
        })

    return {"buses": buses}
