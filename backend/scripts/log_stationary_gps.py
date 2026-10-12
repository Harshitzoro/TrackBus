import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from app.core.firebase import get_database

BUS_ID = "BUS_001"
DURATION_SECONDS = 180  # 3 minutes
INTERVAL_SECONDS = 2

OUTPUT_FILE = Path(__file__).resolve().parent / "stationary_gps.csv"


def main():
    database = get_database()
    location_ref = (
        database.child("buses")
        .child(BUS_ID)
        .child("location")
    )

    end_time = time.monotonic() + DURATION_SECONDS
    readings = 0

    print(f"Recording stationary GPS data for {BUS_ID}")
    print("Keep the device completely still.")
    print(f"Duration: {DURATION_SECONDS} seconds")
    print(f"CSV output: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop early.\n")

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "capture_timestamp_utc",
                "gps_timestamp",
                "bus_id",
                "latitude",
                "longitude",
                "satellites",
                "hdop",
            ],
        )
        writer.writeheader()

        try:
            while time.monotonic() < end_time:
                data = location_ref.get()

                if isinstance(data, dict):
                    latitude = data.get("latitude")
                    longitude = data.get("longitude")

                    if latitude is not None and longitude is not None:
                        writer.writerow({
                            "capture_timestamp_utc": (
                                datetime.now(timezone.utc).isoformat()
                            ),
                            "gps_timestamp": data.get("timestamp", ""),
                            "bus_id": BUS_ID,
                            "latitude": latitude,
                            "longitude": longitude,
                            "satellites": data.get("satellites", ""),
                            "hdop": data.get("hdop", ""),
                        })
                        file.flush()
                        readings += 1
                        print(
                            f"{readings:03d} | "
                            f"Lat: {latitude} | Lon: {longitude}"
                        )
                    else:
                        print("Waiting for valid coordinates...")
                else:
                    print("No location data found in Firebase yet.")

                time.sleep(INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nRecording stopped manually.")

    print(f"\nFinished. Saved {readings} readings.")
    print(f"File: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
