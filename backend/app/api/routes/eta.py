from fastapi import APIRouter

router = APIRouter(prefix="/eta", tags=["eta"])


@router.get("/{bus_id}/{stop_id}")
def get_eta(bus_id: str, stop_id: str) -> dict[str, str]:
    return {"bus_id": bus_id, "stop_id": stop_id, "status": "not_implemented"}