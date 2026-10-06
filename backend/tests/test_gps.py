from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.gps import GPSUpdate


def test_gps_update_accepts_valid_coordinates() -> None:
    update = GPSUpdate(
        bus_id="BUS-001",
        latitude=12.9,
        longitude=77.5,
        timestamp=datetime.now(timezone.utc),
    )

    assert update.bus_id == "BUS-001"


def test_gps_update_rejects_out_of_range_coordinates() -> None:
    with pytest.raises(ValidationError):
        GPSUpdate(
            bus_id="BUS-001",
            latitude=91,
            longitude=77.5,
            timestamp=datetime.now(timezone.utc),
        )