import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


# =========================
# Firebase Admin init
# =========================
def init_firebase() -> None:
    """
    Инициализация Firebase Admin SDK.
    Вариант 1: через сервисный аккаунт JSON (FIREBASE_SERVICE_ACCOUNT_JSON=/path/key.json)
    Вариант 2: через Default Credentials (например, в облаке) — тогда не задавай переменную.
    """
    if firebase_admin._apps:
        return


    sa_path = r"D:\8term\Diplom\backend\keys\vacationventure-service-account.json"
    if sa_path:
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        return

    # Default credentials (например, если настроено окружение в GCP)
    firebase_admin.initialize_app()


init_firebase()


# =========================
# Models
# =========================
class EventType(str, Enum):
    click = "click"
    favorite = "favorite"
    unfavorite = "unfavorite"


class SearchContext(BaseModel):
    from_code: str
    to_code: str
    when_date: str  # "YYYY-MM-DD"


class ItemCardSnapshot(BaseModel):
    # ключ узла / идентификатор (например: thread.uid + "|" + start_date)
    item_id: str

    # то, что нужно для отрисовки карточки (как ты просил)
    thread_uid: str
    title: str

    departure_time: str  # "HH:mm"
    departure_station: str
    departure_date: str  # "YYYY-MM-DD"

    arrival_time: str  # "HH:mm"
    arrival_station: str
    arrival_date: str  # "YYYY-MM-DD"

    duration_text: str
    detail_url: str


class RecoEvent(BaseModel):
    event_type: EventType
    occurred_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))

    # user_id клиент может прислать, но сервер всё равно будет использовать uid из токена
    user_id: Optional[str] = None

    search: SearchContext
    item: ItemCardSnapshot


# =========================
# Auth dependency
# =========================
def get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    return parts[1].strip()


async def get_current_uid(authorization: Optional[str] = Header(default=None)) -> str:
    token = get_bearer_token(authorization)
    try:
        decoded = auth.verify_id_token(token)  # uid берём отсюда
        uid = decoded.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Token decoded but uid missing")
        return uid
    except Exception:
        # Не раскрываем детали, чтобы не помогать злоумышленникам
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# =========================
# Storage (JSONL file)
# =========================
EVENT_LOG_PATH = Path(os.getenv("EVENT_LOG_PATH", "./events.jsonl")).resolve()
EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_event(uid: str, event: RecoEvent) -> None:
    payload = event.model_dump()
    payload["user_id"] = uid  # серверный источник истины
    payload["_received_at_ms"] = int(time.time() * 1000)

    with EVENT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# =========================
# FastAPI
# =========================
app = FastAPI(title="Reco Events Collector")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/events", status_code=204)
def ingest_event(event: RecoEvent, uid: str = Depends(get_current_uid)):
    append_event(uid, event)
    return None