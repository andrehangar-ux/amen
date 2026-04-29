"""
Forum routes - Bible community discussion forum:
- /forum/categories
- /forum/posts (POST create, GET list)
- /forum/posts/{id} (GET single + replies)
- /forum/posts/{id}/vote
- /forum/posts/{id}/reply
- /forum/posts/{id}/ai-mentor (AI-generated wise spiritual response)
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, Depends
from pydantic import BaseModel
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import db, EMERGENT_LLM_KEY, api_router
from models import User
from dependencies import require_auth


class ForumPostCreate(BaseModel):
    title: str
    content: str
    category: str  # discussion, prayer, testimony, question, study
    tags: List[str] = []


class ForumReplyCreate(BaseModel):
    content: str


@api_router.get("/forum/categories")
async def get_forum_categories():
    """Get forum categories"""
    return [
        {"id": "discussion", "name": "Discussione Generale", "icon": "💬", "description": "Conversazioni sulla fede"},
        {"id": "prayer", "name": "Richieste di Preghiera", "icon": "🙏", "description": "Condividi le tue richieste"},
        {"id": "testimony", "name": "Testimonianze", "icon": "✨", "description": "Condividi la tua testimonianza"},
        {"id": "question", "name": "Domande Bibliche", "icon": "❓", "description": "Fai domande sulla Bibbia"},
        {"id": "study", "name": "Studio Biblico", "icon": "📖", "description": "Approfondimenti e studi"},
    ]


@api_router.post("/forum/posts")
async def create_forum_post(data: ForumPostCreate, user: User = Depends(require_auth)):
    """Create a forum post"""
    post = {
        "post_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "title": data.title,
        "content": data.content,
        "category": data.category,
        "tags": data.tags,
        "votes": 0,
        "voters": [],
        "replies_count": 0,
        "views": 0,
        "is_pinned": False,
        "is_approved": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await db.forum_posts.insert_one(post)
    post.pop("_id", None)
    return post


@api_router.get("/forum/posts")
async def get_forum_posts(
    category: Optional[str] = None,
    sort: str = "recent",
    limit: int = 30
):
    """Get forum posts"""
    query = {}
    if category:
        query["category"] = category

    sort_order = [("created_at", -1)]
    if sort == "popular":
        sort_order = [("votes", -1), ("created_at", -1)]
    elif sort == "unanswered":
        query["replies_count"] = 0

    posts = await db.forum_posts.find(query, {"_id": 0}).sort(sort_order).limit(limit).to_list(limit)
    return posts


@api_router.get("/forum/posts/{post_id}")
async def get_forum_post(post_id: str):
    """Get single forum post with replies"""
    post = await db.forum_posts.find_one({"post_id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")

    await db.forum_posts.update_one({"post_id": post_id}, {"$inc": {"views": 1}})

    replies = await db.forum_replies.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    post["replies"] = replies

    return post


@api_router.post("/forum/posts/{post_id}/vote")
async def vote_forum_post(post_id: str, user: User = Depends(require_auth)):
    """Vote on a forum post"""
    post = await db.forum_posts.find_one({"post_id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")

    voters = post.get("voters", [])
    if user.user_id in voters:
        await db.forum_posts.update_one(
            {"post_id": post_id},
            {"$inc": {"votes": -1}, "$pull": {"voters": user.user_id}}
        )
        return {"voted": False, "votes": post["votes"] - 1}
    else:
        await db.forum_posts.update_one(
            {"post_id": post_id},
            {"$inc": {"votes": 1}, "$push": {"voters": user.user_id}}
        )
        return {"voted": True, "votes": post["votes"] + 1}


@api_router.post("/forum/posts/{post_id}/reply")
async def reply_forum_post(post_id: str, data: ForumReplyCreate, user: User = Depends(require_auth)):
    """Reply to a forum post"""
    post = await db.forum_posts.find_one({"post_id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")

    reply = {
        "reply_id": str(uuid.uuid4()),
        "post_id": post_id,
        "user_id": user.user_id,
        "user_name": user.name,
        "content": data.content,
        "votes": 0,
        "voters": [],
        "is_ai_mentor": False,
        "created_at": datetime.now(timezone.utc)
    }

    await db.forum_replies.insert_one(reply)
    await db.forum_posts.update_one({"post_id": post_id}, {"$inc": {"replies_count": 1}})

    reply.pop("_id", None)
    return reply


@api_router.post("/forum/posts/{post_id}/ai-mentor")
async def get_ai_mentor_reply(post_id: str, user: User = Depends(require_auth)):
    """Get AI mentor response for a forum post"""
    post = await db.forum_posts.find_one({"post_id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mentor_{post_id}",
            system_message="""Sei un mentore spirituale cristiano saggio e compassionevole.
Il tuo ruolo è:
- Rispondere con saggezza biblica
- Essere incoraggiante e amorevole
- Citare versetti pertinenti
- Mantenere un tono rispettoso
- Se il contenuto è inappropriato, gentilmente reindirizza

Rispondi in italiano."""
        ).with_model("openai", "gpt-4o")

        prompt = f"Titolo del post: {post['title']}\n\nContenuto: {post['content']}\n\nCategoria: {post['category']}"
        response = await chat.send_message(UserMessage(text=prompt))

        mentor_reply = {
            "reply_id": str(uuid.uuid4()),
            "post_id": post_id,
            "user_id": "ai_mentor",
            "user_name": "🤖 Mentore AI",
            "content": response,
            "votes": 0,
            "voters": [],
            "is_ai_mentor": True,
            "created_at": datetime.now(timezone.utc)
        }
        await db.forum_replies.insert_one(mentor_reply)
        await db.forum_posts.update_one({"post_id": post_id}, {"$inc": {"replies_count": 1}})

        mentor_reply.pop("_id", None)
        return mentor_reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore AI Mentor: {str(e)}")
