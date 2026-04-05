import json
import os
from pathlib import Path
from typing import Optional

from app.models import GlobalRecommendationsSnapshot


GLOBAL_RECOMMENDATIONS_PATH = Path(
    os.getenv("GLOBAL_RECOMMENDATIONS_PATH", "./global_recommendations.json")
).resolve()
GLOBAL_RECOMMENDATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)


def write_global_recommendations(snapshot: GlobalRecommendationsSnapshot) -> None:
    with GLOBAL_RECOMMENDATIONS_PATH.open("w", encoding="utf-8") as file_obj:
        json.dump(snapshot.model_dump(), file_obj, ensure_ascii=False, indent=2)


def read_global_recommendations() -> Optional[GlobalRecommendationsSnapshot]:
    if not GLOBAL_RECOMMENDATIONS_PATH.exists():
        return None

    try:
        with GLOBAL_RECOMMENDATIONS_PATH.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
        return GlobalRecommendationsSnapshot.model_validate(payload)
    except Exception:
        return None
