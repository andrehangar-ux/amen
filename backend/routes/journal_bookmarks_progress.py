"""
Journal, Bookmarks and Progress routes:
- /journal (POST create with AI insight, GET list, DELETE)
- /bookmarks (POST, GET, DELETE)
- /progress (GET, POST reading streak, POST chapter, GET history)
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Depends, Query
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import db, logger, EMERGENT_LLM_KEY, api_router
from models import User, JournalCreate, BookmarkCreate
from dependencies import require_auth


# ==================== JOURNAL ====================

@api_router.post("/journal")
async def create_journal_entry(data: JournalCreate, user: User = Depends(require_auth)):
    try:
        lang = data.language or user.language or "it"

        lang_prompts = {
            "it": "Sei un consigliere spirituale. Offri una breve riflessione in italiano.",
            "es": "Eres un consejero espiritual. Ofrece una breve reflexión en español.",
            "en": "You are a spiritual counselor. Offer a brief reflection in English.",
            "pt": "Você é um conselheiro espiritual. Ofereça uma breve reflexão em português.",
            "fr": "Tu es un conseiller spirituel. Offre une brève réflexion en français.",
        }

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"journal_{user.user_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
            system_message=lang_prompts.get(lang, lang_prompts["it"])
        ).with_model("openai", "gpt-4o")

        prompt = f"L'utente si sente {data.mood} e ha scritto: \"{data.content[:500]}\". Offri una breve riflessione spirituale."
        ai_insight = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error(f"AI insight error: {e}")
        ai_insight = None

    entry = {
        "entry_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "content": data.content,
        "mood": data.mood,
        "language": data.language or user.language or "it",
        "ai_insight": ai_insight,
        "created_at": datetime.now(timezone.utc)
    }
    await db.journal_entries.insert_one(entry)

    await db.progress.update_one(
        {"user_id": user.user_id},
        {"$inc": {"total_journal_entries": 1}},
        upsert=True
    )

    entry.pop("_id", None)
    return entry


@api_router.get("/journal")
async def get_journal_entries(user: User = Depends(require_auth), limit: int = 50):
    entries = await db.journal_entries.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return entries


@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str, user: User = Depends(require_auth)):
    result = await db.journal_entries.delete_one({
        "entry_id": entry_id,
        "user_id": user.user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Voce non trovata")
    return {"message": "Voce eliminata"}


# ==================== BOOKMARKS ====================

@api_router.post("/bookmarks")
async def create_bookmark(data: BookmarkCreate, user: User = Depends(require_auth)):
    bookmark = {
        "bookmark_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc)
    }
    await db.bookmarks.insert_one(bookmark)
    bookmark.pop("_id", None)
    return bookmark


@api_router.get("/bookmarks")
async def get_bookmarks(user: User = Depends(require_auth)):
    bookmarks = await db.bookmarks.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return bookmarks


@api_router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, user: User = Depends(require_auth)):
    result = await db.bookmarks.delete_one({
        "bookmark_id": bookmark_id,
        "user_id": user.user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Segnalibro non trovato")
    return {"message": "Segnalibro eliminato"}


# ==================== PROGRESS ====================

@api_router.get("/progress")
async def get_progress(user: User = Depends(require_auth)):
    progress = await db.progress.find_one({"user_id": user.user_id}, {"_id": 0})
    if not progress:
        new_progress = {
            "user_id": user.user_id,
            "reading_streak": 0,
            "total_chapters_read": 0,
            "total_journal_entries": 0,
            "last_reading_date": None,
            "achievements": []
        }
        await db.progress.insert_one(new_progress)
        progress = {k: v for k, v in new_progress.items() if k != "_id"}
    return progress


@api_router.post("/progress/reading")
async def update_reading_progress(user: User = Depends(require_auth)):
    today = datetime.now(timezone.utc).date()
    progress = await db.progress.find_one({"user_id": user.user_id}, {"_id": 0})

    if progress:
        last_date = progress.get("last_reading_date")
        if last_date:
            if isinstance(last_date, datetime):
                last_date = last_date.date()

            if last_date == today:
                return progress
            elif (today - last_date).days == 1:
                await db.progress.update_one(
                    {"user_id": user.user_id},
                    {
                        "$inc": {"reading_streak": 1, "total_chapters_read": 1},
                        "$set": {"last_reading_date": datetime.now(timezone.utc)}
                    }
                )
            else:
                await db.progress.update_one(
                    {"user_id": user.user_id},
                    {
                        "$set": {"reading_streak": 1, "last_reading_date": datetime.now(timezone.utc)},
                        "$inc": {"total_chapters_read": 1}
                    }
                )
        else:
            await db.progress.update_one(
                {"user_id": user.user_id},
                {
                    "$set": {"reading_streak": 1, "last_reading_date": datetime.now(timezone.utc)},
                    "$inc": {"total_chapters_read": 1}
                }
            )
    else:
        await db.progress.insert_one({
            "user_id": user.user_id,
            "reading_streak": 1,
            "total_chapters_read": 1,
            "total_journal_entries": 0,
            "last_reading_date": datetime.now(timezone.utc),
            "achievements": []
        })

    return await db.progress.find_one({"user_id": user.user_id}, {"_id": 0})


@api_router.post("/progress/reading/chapter")
async def save_chapter_reading(
    book: str = Query(...),
    chapter: int = Query(...),
    user: User = Depends(require_auth)
):
    """Save a specific chapter as read and update reading history"""
    now = datetime.now(timezone.utc)

    existing = await db.reading_history.find_one({
        "user_id": user.user_id,
        "book": book,
        "chapter": chapter
    })

    if existing:
        await db.reading_history.update_one(
            {"_id": existing["_id"]},
            {"$set": {"last_read": now, "read_count": existing.get("read_count", 1) + 1}}
        )
    else:
        await db.reading_history.insert_one({
            "user_id": user.user_id,
            "book": book,
            "chapter": chapter,
            "first_read": now,
            "last_read": now,
            "read_count": 1
        })

    return {"success": True, "book": book, "chapter": chapter}


@api_router.get("/progress/reading/history")
async def get_reading_history(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_auth)
):
    """Get the user's reading history sorted by last read"""
    history = await db.reading_history.find(
        {"user_id": user.user_id},
        {"_id": 0, "user_id": 0}
    ).sort("last_read", -1).limit(limit).to_list(limit)

    return {"history": history, "total": len(history)}
