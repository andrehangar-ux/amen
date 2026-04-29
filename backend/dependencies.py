"""
Shared dependencies and helpers used across all routes:
- Authentication (get_current_user, require_auth)
- Age helpers (calculate_age, is_minor)
- Friendship check
- Translation helper
- Content moderation

Imports from core.py (for db, logger, EMERGENT_LLM_KEY, etc.)
and models.py (for User).
"""
from fastapi import HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import re
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import db, logger, EMERGENT_LLM_KEY, SUPPORTED_LANGUAGES, BAD_WORDS
from models import User


# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    session_token = request.cookies.get("session_token")

    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")

    if not session_token:
        return None

    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None

    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None

    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if user_doc:
        return User(**user_doc)
    return None


async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Non autenticato")
    return user


# ==================== MINOR PROTECTION HELPERS ====================

def calculate_age(birth_date: str) -> Optional[int]:
    """Calculate age from birth_date string (YYYY-MM-DD)"""
    if not birth_date:
        return None
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except Exception:
        return None


def is_minor(birth_date: str) -> bool:
    """Check if user is under 18"""
    age = calculate_age(birth_date)
    return age is not None and age < 18


async def check_users_are_friends(user_id: str, other_user_id: str) -> bool:
    """Check if two users are friends"""
    friendship = await db.friendships.find_one({
        "$or": [
            {"user_id": user_id, "friend_id": other_user_id, "status": "accepted"},
            {"user_id": other_user_id, "friend_id": user_id, "status": "accepted"}
        ]
    })
    return friendship is not None


# ==================== TRANSLATION HELPER ====================

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using AI"""
    if source_lang == target_lang:
        return text

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate_{uuid.uuid4().hex[:8]}",
            system_message=f"You are a translator. Translate the following text from {SUPPORTED_LANGUAGES.get(source_lang, {}).get('name', source_lang)} to {SUPPORTED_LANGUAGES.get(target_lang, {}).get('name', target_lang)}. Only return the translated text, nothing else."
        ).with_model("openai", "gpt-4o")

        response = await chat.send_message(UserMessage(text=text))
        return response.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text


# ==================== CONTENT MODERATION ====================

def check_content_moderation(content: str, lang: str = "it") -> tuple:
    """Check content for offensive words. Returns (is_clean, filtered_content, warnings)"""
    content_lower = content.lower()
    warnings = []

    # Check all language bad words
    for lang_code, words in BAD_WORDS.items():
        for word in words:
            if word in content_lower:
                warnings.append("Parola non appropriata rilevata")
                # Replace with asterisks
                content = re.sub(re.escape(word), '*' * len(word), content, flags=re.IGNORECASE)

    is_clean = len(warnings) == 0
    return is_clean, content, warnings
