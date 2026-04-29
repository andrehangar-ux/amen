"""
Community routes - public message board:
- POST /community/messages (with content moderation + minor protection)
- GET /community/messages (with on-the-fly translation cache)
- POST /community/messages/{id}/translate
- POST /community/messages/{id}/like
- GET /community/users (list users for community interaction)
"""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, Depends

from core import db, logger, api_router
from models import User, CommunityMessageCreate
from dependencies import require_auth, is_minor, translate_text, check_content_moderation


@api_router.post("/community/messages")
async def create_community_message(data: CommunityMessageCreate, user: User = Depends(require_auth)):
    """Create a community message with content moderation"""
    user_doc = await db.users.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "birth_date": 1, "social_features_enabled": 1, "parent_pin": 1, "social_level": 1}
    )
    if user_doc and is_minor(user_doc.get("birth_date")):
        if not user_doc.get("parent_pin") or not user_doc.get("social_features_enabled", False):
            raise HTTPException(status_code=403, detail="Le funzionalita social non sono abilitate. Un genitore deve configurare il Controllo Genitori nelle Impostazioni.")

    is_clean, filtered_content, warnings = check_content_moderation(data.content, data.language)

    if warnings:
        logger.warning(f"Content moderation triggered for user {user.user_id}: {warnings}")

    message = {
        "message_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "user_country": user.country,
        "content": filtered_content,
        "original_language": data.language,
        "translations": {},
        "message_type": data.message_type,
        "likes": 0,
        "moderated": not is_clean,
        "created_at": datetime.now(timezone.utc)
    }
    await db.community_messages.insert_one(message)
    message.pop("_id", None)

    if warnings:
        message["moderation_warning"] = "Il tuo messaggio è stato moderato automaticamente"

    return message


@api_router.post("/community/messages/{message_id}/translate")
async def translate_message(message_id: str, target_lang: str = "it"):
    """Translate a specific message to target language"""
    message = await db.community_messages.find_one({"message_id": message_id}, {"_id": 0})
    if not message:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")

    if message["original_language"] == target_lang:
        return {"translated_text": message["content"], "is_original": True}

    if target_lang in message.get("translations", {}):
        return {"translated_text": message["translations"][target_lang], "is_original": False}

    translated = await translate_text(message["content"], message["original_language"], target_lang)
    await db.community_messages.update_one(
        {"message_id": message_id},
        {"$set": {f"translations.{target_lang}": translated}}
    )

    return {"translated_text": translated, "is_original": False}


@api_router.get("/community/messages")
async def get_community_messages(
    lang: str = "it",
    limit: int = 50,
    user: User = Depends(require_auth)
):
    """Get community messages with translations"""
    messages = await db.community_messages.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    for msg in messages:
        if msg["original_language"] != lang:
            if lang not in msg.get("translations", {}):
                translated = await translate_text(msg["content"], msg["original_language"], lang)
                await db.community_messages.update_one(
                    {"message_id": msg["message_id"]},
                    {"$set": {f"translations.{lang}": translated}}
                )
                msg["translated_content"] = translated
            else:
                msg["translated_content"] = msg["translations"].get(lang, msg["content"])
        else:
            msg["translated_content"] = msg["content"]

    return list(reversed(messages))


@api_router.post("/community/messages/{message_id}/like")
async def like_message(message_id: str, user: User = Depends(require_auth)):
    """Like a community message"""
    result = await db.community_messages.update_one(
        {"message_id": message_id},
        {"$inc": {"likes": 1}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    return {"success": True}


@api_router.get("/community/users")
async def get_community_users(q: str = "", user: User = Depends(require_auth)):
    """Get all registered users for community interaction"""
    query = {"user_id": {"$ne": user.user_id}}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    users = await db.users.find(
        query,
        {"_id": 0, "user_id": 1, "name": 1, "is_online": 1, "last_heartbeat": 1}
    ).sort("last_heartbeat", -1).limit(50).to_list(50)

    threshold = datetime.now(timezone.utc) - timedelta(minutes=2)
    for u in users:
        u["is_online"] = bool(u.get("is_online") and u.get("last_heartbeat") and u["last_heartbeat"] >= threshold)
        u.pop("last_heartbeat", None)
    return users
