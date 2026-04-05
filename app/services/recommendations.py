import math
from typing import Dict, List, Set, Tuple

from app.models import (
    EventType,
    GlobalRecommendationsSnapshot,
    RecommendationValue,
    RecoEvent,
    UserRecommendationsResponse,
)


EVENT_TYPE_WEIGHTS: Dict[EventType, float] = {
    EventType.click: 1.0,
    EventType.favorite: 3.0,
    EventType.unfavorite: -4.0,
}


def detect_time_of_day(departure_time: str) -> str:
    hour = int(departure_time.split(":", maxsplit=1)[0])
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "day"
    if 18 <= hour < 24:
        return "evening"
    return "night"


def extract_departure_city(title: str) -> str:
    for separator in ("\u2014", "-"):
        parts = title.split(separator, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip()
    return title.strip()


def extract_airline_code(item_id: str) -> str:
    return item_id[:2].upper()


def event_feature_weights(event: RecoEvent) -> Dict[str, float]:
    weight = EVENT_TYPE_WEIGHTS[event.event_type]
    departure_time_bucket = detect_time_of_day(event.item.departure_time)
    departure_city = extract_departure_city(event.item.title)
    airline_code = extract_airline_code(event.item.item_id)

    return {
        f"time_of_day:{departure_time_bucket}": weight,
        f"departure_city:{departure_city}": weight,
        f"airline:{airline_code}": weight,
    }


def build_user_vector(events: List[RecoEvent]) -> Tuple[List[str], List[float], Dict[str, float]]:
    raw_scores: Dict[str, float] = {}
    for event in events:
        for feature_name, weight in event_feature_weights(event).items():
            raw_scores[feature_name] = raw_scores.get(feature_name, 0.0) + weight

    feature_order = sorted(raw_scores)
    raw_vector = [raw_scores[name] for name in feature_order]
    norm = math.sqrt(sum(value * value for value in raw_vector))
    if norm == 0:
        vector = [0.0 for _ in raw_vector]
    else:
        vector = [round(value / norm, 6) for value in raw_vector]

    rounded_scores = {name: round(score, 3) for name, score in raw_scores.items()}
    return feature_order, vector, rounded_scores


def build_raw_scores(events: List[RecoEvent]) -> Dict[str, float]:
    _, _, raw_scores = build_user_vector(events)
    return raw_scores


def top_recommendation(raw_scores: Dict[str, float], prefix: str) -> RecommendationValue:
    candidates = {
        feature_name[len(prefix):]: score
        for feature_name, score in raw_scores.items()
        if feature_name.startswith(prefix)
    }
    if not candidates:
        return RecommendationValue(value=None, score=0.0)

    best_value, best_score = max(candidates.items(), key=lambda item: item[1])
    if best_score <= 0:
        return RecommendationValue(value=None, score=round(best_score, 3))
    return RecommendationValue(value=best_value, score=round(best_score, 3))


def build_recommendations_response(
    user_id: str, event_count: int, raw_scores: Dict[str, float]
) -> UserRecommendationsResponse:
    return UserRecommendationsResponse(
        user_id=user_id,
        event_count=event_count,
        preferred_departure_time=top_recommendation(raw_scores, "time_of_day:"),
        recommended_departure_city=top_recommendation(raw_scores, "departure_city:"),
        favorite_airline=top_recommendation(raw_scores, "airline:"),
    )


def build_global_recommendations_snapshot(
    events: List[RecoEvent],
) -> GlobalRecommendationsSnapshot:
    raw_scores = build_raw_scores(events)
    user_ids: Set[str] = {event.user_id for event in events if event.user_id}
    return GlobalRecommendationsSnapshot(
        event_count=len(events),
        user_count=len(user_ids),
        raw_scores=raw_scores,
    )
