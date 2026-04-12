import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class RankingBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CarrierCodes(RankingBaseModel):
    icao: Optional[str] = None
    sirena: Optional[str] = None
    iata: Optional[str] = None


class CarrierInfo(RankingBaseModel):
    code: Optional[int] = None
    title: Optional[str] = None
    codes: Optional[CarrierCodes] = None


class TransportSubtype(RankingBaseModel):
    color: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None


class ThreadInfo(RankingBaseModel):
    uid: Optional[str] = None
    title: Optional[str] = None
    number: Optional[str] = None
    short_title: Optional[str] = None
    carrier: Optional[CarrierInfo] = None
    transport_type: Optional[str] = None
    transport_subtype: Optional[TransportSubtype] = None


class Station(RankingBaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    popular_title: Optional[str] = None
    short_title: Optional[str] = None
    transport_type: Optional[str] = None


class TicketPrice(RankingBaseModel):
    cents: Optional[int] = None
    whole: Optional[int] = None


class Place(RankingBaseModel):
    currency: Optional[str] = None
    price: Optional[TicketPrice] = None
    name: Optional[str] = None


class TicketsInfo(RankingBaseModel):
    et_marker: Optional[bool] = None
    places: List[Place] = Field(default_factory=list)


class FlightSegment(RankingBaseModel):
    arrival: Optional[str] = None
    from_: Optional[Station] = Field(default=None, alias="from")
    thread: Optional[ThreadInfo] = None
    departure_platform: Optional[str] = None
    departure: Optional[str] = None
    stops: Optional[str] = None
    departure_terminal: Optional[str] = None
    to: Optional[Station] = None
    has_transfers: Optional[bool] = None
    tickets_info: Optional[TicketsInfo] = None
    duration: Optional[int] = None
    arrival_terminal: Optional[str] = None
    start_date: Optional[str] = None


class FlightRankingRequest(BaseModel):
    flights: List[FlightSegment]


class RankedFlight(BaseModel):
    rank: int
    score: float
    flight: FlightSegment


class FlightRankingResponse(BaseModel):
    ranked_flights: List[RankedFlight]
