
from datetime import datetime

from pydantic import BaseModel, Field


class GPSUpdate(BaseModel):
    bus_id: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime

    # Optional initially, so existing devices and tests remain compatible.
    speed_kmph: float | None = Field(
        default=None,
        ge=0,
        le=300,
    )
