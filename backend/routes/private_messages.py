"""
Private Messages routes (1-on-1 chat with conversation management):
- POST /private-messages
- GET /private-messages/conversations
- GET /private-messages/{other_user_id}
- POST /messages (legacy, send_message_legacy)
- GET /messages (legacy)
- GET /messages/{other_user_id} (legacy)
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Depends

from core import db, api_router
from models import User, PrivateMessageCreate
from dependencies import require_auth, is_minor, check_users_are_friends


# ==================== /private-messages routes ====================

@api_router.post("/private-messages")
async def send_private_message(data: PrivateMessageCreate, user: User = Depends(require_auth)):
    """Send a private message to another user"""
    receiver = await db.users.find_one({"user_id": data.receiver_id}, {"_id": 0})
    if not receiver:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    sender_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "birth_date": 1})
    sender_birth_date = sender_doc.get("birth_date") if sender_doc else None

    if is_minor(sender_birth_date):
        is_friend = await check_users_are_friends(user.user_id, data.receiver_id)
        if not is_friend:
            raise HTTPException(
                status_code=403,
                detail="Per la tua sicurezza, puoi chattare solo con i tuoi amici. Aggiungi questo utente come amico per iniziare una conversazione."
            )

    participants = sorted([user.user_id, data.receiver_id])
    conversation_id = f"{participants[0]}_{participants[1]}"

    message = {
        "message_id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "sender_id": user.user_id,
        "sender_name": user.name,
        "receiver_id": data.receiver_id,
        "receiver_name": receiver.get("name", "Utente"),
        "content": data.content,
        "read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.private_messages.insert_one(message)
    message.pop("_id", None)

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {
            "conversation_id": conversation_id,
            "participants": participants,
            "last_message": data.content[:100],
            "last_sender_id": user.user_id,
            "last_sender_name": user.name,
            "updated_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    return message


@api_router.get("/private-messages/conversations")
async def get_conversations(user: User = Depends(require_auth)):
    """Get list of conversations for the current user"""
    convos = await db.conversations.find(
        {"participants": user.user_id},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(50)

    result = []
    for c in convos:
        other_id = [p for p in c["participants"] if p != user.user_id][0]
        other_user = await db.users.find_one({"user_id": other_id}, {"_id": 0, "user_id": 1, "name": 1})
        unread = await db.private_messages.count_documents({
            "conversation_id": c["conversation_id"],
            "receiver_id": user.user_id,
            "read": False
        })
        result.append({
            "conversation_id": c["conversation_id"],
            "other_user_id": other_id,
            "other_user_name": other_user.get("name", "Utente") if other_user else "Utente",
            "last_message": c.get("last_message", ""),
            "last_sender_name": c.get("last_sender_name", ""),
            "unread_count": unread,
            "updated_at": c.get("updated_at", "")
        })
    return result


@api_router.get("/private-messages/{other_user_id}")
async def get_private_messages(other_user_id: str, user: User = Depends(require_auth)):
    """Get messages between current user and another user"""
    participants = sorted([user.user_id, other_user_id])
    conversation_id = f"{participants[0]}_{participants[1]}"

    messages = await db.private_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)

    await db.private_messages.update_many(
        {"conversation_id": conversation_id, "receiver_id": user.user_id, "read": False},
        {"$set": {"read": True}}
    )
    return messages


# ==================== Legacy /messages routes (uses is_read field, no conversation_id) ====================

@api_router.post("/messages")
async def send_message_legacy(data: PrivateMessageCreate, user: User = Depends(require_auth)):
    """Send a private message (legacy)"""
    receiver = await db.users.find_one({"user_id": data.receiver_id})
    if not receiver:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    message = {
        "message_id": str(uuid.uuid4()),
        "sender_id": user.user_id,
        "sender_name": user.name,
        "receiver_id": data.receiver_id,
        "content": data.content,
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.private_messages.insert_one(message)

    # Notify receiver
    await db.notifications.insert_one({
        "notification_id": str(uuid.uuid4()),
        "user_id": data.receiver_id,
        "title": "Nuovo messaggio",
        "body": f"{user.name} ti ha inviato un messaggio",
        "notification_type": "message",
        "data": {"sender_id": user.user_id, "message_id": message["message_id"]},
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    })

    message.pop("_id", None)
    return message


@api_router.get("/messages")
async def get_messages_legacy(user: User = Depends(require_auth)):
    """Get all conversations (legacy)"""
    sent = await db.private_messages.find(
        {"sender_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    received = await db.private_messages.find(
        {"receiver_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    all_messages = sent + received
    conversations = {}
    other_ids_needed = set()

    for msg in all_messages:
        other_id = msg["receiver_id"] if msg["sender_id"] == user.user_id else msg["sender_id"]
        other_ids_needed.add(other_id)

    if other_ids_needed:
        users_list = await db.users.find(
            {"user_id": {"$in": list(other_ids_needed)}},
            {"_id": 0, "password_hash": 0}
        ).to_list(len(other_ids_needed))
        user_map = {u["user_id"]: u for u in users_list}
    else:
        user_map = {}

    for msg in all_messages:
        other_id = msg["receiver_id"] if msg["sender_id"] == user.user_id else msg["sender_id"]
        if other_id not in conversations:
            other_user = user_map.get(other_id)
            conversations[other_id] = {
                "user_id": other_id,
                "user_name": other_user["name"] if other_user else "Utente",
                "last_message": msg,
                "unread_count": 0
            }
        if msg["receiver_id"] == user.user_id and not msg.get("is_read", False):
            conversations[other_id]["unread_count"] += 1

    return list(conversations.values())


@api_router.get("/messages/{other_user_id}")
async def get_conversation_legacy(other_user_id: str, user: User = Depends(require_auth)):
    """Get messages with a specific user (legacy)"""
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender_id": user.user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": user.user_id}
            ]
        },
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)

    await db.private_messages.update_many(
        {"sender_id": other_user_id, "receiver_id": user.user_id, "is_read": False},
        {"$set": {"is_read": True}}
    )

    return messages
