
"""Firebase Authentication dependencies for protected API routes."""

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.core.firebase import get_database

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict[str, Any]:
    """Verify the Firebase ID token and return its decoded claims."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Ensure the existing Firebase Admin app is initialized.
        get_database()

        decoded_token = auth.verify_id_token(
            credentials.credentials,
            check_revoked=True,
        )

    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError,
            auth.RevokedIdTokenError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except FirebaseError as exc:
        raise HTTPException(
            status_code=503,
            detail="Firebase authentication is temporarily unavailable",
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Firebase Admin is not configured correctly",
        ) from exc

    if not decoded_token.get("uid"):
        raise HTTPException(
            status_code=401,
            detail="Authentication token has no user identity",
        )

    return decoded_token


def get_current_student(
    token: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Load the trusted profile for the authenticated student."""

    uid = token["uid"]

    try:
        profile = get_database().child("users").child(uid).get()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve user profile",
        ) from exc

    if not isinstance(profile, dict):
        raise HTTPException(
            status_code=403,
            detail="User profile or bus assignment is not configured",
        )

    if str(profile.get("role", "")).strip().lower() != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access required",
        )

    bus_id = profile.get("bus_id")

    if not isinstance(bus_id, str) or not bus_id.strip():
        raise HTTPException(
            status_code=403,
            detail="No bus is assigned to this student",
        )

    return {
        "uid": uid,
        "role": "Student",
        "bus_id": bus_id.strip(),
    }

def require_assigned_bus(
    bus_id: str,
    student: dict[str, Any] = Depends(get_current_student),
) -> dict[str, Any]:
    """Allow a student to access only their assigned bus."""

    if bus_id.strip() != student["bus_id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this bus",
        )

    return student
