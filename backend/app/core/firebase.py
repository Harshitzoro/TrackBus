from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db

from app.core.config import settings


def get_database():
    """Initialize Firebase once and return the root database reference."""
    database_url = settings.firebase_database_url
    credentials_path = settings.firebase_credentials_path

    if not database_url:
        raise RuntimeError("FIREBASE_DATABASE_URL is not configured")

    if not credentials_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH is not configured")

    path = Path(credentials_path).expanduser()
    secret_dir = Path("/etc/secrets")
    secret_path = secret_dir / "trackbus-255f1-firebase-adminsdk-fbsvc-5dc5f542b6.json"
    if not path.is_file():
        details = {
            "configured_path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "resolved_path": str(path.resolve()),
            "secret_dir_exists": secret_dir.is_dir(),
            "secret_entry_exists": secret_path.exists(),
            "secret_entry_is_file": secret_path.is_file(),
            "secret_entry_is_dir": secret_path.is_dir(),
        }

        raise RuntimeError(f"Firebase secret path diagnostic: {details}")

    

    try:
        app = firebase_admin.get_app()
    except ValueError:
        credential = credentials.Certificate(str(path))
        app = firebase_admin.initialize_app(
            credential,
            {"databaseURL": database_url},
        )

    return db.reference("/", app=app)
