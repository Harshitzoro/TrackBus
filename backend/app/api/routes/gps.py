from fastapi import APIRouter

router = APIRouter(prefix="/gps", tags=["gps"])


@router.post("")
def receive_gps_update() -> dict[str, str]:
    return {"status": "not_implemented"}