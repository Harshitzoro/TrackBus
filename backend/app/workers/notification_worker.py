
"""Periodic TrackBus ETA notification worker.

Defaults to dry-run mode. Does not send push notifications unless
explicitly enabled in the worker environment.
"""

import logging
import os
import time

from app.core.firebase import get_database
from app.services.eta_service import estimate_arrival
from app.services.fcm_service import send_bus_approaching_notification
from app.services.notification_store import (
    notification_is_due,
    record_notification_sent,
)

POLL_INTERVAL_SECONDS = 60
ETA_THRESHOLD_SECONDS = 15 * 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def check_student_notifications() -> None:
    """Evaluate assigned stops for students with registered FCM tokens."""
    database = get_database()
    users = database.child("users").get()

    if not isinstance(users, dict):
        logger.info("No student profiles found.")
        return

    dry_run = os.getenv("TRACKBUS_NOTIFICATIONS_DRY_RUN", "true").lower() != "false"

    for student_id, profile in users.items():
        if not isinstance(profile, dict):
            continue

        if str(profile.get("role", "")).strip().lower() != "student":
            continue

        bus_id = profile.get("bus_id")
        stop_id = profile.get("stop_id")
        tokens = profile.get("fcm_tokens")

        if not (
            isinstance(bus_id, str)
            and isinstance(stop_id, str)
            and isinstance(tokens, dict)
            and tokens
        ):
            continue

        try:
            eta = estimate_arrival(bus_id, stop_id)

            if eta.status != "available" or eta.eta_seconds is None:
                continue

            if not 0 <= eta.eta_seconds <= ETA_THRESHOLD_SECONDS:
                continue

            if not notification_is_due(student_id, bus_id, stop_id):
                continue

            if dry_run:
                logger.info(
                    "DRY RUN: notification eligible; bus=%s stop=%s eta_seconds=%s",
                    bus_id,
                    stop_id,
                    eta.eta_seconds,
                )
                continue

            # Real delivery will be enabled only after the send-and-record
            # flow has been implemented and tested.
            successful_sends = 0

            for token_id, token_data in tokens.items():
                # Registered tokens are stored as dictionaries.
                if isinstance(token_data, dict):
                    fcm_token = token_data.get("token")
                elif isinstance(token_data, str):
                    fcm_token = token_data
                else:
                    continue

                if not isinstance(fcm_token, str) or not fcm_token.strip():
                    continue

                try:
                    message_id = send_bus_approaching_notification(
                        token=fcm_token,
                        bus_id=bus_id,
                        stop_id=stop_id,
                        eta_seconds=eta.eta_seconds,
                    )

                    successful_sends += 1

                    logger.info(
                        "FCM notification sent; student=%s token_id=%s message_id=%s",
                        student_id,
                        token_id,
                        message_id,
                    )

                except Exception:
                    logger.exception(
                        "FCM delivery failed for student %s, token %s",
                        student_id,
                        token_id,
                    )

            if successful_sends > 0:
                record_notification_sent(student_id, bus_id, stop_id)

                logger.info(
                    "Notification cooldown recorded; student=%s bus=%s stop=%s",
                    student_id,
                    bus_id,
                    stop_id,
                )
            else:
                logger.warning(
                    "No notification was successfully sent to student %s; cooldown not recorded.",
                    student_id,
                )

        except Exception:
            # One student's bad profile or an ETA failure should not stop
            # the remaining students from being checked.
            logger.exception(
                "Failed to evaluate notification for one student profile."
            )


def main() -> None:
    logger.info(
        "TrackBus notification worker started; dry-run mode is enabled by default."
    )

    while True:
        try:
            check_student_notifications()
        except Exception:
            logger.exception("Notification worker cycle failed.")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
