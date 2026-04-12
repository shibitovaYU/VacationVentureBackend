import math
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple

from app.models import (
    EventType,
    FlightRankingResponse,
    FlightSegment,
    GlobalRecommendationsSnapshot,
    RankedFlight,
    RecommendationValue,
    RecoEvent,
    UserRecommendationsResponse,
)


EVENT_TYPE_WEIGHTS: Dict[EventType, float] = {
    EventType.click: 1.0,
    EventType.favorite: 3.0,
    EventType.unfavorite: -4.0,
}


def extract_hour(departure_time: str) -> int:
    try:
        return datetime.fromisoformat(departure_time.replace("Z", "+00:00")).hour
    except ValueError:
        match = re.search(r"(?:^|[T\s])(\d{1,2}):", departure_time)
        if not match:
            raise
        return int(match.group(1))


def detect_time_of_day(departure_time: str) -> str:
    hour = extract_hour(departure_time)
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


def normalize_feature_scores(raw_scores: Dict[str, float]) -> Dict[str, float]:
    norm = math.sqrt(sum(value * value for value in raw_scores.values()))
    if norm == 0:
        return {feature_name: 0.0 for feature_name in raw_scores}
    return {
        feature_name: value / norm
        for feature_name, value in raw_scores.items()
    }


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
    normalized_scores = normalize_feature_scores(raw_scores)
    vector = [round(normalized_scores[name], 6) for name in feature_order]

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


def extract_airline_code_from_flight(flight: FlightSegment) -> str:
    carrier = flight.thread.carrier if flight.thread else None
    codes = carrier.codes if carrier else None
    for value in (
        codes.iata if codes else None,
        codes.sirena if codes else None,
        str(carrier.code) if carrier and carrier.code is not None else None,
        flight.thread.number[:2] if flight.thread and flight.thread.number else None,
    ):
        if value:
            return value.upper()
    return ""


def build_flight_feature_scores(flight: FlightSegment) -> Dict[str, float]:
    scores: Dict[str, float] = {}

    if flight.departure:
        try:
            scores[f"time_of_day:{detect_time_of_day(flight.departure)}"] = 1.0
        except (TypeError, ValueError):
            pass

    departure_station = flight.from_
    departure_city = None
    if flight.thread and flight.thread.title:
        departure_city = extract_departure_city(flight.thread.title)
    if departure_station:
        departure_city = departure_city or (
            departure_station.title
            or departure_station.popular_title
            or departure_station.short_title
            or departure_station.code
        )
    if departure_city:
        scores[f"departure_city:{departure_city.strip()}"] = 1.0

    airline_code = extract_airline_code_from_flight(flight)
    if airline_code:
        scores[f"airline:{airline_code}"] = 1.0

    return scores


def cosine_similarity(left_scores: Dict[str, float], right_scores: Dict[str, float]) -> float:
    if not left_scores or not right_scores:
        return 0.0

    left_vector = normalize_feature_scores(left_scores)
    right_vector = normalize_feature_scores(right_scores)
    dot_product = sum(
        left_vector.get(feature_name, 0.0) * right_vector.get(feature_name, 0.0)
        for feature_name in right_vector
    )
    return round(dot_product, 6)


def rank_flights(
    flights: List[FlightSegment],
    user_scores: Dict[str, float],
) -> FlightRankingResponse:
    scored_flights = [
        (
            index,
            cosine_similarity(user_scores, build_flight_feature_scores(flight)),
            flight,
        )
        for index, flight in enumerate(flights)
    ]
    scored_flights.sort(key=lambda item: (-item[1], item[0]))

    return FlightRankingResponse(
        ranked_flights=[
            RankedFlight(rank=rank, score=score, flight=flight)
            for rank, (_, score, flight) in enumerate(scored_flights, start=1)
        ]
    )
