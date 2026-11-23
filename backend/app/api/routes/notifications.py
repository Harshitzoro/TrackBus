
"""Authenticated student notification registration."""

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_student
from app.core.firebase import get_database
from app.schemas.notification import (
    NotificationRegistrationRequest,
    NotificationRegistrationResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/register",
    response_model=NotificationRegistrationResponse,
)
def register_notification_device(
    request: NotificationRegistrationRequest,
    student: dict = Depends(get_current_student),
) -> NotificationRegistrationResponse:
    """Register an FCM token for the authenticated student's device."""

    token = request.fcm_token.strip()
    if len(token) < 20:
        raise HTTPException(status_code=422, detail="Invalid FCM token")

    try:
        database = get_database()
        user_ref = database.child("users").child(student["uid"])
        profile = user_ref.get()

        if not isinstance(profile, dict):
            raise HTTPException(
                status_code=403,
                detail="Student profile is not configured",
            )

        bus_id = profile.get("bus_id")
        stop_id = profile.get("stop_id")

        if bus_id != student["bus_id"]:
            raise HTTPException(
                status_code=403,
                detail="Student bus assignment is invalid",
            )

        if not isinstance(stop_id, str) or not stop_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Assign a pickup stop before registering notifications",
            )

        bus = database.child("buses").child(bus_id).get()
        if not isinstance(bus, dict):
            raise HTTPException(status_code=400, detail="Assigned bus not found")

        route_id = bus.get("routeId")
        if not isinstance(route_id, str) or not route_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Assigned bus has no route configured",
            )

        stop = (
            database.child("routes")
            .child(route_id)
            .child("stops")
            .child(stop_id.strip().upper())
            .get()
        )
        if not isinstance(stop, dict):
            raise HTTPException(
                status_code=400,
                detail="Assigned pickup stop is not on the bus route",
            )

        token_key = hashlib.sha256(token.encode("utf-8")).hexdigest()
        token_ref = user_ref.child("fcm_tokens").child(token_key)
        token_ref.set({
            "token": token,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to register notification device",
        ) from None

    return NotificationRegistrationResponse(
        status="registered",
        message="Notification device registered successfully",
    )
