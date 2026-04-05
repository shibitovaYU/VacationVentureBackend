import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials


def _resolve_service_account_path() -> Path:
    env_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    project_root = Path(__file__).resolve().parents[2]
    return project_root / "keys" / "vacationventure-service-account.json"


def init_firebase() -> None:
    if firebase_admin._apps:
        return

    sa_path = _resolve_service_account_path()
    if sa_path.exists():
        cred = credentials.Certificate(str(sa_path))
        firebase_admin.initialize_app(cred)
        return

    raise FileNotFoundError(
        "Firebase service account file not found. "
        "Set FIREBASE_SERVICE_ACCOUNT_PATH or place the key at "
        f"{sa_path}"
    )

    firebase_admin.initialize_app()
