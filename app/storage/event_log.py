import json
import os
import time
from pathlib import Path
from typing import List

from app.models import RecoEvent


EVENT_LOG_PATH = Path(os.getenv("EVENT_LOG_PATH", "./events.jsonl")).resolve()
EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_event(uid: str, event: RecoEvent) -> None:
    payload = event.model_dump()
    payload["user_id"] = uid
    payload["_received_at_ms"] = int(time.time() * 1000)

    with EVENT_LOG_PATH.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_user_events(uid: str) -> List[RecoEvent]:
    if not EVENT_LOG_PATH.exists():
        return []

    events: List[RecoEvent] = []
    with EVENT_LOG_PATH.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                if payload.get("user_id") != uid:
                    continue
                events.append(RecoEvent.model_validate(payload))
            except Exception:
                continue
    return events


def read_all_events() -> List[RecoEvent]:
    if not EVENT_LOG_PATH.exists():
        return []

    events: List[RecoEvent] = []
    with EVENT_LOG_PATH.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                events.append(RecoEvent.model_validate(payload))
            except Exception:
                continue
    return events
