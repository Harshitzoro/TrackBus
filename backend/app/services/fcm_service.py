
"""Firebase Cloud Messaging delivery service."""

import logging

from firebase_admin import messaging

logger = logging.getLogger(__name__)


def send_bus_approaching_notification(
    token: str,
    bus_id: str,
    stop_id: str,
    eta_seconds: int,
) -> str:
    """Send a bus-approaching push notification to one registered device.

    Returns the FCM message ID if Firebase accepts the message.
    Raises an exception if delivery submission fails.
    """
    if not token or not token.strip():
        raise ValueError("FCM token is required")

    if not bus_id.strip() or not stop_id.strip():
        raise ValueError("Bus ID and stop ID are required")

    if eta_seconds < 0:
        raise ValueError("ETA cannot be negative")

    minutes = (eta_seconds + 59) // 60

    message = messaging.Message(
        notification=messaging.Notification(
            title="Your bus is approaching",
            body=f"Your bus is expected at your stop in about {minutes} minutes.",
        ),
        data={
            "event": "bus_approaching",
            "bus_id": bus_id,
            "stop_id": stop_id,
            "eta_seconds": str(eta_seconds),
        },
        token=token,
    )

    message_id = messaging.send(message)
    logger.info(
        "FCM accepted bus-approaching notification for bus %s, stop %s",
        bus_id,
        stop_id,
    )
    return message_id
