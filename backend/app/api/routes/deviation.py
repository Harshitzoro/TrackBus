from fastapi import APIRouter

router = APIRouter(prefix="/deviation", tags=["deviation"])


@router.get("/{bus_id}")
def get_deviation(bus_id: str) -> dict[str, str]:
    return {"bus_id": bus_id, "status": "not_implemented"}