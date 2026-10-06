from fastapi import APIRouter

router = APIRouter(prefix="/buses", tags=["buses"])


@router.get("")
def list_buses() -> dict[str, list[object]]:
    return {"buses": []}