"""
Live events endpoints (synchronized reading, worship, prayer, study).
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from core import api_router, db
from dependencies import require_auth
from models import User


class LiveEventCreate(BaseModel):
    title: str
    description: str
    event_type: str  # reading, worship, prayer, study
    scheduled_at: datetime
    duration_minutes: int = 60
    bible_book: Optional[str] = None
    bible_chapter: Optional[int] = None


@api_router.post("/events")
async def create_live_event(data: LiveEventCreate, user: User = Depends(require_auth)):
    """Create a live synchronized event"""
    event = {
        "event_id": str(uuid.uuid4()),
        "creator_id": user.user_id,
        "creator_name": user.name,
        "title": data.title,
        "description": data.description,
        "event_type": data.event_type,
        "scheduled_at": data.scheduled_at,
        "duration_minutes": data.duration_minutes,
        "bible_book": data.bible_book,
        "bible_chapter": data.bible_chapter,
        "participants": [user.user_id],
        "status": "scheduled",  # scheduled, live, ended
        "created_at": datetime.now(timezone.utc),
    }

    await db.live_events.insert_one(event)
    event.pop("_id", None)
    return event


@api_router.get("/events")
async def get_live_events(status: Optional[str] = None):
    """Get live events"""
    query = {}
    if status:
        query["status"] = status
    else:
        query["status"] = {"$in": ["scheduled", "live"]}

    events = await db.live_events.find(query, {"_id": 0}).sort("scheduled_at", 1).to_list(50)
    return events


@api_router.get("/events/{event_id}")
async def get_event(event_id: str):
    """Get single event details"""
    event = await db.live_events.find_one({"event_id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return event


@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, user: User = Depends(require_auth)):
    """Join a live event"""
    event = await db.live_events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")

    if user.user_id not in event.get("participants", []):
        await db.live_events.update_one(
            {"event_id": event_id},
            {"$push": {"participants": user.user_id}},
        )

    return {"success": True, "message": "Iscritto all'evento"}


@api_router.post("/events/{event_id}/start")
async def start_event(event_id: str, user: User = Depends(require_auth)):
    """Start a live event (creator only)"""
    event = await db.live_events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")

    if event["creator_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Solo il creatore può avviare l'evento")

    await db.live_events.update_one(
        {"event_id": event_id},
        {"$set": {"status": "live", "started_at": datetime.now(timezone.utc)}},
    )

    return {"success": True, "status": "live"}


@api_router.post("/events/{event_id}/end")
async def end_event(event_id: str, user: User = Depends(require_auth)):
    """End a live event"""
    event = await db.live_events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")

    if event["creator_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Solo il creatore può terminare l'evento")

    await db.live_events.update_one(
        {"event_id": event_id},
        {"$set": {"status": "ended", "ended_at": datetime.now(timezone.utc)}},
    )

    return {"success": True, "status": "ended"}
