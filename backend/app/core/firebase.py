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

    if not path.is_file():
        secret_dir = Path("/etc/secrets")
        visible_files = (
            sorted(p.name for p in secret_dir.iterdir() if p.is_file())
            if secret_dir.is_dir()
            else []
        )
        raise RuntimeError(
            "Firebase credentials file is missing. "
            f"Configured path: {path}; "
            f"parent directory exists: {path.parent.is_dir()}; "
            f"secret filenames visible: {visible_files}"
        )
    

    try:
        app = firebase_admin.get_app()
    except ValueError:
        credential = credentials.Certificate(str(path))
        app = firebase_admin.initialize_app(
            credential,
            {"databaseURL": database_url},
        )

    return db.reference("/", app=app)
