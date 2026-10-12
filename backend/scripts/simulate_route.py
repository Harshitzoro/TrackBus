
import json
import math
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# TrackBus 100-metre walking simulation
API_URL = "http://127.0.0.1:8000/api/v1/gps"
BUS_ID = "BUS_SIM_001"

# Example geographic anchor for simulation only.
# This is not a surveyed walking route.
START_LAT = 26.9124
START_LON = 75.7873

ROUTE_LENGTH_M = 100.0
STOP_DISTANCES_M = [0.0, 50.0, 100.0]
STOP_NAMES = ["Stop A", "Stop B", "Stop C"]

WALKING_SPEED_KMH = 4.0
UPDATE_INTERVAL_SECONDS = 5.0


def coordinates_at_distance(distance_m: float) -> tuple[float, float]:
    """Generate coordinates along a straight eastward test line."""
    distance_m = max(0.0, min(distance_m, ROUTE_LENGTH_M))

    meters_per_degree_lon = (
        111320.0 * math.cos(math.radians(START_LAT))
    )

    latitude = START_LAT
    longitude = START_LON + distance_m / meters_per_degree_lon

    return latitude, longitude


def send_gps_update(
    latitude: float,
    longitude: float,
) -> None:
    payload = {
        "bus_id": BUS_ID,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        if response.status != 200:
            raise RuntimeError(
                f"API returned HTTP {response.status}: {body}"
            )


def main() -> None:
    speed_mps = WALKING_SPEED_KMH / 3.6
    progress_m = 0.0

    print("=== TrackBus 100m Route Simulation ===")
    print(f"Bus ID: {BUS_ID}")
    print(f"Walking speed: {WALKING_SPEED_KMH} km/h")
    print(f"Update interval: {UPDATE_INTERVAL_SECONDS} seconds")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            latitude, longitude = coordinates_at_distance(progress_m)

            try:
                send_gps_update(latitude, longitude)
            except HTTPError as exc:
                print(f"HTTP error: {exc.code} - {exc.read().decode()}")
                break
            except URLError as exc:
                print(f"Cannot reach FastAPI: {exc.reason}")
                break

            print(
                f"Progress: {progress_m:6.1f} m / "
                f"{ROUTE_LENGTH_M:.0f} m | "
                f"GPS: {latitude:.6f}, {longitude:.6f}"
            )
            print("  Estimated time remaining:")

            for stop_name, stop_distance in zip(
                STOP_NAMES, STOP_DISTANCES_M
            ):
                remaining_m = max(0.0, stop_distance - progress_m)
                eta_seconds = remaining_m / speed_mps

                if progress_m >= stop_distance:
                    print(f"    {stop_name}: reached")
                else:
                    print(
                        f"    {stop_name}: "
                        f"{eta_seconds:.0f} seconds"
                    )

            print()

            if progress_m >= ROUTE_LENGTH_M:
                print("Simulation complete.")
                break

            time.sleep(UPDATE_INTERVAL_SECONDS)
            progress_m = min(
                ROUTE_LENGTH_M,
                progress_m + speed_mps * UPDATE_INTERVAL_SECONDS,
            )

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")


if __name__ == "__main__":
    main()
