from pydantic import BaseModel, Field


class Bus(BaseModel):
    bus_id: str = Field(min_length=1)
    name: str
    route_id: str
    active: bool = True