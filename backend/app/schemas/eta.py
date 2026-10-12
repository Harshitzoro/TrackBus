from pydantic import BaseModel

class ETAResponse(BaseModel):
    bus_id: str
    stop_id: str
    eta_seconds: int | None = None
    distance_m: float | None = None
    status: str
