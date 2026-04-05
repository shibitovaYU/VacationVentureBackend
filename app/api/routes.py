from fastapi import APIRouter, Depends

from app.auth import get_current_uid
from app.models import RecoEvent, UserRecommendationsResponse, UserVectorResponse
from app.services.recommendations import (
    build_raw_scores,
    build_recommendations_response,
    build_user_vector,
)
from app.storage.event_log import append_event, read_user_events
from app.storage.global_recommendations import read_global_recommendations


router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/events", status_code=204)
def ingest_event(event: RecoEvent, uid: str = Depends(get_current_uid)):
    append_event(uid, event)
    return None


@router.get("/users/me/vector", response_model=UserVectorResponse)
def get_user_vector(uid: str = Depends(get_current_uid)):
    events = read_user_events(uid)
    feature_order, vector, raw_scores = build_user_vector(events)
    return UserVectorResponse(
        user_id=uid,
        event_count=len(events),
        feature_order=feature_order,
        vector=vector,
        raw_scores=raw_scores,
    )


@router.get("/users/me/recommendations", response_model=UserRecommendationsResponse)
def get_user_recommendations(uid: str = Depends(get_current_uid)):
    events = read_user_events(uid)
    if events:
        return build_recommendations_response(
            user_id=uid,
            event_count=len(events),
            raw_scores=build_raw_scores(events),
        )

    snapshot = read_global_recommendations()
    fallback_scores = snapshot.raw_scores if snapshot else {}
    return build_recommendations_response(
        user_id=uid,
        event_count=0,
        raw_scores=fallback_scores,
    )
