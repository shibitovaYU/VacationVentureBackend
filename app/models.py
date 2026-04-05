import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    click = "click"
    favorite = "favorite"
    unfavorite = "unfavorite"


class SearchContext(BaseModel):
    from_code: str
    to_code: str
    when_date: str


class ItemCardSnapshot(BaseModel):
    item_id: str
    thread_uid: str
    title: str
    departure_time: str
    departure_station: str
    departure_date: str
    arrival_time: str
    arrival_station: str
    arrival_date: str
    duration_text: str
    detail_url: str


class RecoEvent(BaseModel):
    event_type: EventType
    occurred_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    user_id: Optional[str] = None
    search: SearchContext
    item: ItemCardSnapshot


class UserVectorResponse(BaseModel):
    user_id: str
    event_count: int
    feature_order: List[str]
    vector: List[float]
    raw_scores: Dict[str, float]


class RecommendationValue(BaseModel):
    value: Optional[str]
    score: float


class UserRecommendationsResponse(BaseModel):
    user_id: str
    event_count: int
    preferred_departure_time: RecommendationValue
    recommended_departure_city: RecommendationValue
    favorite_airline: RecommendationValue


class GlobalRecommendationsSnapshot(BaseModel):
    event_count: int
    user_count: int
    calculated_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    raw_scores: Dict[str, float]
