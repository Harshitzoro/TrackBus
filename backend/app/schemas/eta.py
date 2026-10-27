from pydantic import BaseModel

class ETAResponse(BaseModel):
    bus_id: str
    stop_id: str
    eta_seconds: int | None = None
    distance_m: float | None = None
    status: str
class StopETA(BaseModel):
    stop_id: str
    name: str
    latitude: float
    longitude: float
    distance_remaining_m: float
    eta_seconds: int


class RouteETAResponse(BaseModel):
    bus_id: str
    status: str
    route_progress_fraction: float | None = None
    distance_remaining_m: float | None = None
    next_stop_id: str | None = None
    upcoming_stops: list[StopETA] = []
