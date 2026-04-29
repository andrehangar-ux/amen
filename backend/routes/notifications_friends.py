"""
Notifications and Friends routes:
- /notifications, /notifications/unread-count, /notifications/{id}/read, /notifications/read-all
- /friends, /friends (POST add), /friends/{id} (DELETE), /friends/check/{id}
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Depends
from pydantic import BaseModel

from core import db, api_router
from models import User
from dependencies import require_auth


# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications")
async def get_notifications(user: User = Depends(require_auth), limit: int = 50):
    """Get user notifications"""
    notifications = await db.notifications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return notifications


@api_router.get("/notifications/unread-count")
async def get_unread_count(user: User = Depends(require_auth)):
    """Get unread notifications count"""
    count = await db.notifications.count_documents({
        "user_id": user.user_id,
        "is_read": False
    })
    return {"count": count}


@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: User = Depends(require_auth)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"notification_id": notification_id, "user_id": user.user_id},
        {"$set": {"is_read": True}}
    )
    return {"success": True}


@api_router.post("/notifications/read-all")
async def mark_all_read(user: User = Depends(require_auth)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"user_id": user.user_id},
        {"$set": {"is_read": True}}
    )
    return {"success": True}


# ==================== FRIENDS / FAVORITE USERS ====================

class FriendRequest(BaseModel):
    friend_id: str


@api_router.get("/friends")
async def get_friends(user: User = Depends(require_auth)):
    """Get user's friends list"""
    friendships = await db.friendships.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)

    friend_ids = [f["friend_id"] for f in friendships]

    if not friend_ids:
        return []

    # Bulk fetch users and heartbeats (avoid N+1)
    users_list = await db.users.find(
        {"user_id": {"$in": friend_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    user_map = {u["user_id"]: u for u in users_list}

    heartbeats_list = await db.user_heartbeats.find(
        {"user_id": {"$in": friend_ids}}
    ).to_list(100)
    heartbeat_map = {h["user_id"]: h for h in heartbeats_list}

    friends = []
    for friend_id in friend_ids:
        friend = user_map.get(friend_id)
        if friend:
            is_online = False
            heartbeat = heartbeat_map.get(friend_id)
            if heartbeat:
                last_seen = heartbeat.get("last_seen")
                if last_seen:
                    if last_seen.tzinfo is None:
                        last_seen = last_seen.replace(tzinfo=timezone.utc)
                    is_online = (datetime.now(timezone.utc) - last_seen).total_seconds() < 120

            friends.append({
                **friend,
                "is_online": is_online,
                "added_at": next((f["added_at"] for f in friendships if f["friend_id"] == friend_id), None)
            })

    return friends


@api_router.post("/friends")
async def add_friend(data: FriendRequest, user: User = Depends(require_auth)):
    """Add a user to friends list"""
    if data.friend_id == user.user_id:
        raise HTTPException(status_code=400, detail="Non puoi aggiungere te stesso")

    # Check if already friends
    existing = await db.friendships.find_one({
        "user_id": user.user_id,
        "friend_id": data.friend_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Utente già nei preferiti")

    # Check if friend exists
    friend = await db.users.find_one({"user_id": data.friend_id}, {"_id": 0})
    if not friend:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    friendship = {
        "friendship_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "friend_id": data.friend_id,
        "added_at": datetime.now(timezone.utc)
    }
    await db.friendships.insert_one(friendship)

    return {"message": "Utente aggiunto ai preferiti", "friend": friend}


@api_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user: User = Depends(require_auth)):
    """Remove a user from friends list"""
    result = await db.friendships.delete_one({
        "user_id": user.user_id,
        "friend_id": friend_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Amicizia non trovata")
    return {"message": "Utente rimosso dai preferiti"}


@api_router.get("/friends/check/{friend_id}")
async def check_friendship(friend_id: str, user: User = Depends(require_auth)):
    """Check if a user is in friends list"""
    friendship = await db.friendships.find_one({
        "user_id": user.user_id,
        "friend_id": friend_id
    })
    return {"is_friend": friendship is not None}
