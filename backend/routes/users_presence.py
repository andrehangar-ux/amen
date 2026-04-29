"""
User presence routes (heartbeat tracking) and user settings:
- POST /users/heartbeat
- GET /users/online
- POST /users/offline
- PUT /users/settings
"""
from datetime import datetime, timezone, timedelta

from fastapi import Depends, Request

from core import db, api_router
from models import User
from dependencies import require_auth


@api_router.post("/users/heartbeat")
async def user_heartbeat(user: User = Depends(require_auth)):
    """Update user's online status"""
    await db.user_presence.update_one(
        {"user_id": user.user_id},
        {
            "$set": {
                "user_id": user.user_id,
                "user_name": user.name,
                "last_seen": datetime.now(timezone.utc),
                "is_online": True
            }
        },
        upsert=True
    )
    return {"status": "ok"}


@api_router.get("/users/online")
async def get_online_users(user: User = Depends(require_auth)):
    """Get list of currently online users (active in last 5 minutes)"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    online_users = await db.user_presence.find(
        {"last_seen": {"$gte": cutoff_time}},
        {"_id": 0, "user_id": 1, "user_name": 1, "last_seen": 1}
    ).to_list(100)

    return {
        "online_count": len(online_users),
        "users": online_users
    }


@api_router.post("/users/offline")
async def user_offline(user: User = Depends(require_auth)):
    """Mark user as offline"""
    await db.user_presence.update_one(
        {"user_id": user.user_id},
        {"$set": {"is_online": False, "last_seen": datetime.now(timezone.utc)}}
    )
    return {"status": "offline"}


@api_router.put("/users/settings")
async def update_settings(request: Request, user: User = Depends(require_auth)):
    body = await request.json()
    allowed_fields = ["preferred_bible", "language", "name", "picture", "country", "bio", "is_public"]
    update_data = {k: v for k, v in body.items() if k in allowed_fields}

    if update_data:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": update_data}
        )

    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return updated_user
