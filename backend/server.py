from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import re
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage
from bible_data import NUOVA_DIODATI, REINA_VALERA_1960, get_bible_chapter

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'cibo_spirituale')]

# LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI(title="Amen! API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== SUPPORTED LANGUAGES ====================
SUPPORTED_LANGUAGES = {
    "it": {"name": "Italiano", "flag": "🇮🇹", "tts_code": "it-IT"},
    "es": {"name": "Español", "flag": "🇪🇸", "tts_code": "es-ES"},
    "en": {"name": "English", "flag": "🇬🇧", "tts_code": "en-US"},
    "pt": {"name": "Português", "flag": "🇧🇷", "tts_code": "pt-BR"},
    "fr": {"name": "Français", "flag": "🇫🇷", "tts_code": "fr-FR"},
    "de": {"name": "Deutsch", "flag": "🇩🇪", "tts_code": "de-DE"},
}

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    preferred_bible: str = "nuova_diodati"
    language: str = "it"
    country: Optional[str] = None
    bio: Optional[str] = None
    is_public: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    language: str = "it"
    country: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class JournalEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    mood: str
    language: str = "it"
    ai_insight: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JournalCreate(BaseModel):
    content: str
    mood: str
    language: str = "it"

class Bookmark(BaseModel):
    bookmark_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    book: str
    chapter: int
    verse: int
    text: str
    note: Optional[str] = None
    highlight_color: str = "#D4A574"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookmarkCreate(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str
    note: Optional[str] = None
    highlight_color: str = "#D4A574"

class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str
    mood: Optional[str] = None
    language: str = "it"

class MoodCheckIn(BaseModel):
    checkin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood: str
    verse_reference: str
    verse_text: str
    reflection: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MoodRequest(BaseModel):
    mood: str
    language: str = "it"

class Progress(BaseModel):
    user_id: str
    reading_streak: int = 0
    total_chapters_read: int = 0
    total_journal_entries: int = 0
    last_reading_date: Optional[datetime] = None
    achievements: List[str] = []

class DonationRequest(BaseModel):
    amount: float
    method: str
    message: Optional[str] = None

class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class CommunityMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_country: Optional[str] = None
    content: str
    original_language: str
    translations: Dict[str, str] = {}
    message_type: str = "text"  # text, audio, prayer_request
    likes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommunityMessageCreate(BaseModel):
    content: str
    language: str = "it"
    message_type: str = "text"

# ==================== NEW MODELS FOR GROUPS, NOTIFICATIONS, FEELINGS ====================

class FeelingRequest(BaseModel):
    text: str
    language: str = "it"

class BibleGroup(BaseModel):
    group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    topic: str  # prayer, study, testimony, support, worship
    creator_id: str
    creator_name: str
    members: List[str] = []
    is_public: bool = True
    language: str = "it"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupCreate(BaseModel):
    name: str
    description: str
    topic: str
    is_public: bool = True
    language: str = "it"

class GroupPost(BaseModel):
    post_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    user_id: str
    user_name: str
    content: str
    post_type: str = "text"  # text, prayer, verse, testimony
    bible_reference: Optional[str] = None
    likes: int = 0
    comments: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupPostCreate(BaseModel):
    content: str
    post_type: str = "text"
    bible_reference: Optional[str] = None

class PostComment(BaseModel):
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PrivateMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    sender_name: str
    receiver_id: str
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PrivateMessageCreate(BaseModel):
    receiver_id: str
    content: str

class Notification(BaseModel):
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    body: str
    notification_type: str  # verse, group, message, like, comment
    data: Dict = {}
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StudyNote(BaseModel):
    book: str
    chapter: int
    verse: int
    historical_context: str
    cross_references: List[str]
    hebrew_greek: Optional[str] = None
    application: str
    commentary: str

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

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/google-callback")
async def google_callback(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id mancante")
    
    async with httpx.AsyncClient() as http_client:
        auth_response = await http_client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Sessione non valida")
        
        user_data = auth_response.json()
    
    session_data = SessionDataResponse(**user_data)
    existing_user = await db.users.find_one({"email": session_data.email}, {"_id": 0})
    
    if not existing_user:
        new_user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": new_user_id,
            "email": session_data.email,
            "name": session_data.name,
            "picture": session_data.picture,
            "preferred_bible": "nuova_diodati",
            "language": "it",
            "country": None,
            "bio": None,
            "is_public": False,
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(new_user)
        user_id = new_user_id
    else:
        user_id = existing_user["user_id"]
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_data.session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    response.set_cookie(
        key="session_token",
        value=session_data.session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user, "session_token": session_data.session_token}

@api_router.post("/auth/register")
async def register(data: RegisterRequest, response: Response):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    import hashlib
    password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    
    user = {
        "user_id": user_id,
        "email": data.email,
        "name": data.name,
        "password_hash": password_hash,
        "picture": None,
        "preferred_bible": "nuova_diodati",
        "language": data.language,
        "country": data.country,
        "bio": None,
        "is_public": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.users.insert_one(user)
    
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user.pop("password_hash", None)
    user.pop("_id", None)
    return {"user": user, "session_token": session_token}

@api_router.post("/auth/login")
async def login(data: LoginRequest, response: Response):
    import hashlib
    password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    
    user = await db.users.find_one(
        {"email": data.email, "password_hash": password_hash}, 
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user.pop("password_hash", None)
    return {"user": user, "session_token": session_token}

@api_router.get("/auth/me")
async def get_me(user: User = Depends(require_auth)):
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Disconnesso con successo"}

@api_router.delete("/auth/delete-account")
async def delete_account(user: User = Depends(require_auth)):
    """Delete user account and all associated data (GDPR compliance)"""
    try:
        user_id = user.user_id
        
        # Delete all user data from various collections
        await db.users.delete_one({"user_id": user_id})
        await db.user_sessions.delete_many({"user_id": user_id})
        await db.journal_entries.delete_many({"user_id": user_id})
        await db.community_messages.delete_many({"user_id": user_id})
        await db.user_notes.delete_many({"user_id": user_id})
        await db.reading_progress.delete_many({"user_id": user_id})
        
        logger.info(f"Account deleted for user: {user_id}")
        
        return {"message": "Account e tutti i dati eliminati con successo"}
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'account")

# ==================== BIBLE EDITIONS ====================

BIBLE_EDITIONS = {
    "nuova_diodati": {
        "name": "Nuova Diodati",
        "language": "it",
        "year": "1991",
        "description": "Traduzione italiana moderna basata sul Textus Receptus"
    },
    "diodati_classica": {
        "name": "Diodati Classica",
        "language": "it",
        "year": "1607",
        "description": "La storica traduzione di Giovanni Diodati"
    },
    "cei": {
        "name": "CEI",
        "language": "it",
        "year": "2008",
        "description": "Traduzione della Conferenza Episcopale Italiana"
    },
    "reina_valera": {
        "name": "Reina Valera",
        "language": "es",
        "year": "1960",
        "description": "La clásica traducción española protestante"
    },
    "reina_valera_antigua": {
        "name": "Reina Valera Antigua",
        "language": "es",
        "year": "1569",
        "description": "La traducción original de Casiodoro de Reina"
    },
    "kjv": {
        "name": "King James Version",
        "language": "en",
        "year": "1611",
        "description": "The classic English translation"
    },
    "niv": {
        "name": "New International Version",
        "language": "en",
        "year": "1978",
        "description": "Modern English translation"
    },
    "almeida": {
        "name": "Almeida Revista",
        "language": "pt",
        "year": "1969",
        "description": "Tradução clássica portuguesa"
    },
    "louis_segond": {
        "name": "Louis Segond",
        "language": "fr",
        "year": "1910",
        "description": "Traduction française classique"
    },
    "luther": {
        "name": "Luther Bibel",
        "language": "de",
        "year": "1545",
        "description": "Die klassische deutsche Übersetzung"
    },
}

# ==================== LANGUAGES ENDPOINT ====================

@api_router.get("/languages")
async def get_languages():
    """Get all supported languages"""
    return SUPPORTED_LANGUAGES

@api_router.get("/bible/editions")
async def get_bible_editions(lang: str = None):
    """Get available Bible editions, optionally filtered by language"""
    if lang:
        return {k: v for k, v in BIBLE_EDITIONS.items() if v["language"] == lang}
    return BIBLE_EDITIONS

# ==================== TRANSLATION ENDPOINT ====================

@api_router.post("/translate")
async def translate(data: TranslateRequest, user: User = Depends(require_auth)):
    """Translate text between languages"""
    translated = await translate_text(data.text, data.source_lang, data.target_lang)
    return {
        "original": data.text,
        "translated": translated,
        "source_lang": data.source_lang,
        "target_lang": data.target_lang
    }

# ==================== MULTI-LANGUAGE BIBLE ====================

# Bible books in multiple languages
BIBLE_BOOKS_MULTILANG = {
    "it": [
        {"name": "Genesi", "chapters": 50, "abbrev": "Gen"},
        {"name": "Esodo", "chapters": 40, "abbrev": "Es"},
        {"name": "Levitico", "chapters": 27, "abbrev": "Lev"},
        {"name": "Numeri", "chapters": 36, "abbrev": "Num"},
        {"name": "Deuteronomio", "chapters": 34, "abbrev": "Deut"},
        {"name": "Giosuè", "chapters": 24, "abbrev": "Gios"},
        {"name": "Giudici", "chapters": 21, "abbrev": "Giud"},
        {"name": "Rut", "chapters": 4, "abbrev": "Rut"},
        {"name": "1 Samuele", "chapters": 31, "abbrev": "1Sam"},
        {"name": "2 Samuele", "chapters": 24, "abbrev": "2Sam"},
        {"name": "1 Re", "chapters": 22, "abbrev": "1Re"},
        {"name": "2 Re", "chapters": 25, "abbrev": "2Re"},
        {"name": "Salmi", "chapters": 150, "abbrev": "Sal"},
        {"name": "Proverbi", "chapters": 31, "abbrev": "Prov"},
        {"name": "Ecclesiaste", "chapters": 12, "abbrev": "Eccl"},
        {"name": "Isaia", "chapters": 66, "abbrev": "Is"},
        {"name": "Geremia", "chapters": 52, "abbrev": "Ger"},
        {"name": "Ezechiele", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniele", "chapters": 12, "abbrev": "Dan"},
        {"name": "Matteo", "chapters": 28, "abbrev": "Matt"},
        {"name": "Marco", "chapters": 16, "abbrev": "Mar"},
        {"name": "Luca", "chapters": 24, "abbrev": "Luc"},
        {"name": "Giovanni", "chapters": 21, "abbrev": "Giov"},
        {"name": "Atti", "chapters": 28, "abbrev": "Atti"},
        {"name": "Romani", "chapters": 16, "abbrev": "Rom"},
        {"name": "1 Corinzi", "chapters": 16, "abbrev": "1Cor"},
        {"name": "2 Corinzi", "chapters": 13, "abbrev": "2Cor"},
        {"name": "Galati", "chapters": 6, "abbrev": "Gal"},
        {"name": "Efesini", "chapters": 6, "abbrev": "Ef"},
        {"name": "Filippesi", "chapters": 4, "abbrev": "Fil"},
        {"name": "Colossesi", "chapters": 4, "abbrev": "Col"},
        {"name": "Ebrei", "chapters": 13, "abbrev": "Ebr"},
        {"name": "Giacomo", "chapters": 5, "abbrev": "Giac"},
        {"name": "1 Pietro", "chapters": 5, "abbrev": "1Pt"},
        {"name": "2 Pietro", "chapters": 3, "abbrev": "2Pt"},
        {"name": "1 Giovanni", "chapters": 5, "abbrev": "1Giov"},
        {"name": "Apocalisse", "chapters": 22, "abbrev": "Apoc"},
    ],
    "es": [
        {"name": "Génesis", "chapters": 50, "abbrev": "Gén"},
        {"name": "Éxodo", "chapters": 40, "abbrev": "Éx"},
        {"name": "Levítico", "chapters": 27, "abbrev": "Lev"},
        {"name": "Números", "chapters": 36, "abbrev": "Núm"},
        {"name": "Deuteronomio", "chapters": 34, "abbrev": "Deut"},
        {"name": "Josué", "chapters": 24, "abbrev": "Jos"},
        {"name": "Jueces", "chapters": 21, "abbrev": "Jue"},
        {"name": "Rut", "chapters": 4, "abbrev": "Rut"},
        {"name": "1 Samuel", "chapters": 31, "abbrev": "1Sam"},
        {"name": "2 Samuel", "chapters": 24, "abbrev": "2Sam"},
        {"name": "1 Reyes", "chapters": 22, "abbrev": "1Re"},
        {"name": "2 Reyes", "chapters": 25, "abbrev": "2Re"},
        {"name": "Salmos", "chapters": 150, "abbrev": "Sal"},
        {"name": "Proverbios", "chapters": 31, "abbrev": "Prov"},
        {"name": "Eclesiastés", "chapters": 12, "abbrev": "Ecl"},
        {"name": "Isaías", "chapters": 66, "abbrev": "Is"},
        {"name": "Jeremías", "chapters": 52, "abbrev": "Jer"},
        {"name": "Ezequiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Mateo", "chapters": 28, "abbrev": "Mat"},
        {"name": "Marcos", "chapters": 16, "abbrev": "Mar"},
        {"name": "Lucas", "chapters": 24, "abbrev": "Luc"},
        {"name": "Juan", "chapters": 21, "abbrev": "Jn"},
        {"name": "Hechos", "chapters": 28, "abbrev": "Hch"},
        {"name": "Romanos", "chapters": 16, "abbrev": "Rom"},
        {"name": "1 Corintios", "chapters": 16, "abbrev": "1Cor"},
        {"name": "2 Corintios", "chapters": 13, "abbrev": "2Cor"},
        {"name": "Gálatas", "chapters": 6, "abbrev": "Gál"},
        {"name": "Efesios", "chapters": 6, "abbrev": "Ef"},
        {"name": "Filipenses", "chapters": 4, "abbrev": "Fil"},
        {"name": "Colosenses", "chapters": 4, "abbrev": "Col"},
        {"name": "Hebreos", "chapters": 13, "abbrev": "Heb"},
        {"name": "Santiago", "chapters": 5, "abbrev": "Stg"},
        {"name": "1 Pedro", "chapters": 5, "abbrev": "1Pe"},
        {"name": "2 Pedro", "chapters": 3, "abbrev": "2Pe"},
        {"name": "1 Juan", "chapters": 5, "abbrev": "1Jn"},
        {"name": "Apocalipsis", "chapters": 22, "abbrev": "Ap"},
    ],
    "en": [
        {"name": "Genesis", "chapters": 50, "abbrev": "Gen"},
        {"name": "Exodus", "chapters": 40, "abbrev": "Ex"},
        {"name": "Leviticus", "chapters": 27, "abbrev": "Lev"},
        {"name": "Numbers", "chapters": 36, "abbrev": "Num"},
        {"name": "Deuteronomy", "chapters": 34, "abbrev": "Deut"},
        {"name": "Joshua", "chapters": 24, "abbrev": "Josh"},
        {"name": "Judges", "chapters": 21, "abbrev": "Judg"},
        {"name": "Ruth", "chapters": 4, "abbrev": "Ruth"},
        {"name": "1 Samuel", "chapters": 31, "abbrev": "1Sam"},
        {"name": "2 Samuel", "chapters": 24, "abbrev": "2Sam"},
        {"name": "1 Kings", "chapters": 22, "abbrev": "1Ki"},
        {"name": "2 Kings", "chapters": 25, "abbrev": "2Ki"},
        {"name": "Psalms", "chapters": 150, "abbrev": "Ps"},
        {"name": "Proverbs", "chapters": 31, "abbrev": "Prov"},
        {"name": "Ecclesiastes", "chapters": 12, "abbrev": "Eccl"},
        {"name": "Isaiah", "chapters": 66, "abbrev": "Isa"},
        {"name": "Jeremiah", "chapters": 52, "abbrev": "Jer"},
        {"name": "Ezekiel", "chapters": 48, "abbrev": "Ezek"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Matthew", "chapters": 28, "abbrev": "Matt"},
        {"name": "Mark", "chapters": 16, "abbrev": "Mark"},
        {"name": "Luke", "chapters": 24, "abbrev": "Luke"},
        {"name": "John", "chapters": 21, "abbrev": "John"},
        {"name": "Acts", "chapters": 28, "abbrev": "Acts"},
        {"name": "Romans", "chapters": 16, "abbrev": "Rom"},
        {"name": "1 Corinthians", "chapters": 16, "abbrev": "1Cor"},
        {"name": "2 Corinthians", "chapters": 13, "abbrev": "2Cor"},
        {"name": "Galatians", "chapters": 6, "abbrev": "Gal"},
        {"name": "Ephesians", "chapters": 6, "abbrev": "Eph"},
        {"name": "Philippians", "chapters": 4, "abbrev": "Phil"},
        {"name": "Colossians", "chapters": 4, "abbrev": "Col"},
        {"name": "Hebrews", "chapters": 13, "abbrev": "Heb"},
        {"name": "James", "chapters": 5, "abbrev": "Jas"},
        {"name": "1 Peter", "chapters": 5, "abbrev": "1Pet"},
        {"name": "2 Peter", "chapters": 3, "abbrev": "2Pet"},
        {"name": "1 John", "chapters": 5, "abbrev": "1John"},
        {"name": "Revelation", "chapters": 22, "abbrev": "Rev"},
    ],
    "pt": [
        {"name": "Gênesis", "chapters": 50, "abbrev": "Gn"},
        {"name": "Êxodo", "chapters": 40, "abbrev": "Êx"},
        {"name": "Levítico", "chapters": 27, "abbrev": "Lv"},
        {"name": "Números", "chapters": 36, "abbrev": "Nm"},
        {"name": "Deuteronômio", "chapters": 34, "abbrev": "Dt"},
        {"name": "Josué", "chapters": 24, "abbrev": "Js"},
        {"name": "Juízes", "chapters": 21, "abbrev": "Jz"},
        {"name": "Rute", "chapters": 4, "abbrev": "Rt"},
        {"name": "1 Samuel", "chapters": 31, "abbrev": "1Sm"},
        {"name": "2 Samuel", "chapters": 24, "abbrev": "2Sm"},
        {"name": "1 Reis", "chapters": 22, "abbrev": "1Rs"},
        {"name": "2 Reis", "chapters": 25, "abbrev": "2Rs"},
        {"name": "Salmos", "chapters": 150, "abbrev": "Sl"},
        {"name": "Provérbios", "chapters": 31, "abbrev": "Pv"},
        {"name": "Eclesiastes", "chapters": 12, "abbrev": "Ec"},
        {"name": "Isaías", "chapters": 66, "abbrev": "Is"},
        {"name": "Jeremias", "chapters": 52, "abbrev": "Jr"},
        {"name": "Ezequiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dn"},
        {"name": "Mateus", "chapters": 28, "abbrev": "Mt"},
        {"name": "Marcos", "chapters": 16, "abbrev": "Mc"},
        {"name": "Lucas", "chapters": 24, "abbrev": "Lc"},
        {"name": "João", "chapters": 21, "abbrev": "Jo"},
        {"name": "Atos", "chapters": 28, "abbrev": "At"},
        {"name": "Romanos", "chapters": 16, "abbrev": "Rm"},
        {"name": "1 Coríntios", "chapters": 16, "abbrev": "1Co"},
        {"name": "2 Coríntios", "chapters": 13, "abbrev": "2Co"},
        {"name": "Gálatas", "chapters": 6, "abbrev": "Gl"},
        {"name": "Efésios", "chapters": 6, "abbrev": "Ef"},
        {"name": "Filipenses", "chapters": 4, "abbrev": "Fp"},
        {"name": "Colossenses", "chapters": 4, "abbrev": "Cl"},
        {"name": "Hebreus", "chapters": 13, "abbrev": "Hb"},
        {"name": "Tiago", "chapters": 5, "abbrev": "Tg"},
        {"name": "1 Pedro", "chapters": 5, "abbrev": "1Pe"},
        {"name": "2 Pedro", "chapters": 3, "abbrev": "2Pe"},
        {"name": "1 João", "chapters": 5, "abbrev": "1Jo"},
        {"name": "Apocalipse", "chapters": 22, "abbrev": "Ap"},
    ],
    "fr": [
        {"name": "Genèse", "chapters": 50, "abbrev": "Gn"},
        {"name": "Exode", "chapters": 40, "abbrev": "Ex"},
        {"name": "Lévitique", "chapters": 27, "abbrev": "Lv"},
        {"name": "Nombres", "chapters": 36, "abbrev": "Nb"},
        {"name": "Deutéronome", "chapters": 34, "abbrev": "Dt"},
        {"name": "Josué", "chapters": 24, "abbrev": "Jos"},
        {"name": "Juges", "chapters": 21, "abbrev": "Jg"},
        {"name": "Ruth", "chapters": 4, "abbrev": "Rt"},
        {"name": "1 Samuel", "chapters": 31, "abbrev": "1S"},
        {"name": "2 Samuel", "chapters": 24, "abbrev": "2S"},
        {"name": "1 Rois", "chapters": 22, "abbrev": "1R"},
        {"name": "2 Rois", "chapters": 25, "abbrev": "2R"},
        {"name": "Psaumes", "chapters": 150, "abbrev": "Ps"},
        {"name": "Proverbes", "chapters": 31, "abbrev": "Pr"},
        {"name": "Ecclésiaste", "chapters": 12, "abbrev": "Ec"},
        {"name": "Ésaïe", "chapters": 66, "abbrev": "Es"},
        {"name": "Jérémie", "chapters": 52, "abbrev": "Jr"},
        {"name": "Ézéchiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dn"},
        {"name": "Matthieu", "chapters": 28, "abbrev": "Mt"},
        {"name": "Marc", "chapters": 16, "abbrev": "Mc"},
        {"name": "Luc", "chapters": 24, "abbrev": "Lc"},
        {"name": "Jean", "chapters": 21, "abbrev": "Jn"},
        {"name": "Actes", "chapters": 28, "abbrev": "Ac"},
        {"name": "Romains", "chapters": 16, "abbrev": "Rm"},
        {"name": "1 Corinthiens", "chapters": 16, "abbrev": "1Co"},
        {"name": "2 Corinthiens", "chapters": 13, "abbrev": "2Co"},
        {"name": "Galates", "chapters": 6, "abbrev": "Ga"},
        {"name": "Éphésiens", "chapters": 6, "abbrev": "Ep"},
        {"name": "Philippiens", "chapters": 4, "abbrev": "Ph"},
        {"name": "Colossiens", "chapters": 4, "abbrev": "Col"},
        {"name": "Hébreux", "chapters": 13, "abbrev": "He"},
        {"name": "Jacques", "chapters": 5, "abbrev": "Jc"},
        {"name": "1 Pierre", "chapters": 5, "abbrev": "1P"},
        {"name": "2 Pierre", "chapters": 3, "abbrev": "2P"},
        {"name": "1 Jean", "chapters": 5, "abbrev": "1Jn"},
        {"name": "Apocalypse", "chapters": 22, "abbrev": "Ap"},
    ],
    "de": [
        {"name": "Genesis", "chapters": 50, "abbrev": "1Mo"},
        {"name": "Exodus", "chapters": 40, "abbrev": "2Mo"},
        {"name": "Levitikus", "chapters": 27, "abbrev": "3Mo"},
        {"name": "Numeri", "chapters": 36, "abbrev": "4Mo"},
        {"name": "Deuteronomium", "chapters": 34, "abbrev": "5Mo"},
        {"name": "Josua", "chapters": 24, "abbrev": "Jos"},
        {"name": "Richter", "chapters": 21, "abbrev": "Ri"},
        {"name": "Ruth", "chapters": 4, "abbrev": "Rt"},
        {"name": "1 Samuel", "chapters": 31, "abbrev": "1Sam"},
        {"name": "2 Samuel", "chapters": 24, "abbrev": "2Sam"},
        {"name": "1 Könige", "chapters": 22, "abbrev": "1Kö"},
        {"name": "2 Könige", "chapters": 25, "abbrev": "2Kö"},
        {"name": "Psalmen", "chapters": 150, "abbrev": "Ps"},
        {"name": "Sprüche", "chapters": 31, "abbrev": "Spr"},
        {"name": "Prediger", "chapters": 12, "abbrev": "Pred"},
        {"name": "Jesaja", "chapters": 66, "abbrev": "Jes"},
        {"name": "Jeremia", "chapters": 52, "abbrev": "Jer"},
        {"name": "Hesekiel", "chapters": 48, "abbrev": "Hes"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Matthäus", "chapters": 28, "abbrev": "Mt"},
        {"name": "Markus", "chapters": 16, "abbrev": "Mk"},
        {"name": "Lukas", "chapters": 24, "abbrev": "Lk"},
        {"name": "Johannes", "chapters": 21, "abbrev": "Joh"},
        {"name": "Apostelgeschichte", "chapters": 28, "abbrev": "Apg"},
        {"name": "Römer", "chapters": 16, "abbrev": "Röm"},
        {"name": "1 Korinther", "chapters": 16, "abbrev": "1Kor"},
        {"name": "2 Korinther", "chapters": 13, "abbrev": "2Kor"},
        {"name": "Galater", "chapters": 6, "abbrev": "Gal"},
        {"name": "Epheser", "chapters": 6, "abbrev": "Eph"},
        {"name": "Philipper", "chapters": 4, "abbrev": "Phil"},
        {"name": "Kolosser", "chapters": 4, "abbrev": "Kol"},
        {"name": "Hebräer", "chapters": 13, "abbrev": "Heb"},
        {"name": "Jakobus", "chapters": 5, "abbrev": "Jak"},
        {"name": "1 Petrus", "chapters": 5, "abbrev": "1Pt"},
        {"name": "2 Petrus", "chapters": 3, "abbrev": "2Pt"},
        {"name": "1 Johannes", "chapters": 5, "abbrev": "1Joh"},
        {"name": "Offenbarung", "chapters": 22, "abbrev": "Offb"},
    ],
}

# Sample verses in multiple languages
SAMPLE_VERSES_MULTILANG = {
    "it": {
        "Giovanni:3": [
            {"verse": 16, "text": "Poiché Dio ha tanto amato il mondo, che ha dato il suo unigenito Figlio, affinché chiunque crede in lui non perisca, ma abbia vita eterna."},
        ],
        "Salmi:23": [
            {"verse": 1, "text": "L'Eterno è il mio pastore, nulla mi mancherà."},
            {"verse": 2, "text": "Egli mi fa riposare in verdi pascoli, mi guida lungo le acque tranquille."},
            {"verse": 3, "text": "Egli ristora la mia anima, mi guida per sentieri di giustizia per amore del suo nome."},
            {"verse": 4, "text": "Anche se camminassi nella valle dell'ombra della morte, non temerei alcun male, perché tu sei con me."},
        ],
        "Romani:8": [
            {"verse": 28, "text": "Or noi sappiamo che tutte le cose cooperano al bene di quelli che amano Dio."},
            {"verse": 31, "text": "Che diremo dunque di queste cose? Se Dio è per noi, chi sarà contro di noi?"},
        ],
        "Filippesi:4": [
            {"verse": 13, "text": "Io posso ogni cosa in Cristo che mi fortifica."},
        ],
    },
    "es": {
        "Juan:3": [
            {"verse": 16, "text": "Porque de tal manera amó Dios al mundo, que ha dado a su Hijo unigénito, para que todo aquel que en él cree, no se pierda, mas tenga vida eterna."},
        ],
        "Salmos:23": [
            {"verse": 1, "text": "Jehová es mi pastor; nada me faltará."},
            {"verse": 2, "text": "En lugares de delicados pastos me hará descansar; junto a aguas de reposo me pastoreará."},
            {"verse": 3, "text": "Confortará mi alma; me guiará por sendas de justicia por amor de su nombre."},
            {"verse": 4, "text": "Aunque ande en valle de sombra de muerte, no temeré mal alguno, porque tú estarás conmigo."},
        ],
        "Romanos:8": [
            {"verse": 28, "text": "Y sabemos que a los que aman a Dios, todas las cosas les ayudan a bien."},
            {"verse": 31, "text": "¿Qué, pues, diremos a esto? Si Dios es por nosotros, ¿quién contra nosotros?"},
        ],
        "Filipenses:4": [
            {"verse": 13, "text": "Todo lo puedo en Cristo que me fortalece."},
        ],
    },
    "en": {
        "John:3": [
            {"verse": 16, "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."},
        ],
        "Psalms:23": [
            {"verse": 1, "text": "The Lord is my shepherd; I shall not want."},
            {"verse": 2, "text": "He maketh me to lie down in green pastures: he leadeth me beside the still waters."},
            {"verse": 3, "text": "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake."},
            {"verse": 4, "text": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me."},
        ],
        "Romans:8": [
            {"verse": 28, "text": "And we know that all things work together for good to them that love God."},
            {"verse": 31, "text": "What shall we then say to these things? If God be for us, who can be against us?"},
        ],
        "Philippians:4": [
            {"verse": 13, "text": "I can do all things through Christ which strengtheneth me."},
        ],
    },
    "pt": {
        "João:3": [
            {"verse": 16, "text": "Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna."},
        ],
        "Salmos:23": [
            {"verse": 1, "text": "O Senhor é o meu pastor; nada me faltará."},
            {"verse": 2, "text": "Deitar-me faz em verdes pastos, guia-me mansamente a águas tranquilas."},
            {"verse": 3, "text": "Refrigera a minha alma; guia-me pelas veredas da justiça, por amor do seu nome."},
            {"verse": 4, "text": "Ainda que eu andasse pelo vale da sombra da morte, não temeria mal algum, porque tu estás comigo."},
        ],
    },
    "fr": {
        "Jean:3": [
            {"verse": 16, "text": "Car Dieu a tant aimé le monde qu'il a donné son Fils unique, afin que quiconque croit en lui ne périsse point, mais qu'il ait la vie éternelle."},
        ],
        "Psaumes:23": [
            {"verse": 1, "text": "L'Éternel est mon berger: je ne manquerai de rien."},
            {"verse": 2, "text": "Il me fait reposer dans de verts pâturages, il me dirige près des eaux paisibles."},
            {"verse": 3, "text": "Il restaure mon âme, il me conduit dans les sentiers de la justice, à cause de son nom."},
            {"verse": 4, "text": "Quand je marche dans la vallée de l'ombre de la mort, je ne crains aucun mal, car tu es avec moi."},
        ],
    },
}

# Mood verses in multiple languages
MOOD_VERSES_MULTILANG = {
    "it": {
        "felice": [{"ref": "Salmi 118:24", "text": "Questo è il giorno che l'Eterno ha fatto; rallegriamoci e gioisciamo in esso."}],
        "triste": [{"ref": "Salmi 34:18", "text": "L'Eterno è vicino a quelli che hanno il cuore rotto."}],
        "ansioso": [{"ref": "Filippesi 4:6-7", "text": "Non angustiatevi di nulla, ma in ogni cosa fate conoscere le vostre richieste a Dio."}],
        "arrabbiato": [{"ref": "Efesini 4:26", "text": "Adiratevi e non peccate; il sole non tramonti sopra la vostra ira."}],
        "grato": [{"ref": "1 Tessalonicesi 5:18", "text": "In ogni cosa rendete grazie."}],
        "confuso": [{"ref": "Proverbi 3:5-6", "text": "Confida nell'Eterno con tutto il cuore e non appoggiarti sul tuo intendimento."}],
        "speranzoso": [{"ref": "Geremia 29:11", "text": "Poiché io conosco i pensieri che ho per voi, pensieri di pace e non di male."}],
        "stanco": [{"ref": "Matteo 11:28", "text": "Venite a me, voi tutti che siete travagliati e aggravati, e io vi darò riposo."}],
    },
    "es": {
        "felice": [{"ref": "Salmos 118:24", "text": "Este es el día que hizo Jehová; nos gozaremos y alegraremos en él."}],
        "triste": [{"ref": "Salmos 34:18", "text": "Cercano está Jehová a los quebrantados de corazón."}],
        "ansioso": [{"ref": "Filipenses 4:6-7", "text": "Por nada estéis afanosos, sino sean conocidas vuestras peticiones delante de Dios."}],
        "stanco": [{"ref": "Mateo 11:28", "text": "Venid a mí todos los que estáis trabajados y cargados, y yo os haré descansar."}],
    },
    "en": {
        "felice": [{"ref": "Psalm 118:24", "text": "This is the day which the Lord hath made; we will rejoice and be glad in it."}],
        "triste": [{"ref": "Psalm 34:18", "text": "The Lord is nigh unto them that are of a broken heart."}],
        "ansioso": [{"ref": "Philippians 4:6-7", "text": "Be careful for nothing; but in every thing by prayer let your requests be made known unto God."}],
        "stanco": [{"ref": "Matthew 11:28", "text": "Come unto me, all ye that labour and are heavy laden, and I will give you rest."}],
    },
    "pt": {
        "felice": [{"ref": "Salmos 118:24", "text": "Este é o dia que o Senhor fez; regozijemo-nos e alegremo-nos nele."}],
        "triste": [{"ref": "Salmos 34:18", "text": "Perto está o Senhor dos que têm o coração quebrantado."}],
        "stanco": [{"ref": "Mateus 11:28", "text": "Vinde a mim, todos os que estais cansados e oprimidos, e eu vos aliviarei."}],
    },
    "fr": {
        "felice": [{"ref": "Psaume 118:24", "text": "C'est ici la journée que l'Éternel a faite: Qu'elle soit pour nous un sujet d'allégresse et de joie!"}],
        "triste": [{"ref": "Psaume 34:18", "text": "L'Éternel est près de ceux qui ont le cœur brisé."}],
        "stanco": [{"ref": "Matthieu 11:28", "text": "Venez à moi, vous tous qui êtes fatigués et chargés, et je vous donnerai du repos."}],
    },
}

@api_router.get("/bible/books")
async def get_bible_books(lang: str = "it"):
    """Get list of Bible books in specified language"""
    return BIBLE_BOOKS_MULTILANG.get(lang, BIBLE_BOOKS_MULTILANG["it"])

# Helper function to fetch Bible text from laparola.net
async def fetch_from_laparola(book: str, chapter: int, version: str = "Nuova+Diodati") -> list:
    """Fetch Bible chapter from laparola.net"""
    try:
        # Map Italian book names to URL-friendly format
        book_url = book.lower().replace(" ", "+")
        url = f"https://www.laparola.net/testo.php?riferimento={book_url}+{chapter}&versioni[]={version}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                logger.error(f"laparola.net returned status {response.status_code}")
                return []
            
            html_content = response.text
            
            # Find the brano div content
            brano_match = re.search(r'<div id="brano">(.*?)</div><!-- RESULT LIST END -->', html_content, re.DOTALL)
            if not brano_match:
                logger.warning("Could not find brano div in laparola.net response")
                return []
            
            brano_content = brano_match.group(1)
            
            # Extract verses using <strong>number</strong> pattern
            # Pattern: <strong>1</strong>&nbsp;text until next <strong> or end
            verse_pattern = r'<strong>(\d+)</strong>&nbsp;(.*?)(?=<strong>\d+</strong>|<br\s*/?>|</p>|$)'
            matches = re.findall(verse_pattern, brano_content, re.DOTALL)
            
            verses = []
            for match in matches:
                verse_num = int(match[0])
                verse_text = match[1].strip()
                
                # Clean up HTML entities and tags
                verse_text = re.sub(r'<[^>]+>', '', verse_text)  # Remove HTML tags
                verse_text = verse_text.replace('&nbsp;', ' ')
                verse_text = verse_text.replace('&laquo;', '«')
                verse_text = verse_text.replace('&raquo;', '»')
                verse_text = verse_text.replace('&egrave;', 'è')
                verse_text = verse_text.replace('&eacute;', 'é')
                verse_text = verse_text.replace('&igrave;', 'ì')
                verse_text = verse_text.replace('&ograve;', 'ò')
                verse_text = verse_text.replace('&ugrave;', 'ù')
                verse_text = verse_text.replace('&agrave;', 'à')
                verse_text = verse_text.replace('&Egrave;', 'È')
                verse_text = verse_text.replace('&#39;', "'")
                verse_text = re.sub(r'&[a-z]+;', '', verse_text)  # Remove remaining entities
                verse_text = ' '.join(verse_text.split())  # Normalize whitespace
                
                if verse_text and len(verse_text) > 3:
                    verses.append({"verse": verse_num, "text": verse_text})
            
            # Sort by verse number and return
            verses.sort(key=lambda x: x["verse"])
            logger.info(f"Fetched {len(verses)} verses from laparola.net for {book} {chapter}")
            return verses
            
    except Exception as e:
        logger.error(f"Error fetching from laparola.net: {e}")
        return []

# Mapping nomi libri per diverse lingue/API
BOOK_NAME_MAPPING = {
    "Genesi": {"en": "Genesis", "es": "Génesis", "de": "Genesis", "fr": "Genèse", "pt": "Gênesis"},
    "Esodo": {"en": "Exodus", "es": "Éxodo", "de": "Exodus", "fr": "Exode", "pt": "Êxodo"},
    "Levitico": {"en": "Leviticus", "es": "Levítico", "de": "Levitikus", "fr": "Lévitique", "pt": "Levítico"},
    "Numeri": {"en": "Numbers", "es": "Números", "de": "Numeri", "fr": "Nombres", "pt": "Números"},
    "Deuteronomio": {"en": "Deuteronomy", "es": "Deuteronomio", "de": "Deuteronomium", "fr": "Deutéronome", "pt": "Deuteronômio"},
    "Giosuè": {"en": "Joshua", "es": "Josué", "de": "Josua", "fr": "Josué", "pt": "Josué"},
    "Giudici": {"en": "Judges", "es": "Jueces", "de": "Richter", "fr": "Juges", "pt": "Juízes"},
    "Rut": {"en": "Ruth", "es": "Rut", "de": "Ruth", "fr": "Ruth", "pt": "Rute"},
    "1 Samuele": {"en": "1 Samuel", "es": "1 Samuel", "de": "1 Samuel", "fr": "1 Samuel", "pt": "1 Samuel"},
    "2 Samuele": {"en": "2 Samuel", "es": "2 Samuel", "de": "2 Samuel", "fr": "2 Samuel", "pt": "2 Samuel"},
    "1 Re": {"en": "1 Kings", "es": "1 Reyes", "de": "1 Könige", "fr": "1 Rois", "pt": "1 Reis"},
    "2 Re": {"en": "2 Kings", "es": "2 Reyes", "de": "2 Könige", "fr": "2 Rois", "pt": "2 Reis"},
    "1 Cronache": {"en": "1 Chronicles", "es": "1 Crónicas", "de": "1 Chronik", "fr": "1 Chroniques", "pt": "1 Crônicas"},
    "2 Cronache": {"en": "2 Chronicles", "es": "2 Crónicas", "de": "2 Chronik", "fr": "2 Chroniques", "pt": "2 Crônicas"},
    "Esdra": {"en": "Ezra", "es": "Esdras", "de": "Esra", "fr": "Esdras", "pt": "Esdras"},
    "Neemia": {"en": "Nehemiah", "es": "Nehemías", "de": "Nehemia", "fr": "Néhémie", "pt": "Neemias"},
    "Ester": {"en": "Esther", "es": "Ester", "de": "Esther", "fr": "Esther", "pt": "Ester"},
    "Giobbe": {"en": "Job", "es": "Job", "de": "Hiob", "fr": "Job", "pt": "Jó"},
    "Salmi": {"en": "Psalms", "es": "Salmos", "de": "Psalmen", "fr": "Psaumes", "pt": "Salmos"},
    "Proverbi": {"en": "Proverbs", "es": "Proverbios", "de": "Sprüche", "fr": "Proverbes", "pt": "Provérbios"},
    "Ecclesiaste": {"en": "Ecclesiastes", "es": "Eclesiastés", "de": "Prediger", "fr": "Ecclésiaste", "pt": "Eclesiastes"},
    "Cantico dei Cantici": {"en": "Song of Solomon", "es": "Cantares", "de": "Hohelied", "fr": "Cantique", "pt": "Cânticos"},
    "Isaia": {"en": "Isaiah", "es": "Isaías", "de": "Jesaja", "fr": "Ésaïe", "pt": "Isaías"},
    "Geremia": {"en": "Jeremiah", "es": "Jeremías", "de": "Jeremia", "fr": "Jérémie", "pt": "Jeremias"},
    "Lamentazioni": {"en": "Lamentations", "es": "Lamentaciones", "de": "Klagelieder", "fr": "Lamentations", "pt": "Lamentações"},
    "Ezechiele": {"en": "Ezekiel", "es": "Ezequiel", "de": "Hesekiel", "fr": "Ézéchiel", "pt": "Ezequiel"},
    "Daniele": {"en": "Daniel", "es": "Daniel", "de": "Daniel", "fr": "Daniel", "pt": "Daniel"},
    "Osea": {"en": "Hosea", "es": "Oseas", "de": "Hosea", "fr": "Osée", "pt": "Oséias"},
    "Gioele": {"en": "Joel", "es": "Joel", "de": "Joel", "fr": "Joël", "pt": "Joel"},
    "Amos": {"en": "Amos", "es": "Amós", "de": "Amos", "fr": "Amos", "pt": "Amós"},
    "Abdia": {"en": "Obadiah", "es": "Abdías", "de": "Obadja", "fr": "Abdias", "pt": "Obadias"},
    "Giona": {"en": "Jonah", "es": "Jonás", "de": "Jona", "fr": "Jonas", "pt": "Jonas"},
    "Michea": {"en": "Micah", "es": "Miqueas", "de": "Micha", "fr": "Michée", "pt": "Miquéias"},
    "Naum": {"en": "Nahum", "es": "Nahúm", "de": "Nahum", "fr": "Nahum", "pt": "Naum"},
    "Abacuc": {"en": "Habakkuk", "es": "Habacuc", "de": "Habakuk", "fr": "Habacuc", "pt": "Habacuque"},
    "Sofonia": {"en": "Zephaniah", "es": "Sofonías", "de": "Zefanja", "fr": "Sophonie", "pt": "Sofonias"},
    "Aggeo": {"en": "Haggai", "es": "Hageo", "de": "Haggai", "fr": "Aggée", "pt": "Ageu"},
    "Zaccaria": {"en": "Zechariah", "es": "Zacarías", "de": "Sacharja", "fr": "Zacharie", "pt": "Zacarias"},
    "Malachia": {"en": "Malachi", "es": "Malaquías", "de": "Maleachi", "fr": "Malachie", "pt": "Malaquias"},
    "Matteo": {"en": "Matthew", "es": "Mateo", "de": "Matthäus", "fr": "Matthieu", "pt": "Mateus"},
    "Marco": {"en": "Mark", "es": "Marcos", "de": "Markus", "fr": "Marc", "pt": "Marcos"},
    "Luca": {"en": "Luke", "es": "Lucas", "de": "Lukas", "fr": "Luc", "pt": "Lucas"},
    "Giovanni": {"en": "John", "es": "Juan", "de": "Johannes", "fr": "Jean", "pt": "João"},
    "Atti": {"en": "Acts", "es": "Hechos", "de": "Apostelgeschichte", "fr": "Actes", "pt": "Atos"},
    "Romani": {"en": "Romans", "es": "Romanos", "de": "Römer", "fr": "Romains", "pt": "Romanos"},
    "1 Corinzi": {"en": "1 Corinthians", "es": "1 Corintios", "de": "1 Korinther", "fr": "1 Corinthiens", "pt": "1 Coríntios"},
    "2 Corinzi": {"en": "2 Corinthians", "es": "2 Corintios", "de": "2 Korinther", "fr": "2 Corinthiens", "pt": "2 Coríntios"},
    "Galati": {"en": "Galatians", "es": "Gálatas", "de": "Galater", "fr": "Galates", "pt": "Gálatas"},
    "Efesini": {"en": "Ephesians", "es": "Efesios", "de": "Epheser", "fr": "Éphésiens", "pt": "Efésios"},
    "Filippesi": {"en": "Philippians", "es": "Filipenses", "de": "Philipper", "fr": "Philippiens", "pt": "Filipenses"},
    "Colossesi": {"en": "Colossians", "es": "Colosenses", "de": "Kolosser", "fr": "Colossiens", "pt": "Colossenses"},
    "1 Tessalonicesi": {"en": "1 Thessalonians", "es": "1 Tesalonicenses", "de": "1 Thessalonicher", "fr": "1 Thessaloniciens", "pt": "1 Tessalonicenses"},
    "2 Tessalonicesi": {"en": "2 Thessalonians", "es": "2 Tesalonicenses", "de": "2 Thessalonicher", "fr": "2 Thessaloniciens", "pt": "2 Tessalonicenses"},
    "1 Timoteo": {"en": "1 Timothy", "es": "1 Timoteo", "de": "1 Timotheus", "fr": "1 Timothée", "pt": "1 Timóteo"},
    "2 Timoteo": {"en": "2 Timothy", "es": "2 Timoteo", "de": "2 Timotheus", "fr": "2 Timothée", "pt": "2 Timóteo"},
    "Tito": {"en": "Titus", "es": "Tito", "de": "Titus", "fr": "Tite", "pt": "Tito"},
    "Filemone": {"en": "Philemon", "es": "Filemón", "de": "Philemon", "fr": "Philémon", "pt": "Filemom"},
    "Ebrei": {"en": "Hebrews", "es": "Hebreos", "de": "Hebräer", "fr": "Hébreux", "pt": "Hebreus"},
    "Giacomo": {"en": "James", "es": "Santiago", "de": "Jakobus", "fr": "Jacques", "pt": "Tiago"},
    "1 Pietro": {"en": "1 Peter", "es": "1 Pedro", "de": "1 Petrus", "fr": "1 Pierre", "pt": "1 Pedro"},
    "2 Pietro": {"en": "2 Peter", "es": "2 Pedro", "de": "2 Petrus", "fr": "2 Pierre", "pt": "2 Pedro"},
    "1 Giovanni": {"en": "1 John", "es": "1 Juan", "de": "1 Johannes", "fr": "1 Jean", "pt": "1 João"},
    "2 Giovanni": {"en": "2 John", "es": "2 Juan", "de": "2 Johannes", "fr": "2 Jean", "pt": "2 João"},
    "3 Giovanni": {"en": "3 John", "es": "3 Juan", "de": "3 Johannes", "fr": "3 Jean", "pt": "3 João"},
    "Giuda": {"en": "Jude", "es": "Judas", "de": "Judas", "fr": "Jude", "pt": "Judas"},
    "Apocalisse": {"en": "Revelation", "es": "Apocalipsis", "de": "Offenbarung", "fr": "Apocalypse", "pt": "Apocalipse"},
}

def get_book_name_for_lang(italian_name: str, lang: str) -> str:
    """Get book name in target language from Italian name"""
    if lang == "it":
        return italian_name
    mapping = BOOK_NAME_MAPPING.get(italian_name, {})
    return mapping.get(lang, italian_name)

async def fetch_from_bible_api(book: str, chapter: int, lang: str = "en") -> list:
    """Fetch Bible chapter from bible-api.com (supports English and other languages)"""
    try:
        # Map Italian book name to English for API
        book_en = get_book_name_for_lang(book, "en")
        
        # bible-api.com translations
        translations = {
            "en": "kjv",  # King James Version
            "es": "rvr1960",  # Reina Valera would need different API
            "de": "luther",  # Luther Bible would need different API
            "fr": "lsg",  # Louis Segond would need different API
            "pt": "almeida"  # Almeida would need different API
        }
        
        # For now, use WEB (World English Bible) which is freely available
        translation = "web" if lang == "en" else "kjv"
        
        url = f"https://bible-api.com/{book_en}+{chapter}?translation={translation}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                logger.error(f"bible-api.com returned status {response.status_code}")
                return []
            
            data = response.json()
            verses = []
            
            for v in data.get("verses", []):
                verse_text = v.get("text", "").strip()
                verse_text = verse_text.replace("\n", " ").strip()
                if verse_text:
                    verses.append({
                        "verse": v.get("verse", 0),
                        "text": verse_text
                    })
            
            logger.info(f"Fetched {len(verses)} verses from bible-api.com for {book} {chapter} ({lang})")
            return verses
            
    except Exception as e:
        logger.error(f"Error fetching from bible-api.com: {e}")
        return []

def get_book_index_from_any_lang(book_name: str) -> int:
    """Find a book's index by searching all language book lists"""
    for lang_books in BIBLE_BOOKS_MULTILANG.values():
        for idx, b in enumerate(lang_books):
            if b["name"] == book_name:
                return idx
    return -1

def get_italian_book_name(book_name: str) -> str:
    """Convert any language book name to its Italian equivalent"""
    # If it's already an Italian name, return as-is
    it_books = BIBLE_BOOKS_MULTILANG["it"]
    for b in it_books:
        if b["name"] == book_name:
            return book_name
    # Find the book index from any language and return Italian name at that index
    idx = get_book_index_from_any_lang(book_name)
    if 0 <= idx < len(it_books):
        return it_books[idx]["name"]
    return book_name

# Map Italian book names to GitHub Bible abbreviations
BOOK_ABBREVS_IT = {
    "Genesi": "gn", "Esodo": "ex", "Levitico": "lv", "Numeri": "nm", "Deuteronomio": "dt",
    "Giosuè": "js", "Giudici": "jud", "Rut": "rt", "1 Samuele": "1sm", "2 Samuele": "2sm",
    "1 Re": "1kgs", "2 Re": "2kgs", "1 Cronache": "1ch", "2 Cronache": "2ch",
    "Esdra": "ezr", "Neemia": "ne", "Ester": "et", "Giobbe": "job", "Salmi": "ps",
    "Proverbi": "prv", "Ecclesiaste": "ec", "Cantico dei Cantici": "so", "Isaia": "is",
    "Geremia": "jr", "Lamentazioni": "lm", "Ezechiele": "ez", "Daniele": "dn",
    "Osea": "ho", "Gioele": "jl", "Amos": "am", "Abdia": "ob", "Giona": "jn",
    "Michea": "mi", "Naum": "na", "Abacuc": "hk", "Sofonia": "zp", "Aggeo": "hg",
    "Zaccaria": "zc", "Malachia": "ml", "Matteo": "mt", "Marco": "mk", "Luca": "lk",
    "Giovanni": "jo", "Atti": "act", "Romani": "rm", "1 Corinzi": "1co", "2 Corinzi": "2co",
    "Galati": "gl", "Efesini": "eph", "Filippesi": "ph", "Colossesi": "cl",
    "1 Tessalonicesi": "1ts", "2 Tessalonicesi": "2ts", "1 Timoteo": "1tm", "2 Timoteo": "2tm",
    "Tito": "tt", "Filemone": "phm", "Ebrei": "hb", "Giacomo": "jm", "1 Pietro": "1pe",
    "2 Pietro": "2pe", "1 Giovanni": "1jo", "2 Giovanni": "2jo", "3 Giovanni": "3jo",
    "Giuda": "jd", "Apocalisse": "re"
}

async def fetch_bible_chapter_any_lang(book: str, chapter: int, lang: str) -> list:
    """Fetch Bible chapter in any language using multiple free APIs"""
    
    # Try laparola.net for Italian first (best for Nuova Diodati)
    if lang == "it":
        verses = await fetch_from_laparola(book, chapter)
        if verses and len(verses) > 3:
            return verses
    
    # GitHub Bible JSON files - most reliable source
    github_files = {
        "es": "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/es_rvr.json",
        "en": "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json", 
        "de": "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/de_schlachter.json",
        "fr": "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/fr_apee.json",
        "pt": "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_acf.json",
    }
    
    if lang in github_files:
        try:
            # Convert any language book name to Italian, then get GitHub abbreviation
            it_name = get_italian_book_name(book)
            book_abbrev = BOOK_ABBREVS_IT.get(it_name, book.lower()[:2])
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(github_files[lang])
                
                if response.status_code == 200:
                    content = response.text
                    if content.startswith('\ufeff'):
                        content = content[1:]
                    
                    bible_data = json.loads(content)
                    
                    for b in bible_data:
                        if b.get("abbrev") == book_abbrev:
                            chapters = b.get("chapters", [])
                            if chapter <= len(chapters):
                                chapter_verses = chapters[chapter - 1]
                                verses = []
                                for i, text in enumerate(chapter_verses):
                                    if text:
                                        verses.append({"verse": i + 1, "text": text.strip()})
                                
                                if verses:
                                    logger.info(f"Fetched {len(verses)} verses from GitHub for {book} {chapter} ({lang})")
                                    return verses
                            break
        except Exception as e:
            logger.error(f"Error fetching from GitHub: {e}")
    
    # Fallback to bible-api.com (English)
    try:
        it_name = get_italian_book_name(book)
        book_en = get_book_name_for_lang(it_name, "en")
        url = f"https://bible-api.com/{book_en}+{chapter}?translation=web"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                verses = []
                
                for v in data.get("verses", []):
                    verse_text = v.get("text", "").strip()
                    verse_text = verse_text.replace("\n", " ").strip()
                    if verse_text:
                        verses.append({
                            "verse": v.get("verse", 0),
                            "text": verse_text
                        })
                
                if verses:
                    logger.info(f"Fetched {len(verses)} verses from bible-api.com for {book} {chapter}")
                    return verses
    except Exception as e:
        logger.error(f"Error fetching from bible-api.com: {e}")
    
    return []

@api_router.get("/bible/chapter/{book}/{chapter}")
async def get_chapter(book: str, chapter: int, lang: str = "it"):
    """Get verses for a chapter in specified language"""
    key = f"{book}:{chapter}"
    
    # First try the real Bible data (Nuova Diodati or Reina Valera)
    if lang == "it":
        verses = NUOVA_DIODATI.get(key, [])
    elif lang == "es":
        verses = REINA_VALERA_1960.get(key, [])
    else:
        verses = []
    
    if verses:
        return {"book": book, "chapter": chapter, "verses": verses, "language": lang}
    
    # Check if we have it cached in MongoDB
    cached = await db.bible_cache.find_one({"book": book, "chapter": chapter, "language": lang})
    if cached and cached.get("verses") and len(cached.get("verses", [])) > 3:
        return {"book": book, "chapter": chapter, "verses": cached["verses"], "language": lang}
    
    # Fetch from external APIs
    fetched_verses = await fetch_bible_chapter_any_lang(book, chapter, lang)
    
    if fetched_verses and len(fetched_verses) > 3:
        # Cache in MongoDB for future use
        await db.bible_cache.update_one(
            {"book": book, "chapter": chapter, "language": lang},
            {"$set": {"verses": fetched_verses, "source": "external_api", "cached_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        return {"book": book, "chapter": chapter, "verses": fetched_verses, "language": lang}
    
    # Return placeholder if nothing found
    verses = []
    placeholders = {
        "it": "Questo capitolo sarà presto disponibile.",
        "es": "Este capítulo estará disponible pronto.",
        "en": "This chapter will be available soon.",
        "de": "Dieses Kapitel wird bald verfügbar sein.",
        "fr": "Ce chapitre sera bientôt disponible.",
        "pt": "Este capítulo estará disponível em breve."
    }
    placeholder_text = placeholders.get(lang, placeholders["en"])
    
    for i in range(1, 10):
        verses.append({"verse": i, "text": placeholder_text})
    
    return {"book": book, "chapter": chapter, "verses": verses, "language": lang}

# ==================== BIBLE STUDY TOOLS ====================

# Cross-references - Versetti correlati
CROSS_REFERENCES = {
    "Genesi:1:1": [
        {"ref": "Giovanni 1:1-3", "text": "Nel principio era la Parola..."},
        {"ref": "Colossesi 1:16", "text": "Poiché in lui sono state create tutte le cose"},
        {"ref": "Ebrei 11:3", "text": "Per fede comprendiamo che l'universo è stato formato dalla parola di Dio"},
        {"ref": "Salmi 33:6", "text": "I cieli furono fatti dalla parola dell'Eterno"},
    ],
    "Genesi:1:26": [
        {"ref": "Genesi 5:1", "text": "Nel giorno che Dio creò l'uomo, lo fece a somiglianza di Dio"},
        {"ref": "1 Corinzi 11:7", "text": "L'uomo è immagine e gloria di Dio"},
        {"ref": "Colossesi 3:10", "text": "Rivestiti del nuovo uomo che si va rinnovando"},
    ],
    "Salmi:23:1": [
        {"ref": "Giovanni 10:11", "text": "Io sono il buon pastore; il buon pastore dà la sua vita per le pecore"},
        {"ref": "Ezechiele 34:11-12", "text": "Io stesso cercherò le mie pecore"},
        {"ref": "Isaia 40:11", "text": "Come un pastore, egli pascerà il suo gregge"},
    ],
    "Giovanni:3:16": [
        {"ref": "Romani 5:8", "text": "Ma Dio dimostra il suo amore verso di noi"},
        {"ref": "1 Giovanni 4:9-10", "text": "In questo si è manifestato l'amore di Dio"},
        {"ref": "Giovanni 1:14", "text": "E la Parola si è fatta carne"},
    ],
    "Giovanni:14:6": [
        {"ref": "Atti 4:12", "text": "Non c'è salvezza in nessun altro"},
        {"ref": "1 Timoteo 2:5", "text": "C'è un solo mediatore fra Dio e gli uomini"},
        {"ref": "Ebrei 10:19-20", "text": "Una via nuova e vivente"},
    ],
    "Romani:8:28": [
        {"ref": "Geremia 29:11", "text": "Io so i pensieri che ho per voi"},
        {"ref": "Efesini 1:11", "text": "Secondo il proponimento di colui che opera tutte le cose"},
        {"ref": "Genesi 50:20", "text": "Voi avete pensato del male contro di me; ma Dio ha pensato di farlo servire al bene"},
    ],
    "Filippesi:4:13": [
        {"ref": "2 Corinzi 12:9", "text": "La mia grazia ti basta"},
        {"ref": "Giovanni 15:5", "text": "Senza di me non potete far nulla"},
        {"ref": "Isaia 40:31", "text": "Quelli che sperano nell'Eterno acquistano nuove forze"},
    ],
}

# Termini chiave collegati al dizionario
VERSE_DICTIONARY_LINKS = {
    "Genesi:1:1": ["elohim"],
    "Genesi:1:2": ["ruach"],
    "Genesi:2:7": ["ruach"],
    "Salmi:23:1": ["yhwh", "shalom"],
    "Giovanni:1:1": ["logos"],
    "Giovanni:3:16": ["agape"],
    "Romani:8:28": ["agape"],
    "1 Corinzi:13:4": ["agape"],
    "Salmi:136:1": ["chesed"],
    "Numeri:6:26": ["shalom"],
}

# Studio contestuale - Contesto storico e note
STUDY_CONTEXT = {
    "Genesi:1": {
        "historical_context": "Il racconto della creazione in Genesi presenta una visione teologica dell'origine dell'universo, distinta dai miti cosmogonici delle culture circostanti (Babilonese, Egiziana). Scritto probabilmente durante o dopo l'esilio babilonese.",
        "literary_structure": "Struttura settenaria con formula ripetitiva: 'Dio disse... e fu così... Dio vide che era buono'. I sei giorni mostrano un parallelismo: giorni 1-3 (separazione), giorni 4-6 (riempimento).",
        "key_themes": ["Sovranità di Dio", "Bontà della creazione", "Dignità dell'uomo", "Riposo sabbatico"],
        "application": "La creazione testimonia la potenza e la sapienza di Dio. L'uomo, creato a immagine di Dio, ha responsabilità di cura verso il creato."
    },
    "Salmi:23": {
        "historical_context": "Salmo attribuito a Davide, probabilmente composto riflettendo sulla sua esperienza come pastore di pecore a Betlemme prima di diventare re. Uno dei salmi più amati nella storia della Chiesa.",
        "literary_structure": "Due metafore principali: il pastore (vv. 1-4) e l'ospite (vv. 5-6). Cambio dal 'lui' al 'tu' indica intimità crescente con Dio.",
        "key_themes": ["Provvidenza divina", "Guida spirituale", "Protezione nella prova", "Comunione con Dio"],
        "application": "Il Signore provvede a tutti i nostri bisogni. Anche nelle difficoltà ('valle dell'ombra'), possiamo confidare nella Sua presenza."
    },
    "Giovanni:3": {
        "historical_context": "Dialogo notturno tra Gesù e Nicodemo, un fariseo membro del Sinedrio. Ambientato probabilmente a Gerusalemme durante la Pasqua (Giovanni 2:23).",
        "literary_structure": "Dialogo che procede per incomprensioni: Nicodemo interpreta letteralmente, Gesù parla spiritualmente. Culmina nella dichiarazione teologica di 3:16.",
        "key_themes": ["Nuova nascita", "Fede in Cristo", "Amore di Dio", "Vita eterna vs condanna"],
        "application": "La salvezza richiede una trasformazione radicale (nuova nascita) operata dallo Spirito Santo. Giovanni 3:16 riassume l'intero vangelo."
    },
    "Romani:8": {
        "historical_context": "Lettera scritta da Paolo da Corinto (ca. 57 d.C.) alla chiesa di Roma che non aveva fondato. Capitolo 8 rappresenta il culmine della sezione dottrinale.",
        "literary_structure": "Struttura: vita nello Spirito (1-17), sofferenza presente vs gloria futura (18-30), inno di trionfo (31-39).",
        "key_themes": ["Nessuna condanna", "Vita nello Spirito", "Adozione filiale", "Perseveranza dei santi", "Amore inseparabile di Dio"],
        "application": "Chi è in Cristo non è più sotto condanna. Lo Spirito ci guida, intercede per noi, e nulla può separarci dall'amore di Dio."
    },
}

class StudyNoteCreate(BaseModel):
    book: str
    chapter: int
    verse: Optional[int] = None
    note: str
    highlight_color: Optional[str] = None
    tags: List[str] = []

@api_router.get("/bible/study/{book}/{chapter}")
async def get_study_data(book: str, chapter: int, verse: Optional[int] = None, user: User = Depends(require_auth)):
    """Get study tools for a chapter/verse"""
    chapter_key = f"{book}:{chapter}"
    
    # Get cross-references
    cross_refs = {}
    for key, refs in CROSS_REFERENCES.items():
        if key.startswith(chapter_key):
            cross_refs[key] = refs
    
    # Get dictionary links
    dict_links = {}
    for key, terms in VERSE_DICTIONARY_LINKS.items():
        if key.startswith(chapter_key):
            dict_links[key] = terms
    
    # Get study context
    context = STUDY_CONTEXT.get(chapter_key, None)
    
    # Get user's personal notes
    user_notes = await db.study_notes.find(
        {"user_id": user.user_id, "book": book, "chapter": chapter},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "book": book,
        "chapter": chapter,
        "cross_references": cross_refs,
        "dictionary_links": dict_links,
        "study_context": context,
        "user_notes": user_notes
    }

@api_router.post("/bible/study/notes")
async def create_study_note(data: StudyNoteCreate, user: User = Depends(require_auth)):
    """Create a personal study note"""
    note = {
        "note_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "book": data.book,
        "chapter": data.chapter,
        "verse": data.verse,
        "note": data.note,
        "highlight_color": data.highlight_color,
        "tags": data.tags,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.study_notes.insert_one(note)
    note.pop("_id", None)
    return note

@api_router.get("/bible/study/notes")
async def get_all_study_notes(user: User = Depends(require_auth)):
    """Get all user's study notes"""
    notes = await db.study_notes.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return notes

@api_router.delete("/bible/study/notes/{note_id}")
async def delete_study_note(note_id: str, user: User = Depends(require_auth)):
    """Delete a study note"""
    result = await db.study_notes.delete_one({"note_id": note_id, "user_id": user.user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nota non trovata")
    return {"success": True}

@api_router.post("/bible/study/ai-explain")
async def ai_explain_verse(request: Request, user: User = Depends(require_auth)):
    """AI explanation of a verse"""
    body = await request.json()
    verse_ref = body.get("verse_ref", "")
    verse_text = body.get("verse_text", "")
    question = body.get("question")
    language = body.get("language", "it")
    
    # System prompts for each language
    system_prompts = {
        "it": """Sei un teologo e biblista cristiano evangelico esperto. Spiega i versetti biblici in modo:
- Fedele al testo originale (ebraico/greco quando rilevante)
- Contestualizzato storicamente e culturalmente
- Applicabile alla vita quotidiana
- Con riferimenti ad altri versetti correlati
Rispondi in ITALIANO in modo chiaro e accessibile.""",
        "es": """Eres un teólogo y biblista cristiano evangélico experto. Explica los versículos bíblicos de manera:
- Fiel al texto original (hebreo/griego cuando sea relevante)
- Contextualizado histórica y culturalmente
- Aplicable a la vida cotidiana
- Con referencias a otros versículos relacionados
Responde en ESPAÑOL de manera clara y accesible.""",
        "en": """You are an expert evangelical Christian theologian and biblical scholar. Explain Bible verses:
- Faithful to the original text (Hebrew/Greek when relevant)
- Historically and culturally contextualized
- Applicable to daily life
- With references to other related verses
Answer in ENGLISH clearly and accessibly.""",
        "de": """Du bist ein erfahrener evangelikaler christlicher Theologe und Bibelwissenschaftler. Erkläre Bibelverse:
- Treu zum Originaltext (Hebräisch/Griechisch wenn relevant)
- Historisch und kulturell kontextualisiert
- Anwendbar auf das tägliche Leben
- Mit Verweisen auf andere verwandte Verse
Antworte auf DEUTSCH klar und verständlich.""",
        "fr": """Tu es un théologien et bibliste chrétien évangélique expert. Explique les versets bibliques de manière:
- Fidèle au texte original (hébreu/grec si pertinent)
- Contextualisé historiquement et culturellement
- Applicable à la vie quotidienne
- Avec des références à d'autres versets connexes
Réponds en FRANÇAIS de manière claire et accessible.""",
        "pt": """Você é um teólogo e estudioso bíblico cristão evangélico experiente. Explique os versículos bíblicos:
- Fiel ao texto original (hebraico/grego quando relevante)
- Contextualizado histórica e culturalmente
- Aplicável à vida cotidiana
- Com referências a outros versículos relacionados
Responda em PORTUGUÊS de forma clara e acessível."""
    }
    
    # Default questions for each language
    default_questions = {
        "it": "Spiega questo versetto",
        "es": "Explica este versículo",
        "en": "Explain this verse",
        "de": "Erkläre diesen Vers",
        "fr": "Explique ce verset",
        "pt": "Explique este versículo"
    }
    
    if not question:
        question = default_questions.get(language, default_questions["it"])
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"study_{user.user_id}_{uuid.uuid4().hex[:8]}",
            system_message=system_prompts.get(language, system_prompts["it"])
        ).with_model("openai", "gpt-4o")
        
        prompt = f"Versetto: {verse_ref}\nTesto: {verse_text}\n\nDomanda: {question}"
        response = await chat.send_message(UserMessage(text=prompt))
        
        return {"explanation": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore AI: {str(e)}")

@api_router.get("/bible/daily-verse")
async def get_daily_verse(lang: str = "it"):
    """Get daily verse in specified language"""
    import random
    verses_dict = SAMPLE_VERSES_MULTILANG.get(lang, SAMPLE_VERSES_MULTILANG["it"])
    
    all_verses = []
    for ref, verses in verses_dict.items():
        book, chap = ref.split(":")
        for v in verses:
            all_verses.append({
                "reference": f"{book} {chap}:{v['verse']}",
                "text": v["text"]
            })
    
    if not all_verses:
        # Fallback to Italian
        for ref, verses in SAMPLE_VERSES_MULTILANG["it"].items():
            book, chap = ref.split(":")
            for v in verses:
                all_verses.append({
                    "reference": f"{book} {chap}:{v['verse']}",
                    "text": v["text"]
                })
    
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    random.seed(int(today))
    verse = random.choice(all_verses)
    verse["language"] = lang
    return verse

@api_router.post("/bible/translate-verse")
async def translate_verse(request: Request, user: User = Depends(require_auth)):
    """Translate a Bible verse to another language"""
    body = await request.json()
    text = body.get("text", "")
    source_lang = body.get("source_lang", "it")
    target_lang = body.get("target_lang", "en")
    
    translated = await translate_text(text, source_lang, target_lang)
    return {
        "original": text,
        "translated": translated,
        "source_lang": source_lang,
        "target_lang": target_lang
    }

# ==================== AI ENDPOINTS ====================

@api_router.post("/ai/chat")
async def ai_chat(data: ChatRequest, user: User = Depends(require_auth)):
    """Chat with AI spiritual assistant in user's language"""
    try:
        session_id = f"chat_{user.user_id}"
        lang = data.language or user.language or "it"
        lang_name = SUPPORTED_LANGUAGES.get(lang, {}).get("name", "Italiano")
        
        system_messages = {
            "it": f"Sei un assistente spirituale cristiano. Rispondi in italiano con compassione e saggezza biblica.",
            "es": f"Eres un asistente espiritual cristiano. Responde en español con compasión y sabiduría bíblica.",
            "en": f"You are a Christian spiritual assistant. Respond in English with compassion and biblical wisdom.",
            "pt": f"Você é um assistente espiritual cristão. Responda em português com compaixão e sabedoria bíblica.",
            "fr": f"Tu es un assistant spirituel chrétien. Réponds en français avec compassion et sagesse biblique.",
        }
        
        system_message = system_messages.get(lang, system_messages["it"])
        if data.mood:
            system_message += f"\n\nL'utente si sente: {data.mood}."
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=data.message))
        
        await db.chat_history.insert_one({
            "message_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "role": "user",
            "content": data.message,
            "language": lang,
            "created_at": datetime.now(timezone.utc)
        })
        
        await db.chat_history.insert_one({
            "message_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "role": "assistant",
            "content": response,
            "language": lang,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {"response": response, "language": lang}
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore AI: {str(e)}")

@api_router.get("/ai/chat-history")
async def get_chat_history(user: User = Depends(require_auth), limit: int = 50):
    messages = await db.chat_history.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return list(reversed(messages))

@api_router.delete("/ai/chat-history")
async def clear_chat_history(user: User = Depends(require_auth)):
    await db.chat_history.delete_many({"user_id": user.user_id})
    return {"message": "Cronologia cancellata"}

@api_router.post("/ai/mood-checkin")
async def mood_checkin(data: MoodRequest, user: User = Depends(require_auth)):
    """Get AI-generated reflection based on mood in user's language"""
    try:
        import random
        lang = data.language or user.language or "it"
        
        mood_verses = MOOD_VERSES_MULTILANG.get(lang, MOOD_VERSES_MULTILANG["it"])
        mood = data.mood.lower()
        mood_data = mood_verses.get(mood, mood_verses.get("speranzoso", [{"ref": "Salmi 23:1", "text": "Il Signore è il mio pastore."}]))
        verse = random.choice(mood_data) if mood_data else {"ref": "Salmi 23:1", "text": "Il Signore è il mio pastore."}
        
        # Generate reflection in user's language
        lang_prompts = {
            "it": f"L'utente si sente {mood}. Il versetto è: {verse['ref']} - \"{verse['text']}\". Genera una breve riflessione spirituale in italiano.",
            "es": f"El usuario se siente {mood}. El versículo es: {verse['ref']} - \"{verse['text']}\". Genera una breve reflexión espiritual en español.",
            "en": f"The user feels {mood}. The verse is: {verse['ref']} - \"{verse['text']}\". Generate a brief spiritual reflection in English.",
            "pt": f"O usuário está se sentindo {mood}. O versículo é: {verse['ref']} - \"{verse['text']}\". Gere uma breve reflexão espiritual em português.",
            "fr": f"L'utilisateur se sent {mood}. Le verset est: {verse['ref']} - \"{verse['text']}\". Génère une brève réflexion spirituelle en français.",
        }
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mood_{user.user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message="You are a spiritual counselor. Generate brief, encouraging reflections."
        ).with_model("openai", "gpt-4o")
        
        prompt = lang_prompts.get(lang, lang_prompts["it"])
        response = await chat.send_message(UserMessage(text=prompt))
        
        checkin = {
            "checkin_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "mood": mood,
            "verse_reference": verse["ref"],
            "verse_text": verse["text"],
            "reflection": response,
            "language": lang,
            "created_at": datetime.now(timezone.utc)
        }
        await db.mood_checkins.insert_one(checkin)
        
        return {
            "mood": mood,
            "verse": verse,
            "reflection": response,
            "language": lang
        }
    except Exception as e:
        logger.error(f"Mood checkin error: {e}")
        import random
        mood_data = MOOD_VERSES_MULTILANG.get("it", {}).get(data.mood.lower(), [{"ref": "Salmi 23:1", "text": "Il Signore è il mio pastore."}])
        verse = random.choice(mood_data) if mood_data else {"ref": "Salmi 23:1", "text": "Il Signore è il mio pastore."}
        return {
            "mood": data.mood,
            "verse": verse,
            "reflection": "Che Dio ti benedica e ti dia pace oggi."
        }

# ==================== COMMUNITY ENDPOINTS ====================

# Bad words filter for moderation
BAD_WORDS = {
    "it": ["cazzo", "minchia", "stronzo", "merda", "vaffanculo", "puttana", "coglione", "idiota", "deficiente"],
    "es": ["mierda", "puta", "joder", "coño", "cabrón", "pendejo", "idiota"],
    "en": ["fuck", "shit", "ass", "bitch", "damn", "bastard", "idiot"],
    "generic": ["nazi", "hitler", "satan", "666"]
}

def check_content_moderation(content: str, lang: str = "it") -> tuple:
    """Check content for offensive words. Returns (is_clean, filtered_content, warnings)"""
    content_lower = content.lower()
    warnings = []
    
    # Check all language bad words
    for lang_code, words in BAD_WORDS.items():
        for word in words:
            if word in content_lower:
                warnings.append(f"Parola non appropriata rilevata")
                # Replace with asterisks
                content = re.sub(re.escape(word), '*' * len(word), content, flags=re.IGNORECASE)
    
    is_clean = len(warnings) == 0
    return is_clean, content, warnings

@api_router.post("/community/messages")
async def create_community_message(data: CommunityMessageCreate, user: User = Depends(require_auth)):
    """Create a community message with content moderation"""
    # Content moderation
    is_clean, filtered_content, warnings = check_content_moderation(data.content, data.language)
    
    if warnings:
        logger.warning(f"Content moderation triggered for user {user.user_id}: {warnings}")
    
    message = {
        "message_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "user_country": user.country,
        "content": filtered_content,  # Use filtered content
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
    
    # Check cache first
    if target_lang in message.get("translations", {}):
        return {"translated_text": message["translations"][target_lang], "is_original": False}
    
    # Translate and cache
    translated = await translate_text(message["content"], message["original_language"], target_lang)
    await db.community_messages.update_one(
        {"message_id": message_id},
        {"$set": {f"translations.{target_lang}": translated}}
    )
    
    return {"translated_text": translated, "is_original": False}

# ==================== ONLINE USERS TRACKING ====================

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
    
    # Translate messages to user's language if needed
    for msg in messages:
        if msg["original_language"] != lang:
            if lang not in msg.get("translations", {}):
                # Translate and cache
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
async def get_community_users(user: User = Depends(require_auth)):
    """Get public users from community"""
    users = await db.users.find(
        {"is_public": True},
        {"_id": 0, "password_hash": 0, "email": 0}
    ).limit(50).to_list(50)
    return users

# ==================== JOURNAL ENDPOINTS ====================

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

# ==================== BOOKMARK ENDPOINTS ====================

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

# ==================== PROGRESS ENDPOINTS ====================

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
        # Return copy without _id
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

# Save reading history for a specific chapter
@api_router.post("/progress/reading/chapter")
async def save_chapter_reading(
    book: str = Query(...),
    chapter: int = Query(...),
    user: User = Depends(require_auth)
):
    """Save a specific chapter as read and update reading history"""
    now = datetime.now(timezone.utc)
    
    # Update reading history collection
    existing = await db.reading_history.find_one({
        "user_id": user.user_id,
        "book": book,
        "chapter": chapter
    })
    
    if existing:
        # Update last read date
        await db.reading_history.update_one(
            {"_id": existing["_id"]},
            {"$set": {"last_read": now, "read_count": existing.get("read_count", 1) + 1}}
        )
    else:
        # Create new entry
        await db.reading_history.insert_one({
            "user_id": user.user_id,
            "book": book,
            "chapter": chapter,
            "first_read": now,
            "last_read": now,
            "read_count": 1
        })
    
    return {"success": True, "book": book, "chapter": chapter}

# Get reading history
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

# ==================== DONATION ENDPOINTS ====================

# Donation Configuration
DONATION_CONFIG = {
    "paypal_email": "andrehangar@live.it",
    "paypal_link": "https://www.paypal.com/paypalme/andrehangar",
    "iban": "IT46I0366160085802855893200",
    "intestatario": "Andrea Confortino",
    "banca": "Revolut",
}

@api_router.get("/donations/config")
async def get_donation_config():
    """Get donation configuration (PayPal, IBAN)"""
    return DONATION_CONFIG

@api_router.post("/donations")
async def create_donation(data: DonationRequest, user: User = Depends(require_auth)):
    donation = {
        "donation_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "amount": data.amount,
        "method": data.method,
        "message": data.message,
        "status": "pending" if data.method == "bonifico" else "completed",
        "created_at": datetime.now(timezone.utc)
    }
    
    if data.method == "bonifico":
        donation["bank_details"] = {
            "iban": DONATION_CONFIG["iban"],
            "intestatario": DONATION_CONFIG["intestatario"],
            "banca": DONATION_CONFIG["banca"],
            "causale": f"Donazione Amen! - {donation['donation_id'][:8]}"
        }
    elif data.method == "paypal":
        donation["paypal_email"] = DONATION_CONFIG["paypal_email"]
        donation["paypal_link"] = DONATION_CONFIG["paypal_link"]
    
    await db.donations.insert_one(donation)
    donation.pop("_id", None)
    return donation

@api_router.get("/donations")
async def get_donations(user: User = Depends(require_auth)):
    donations = await db.donations.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return donations

# ==================== RADIO ENDPOINTS ====================

EVANGELICAL_RADIOS = [
    # EUROPA - ITALIA (15 radio)
    {"name": "Radio Evangelo Roma", "url": "https://www.radioevangeloroma.it/", "stream_url": "https://stream.radioevangeloroma.it/stream", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Luce", "url": "https://www.radioluce.it/", "stream_url": "https://www.radioluce.it/player", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "RTB Network", "url": "https://www.rtbnetwork.it/", "stream_url": "https://stream.rtbnetwork.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio RCR", "url": "https://www.rcr.it/", "stream_url": "https://www.rcr.it/diretta", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Parole di Vita", "url": "https://www.paroledivita.org/", "stream_url": "https://www.paroledivita.org/radio", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Voce della Speranza", "url": "https://www.radiovocedellasperanza.it/", "stream_url": "https://www.radiovocedellasperanza.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Speranza Italia", "url": "https://radiosperanza.it/", "stream_url": "https://radiosperanza.it/streaming", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Cristiana Evangelica", "url": "https://radiocristianaevangelica.it/", "stream_url": "https://radiocristianaevangelica.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Grazia", "url": "https://www.radiograzia.it/", "stream_url": "https://www.radiograzia.it/live", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Buon Messaggio", "url": "https://www.radiobuonmessaggio.it/", "stream_url": "https://www.radiobuonmessaggio.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Pace Milano", "url": "https://www.radiopace.net/", "stream_url": "https://www.radiopace.net/ascolta", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Berea Italia", "url": "https://www.radioberea.it/", "stream_url": "https://www.radioberea.it/live", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Missione Francescana", "url": "https://www.radiomissionefrancescana.it/", "stream_url": "https://www.radiomissionefrancescana.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Punto Italia", "url": "https://radiopunto.it/", "stream_url": "https://radiopunto.it/streaming", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Studio Aperto", "url": "https://www.radiostudioaperto.it/", "stream_url": "https://www.radiostudioaperto.it/", "country": "Italia", "language": "it", "region": "Europa", "continent": "Europa"},
    
    # EUROPA - SPAGNA
    {"name": "Radio Unción", "url": "https://www.radiouncion.com/", "stream_url": "https://www.radiouncion.com/", "country": "España", "language": "es", "region": "Europa", "continent": "Europa"},
    {"name": "Onda Luz Radio", "url": "https://ondaluzradio.es/", "stream_url": "https://ondaluzradio.es/", "country": "España", "language": "es", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Oasis España", "url": "https://www.radiooasis.es/", "stream_url": "https://www.radiooasis.es/envivo", "country": "España", "language": "es", "region": "Europa", "continent": "Europa"},
    {"name": "Radio Vida España", "url": "https://www.radiovidaespana.com/", "stream_url": "https://www.radiovidaespana.com/", "country": "España", "language": "es", "region": "Europa", "continent": "Europa"},
    
    # EUROPA - FRANCIA
    {"name": "Radio Vie", "url": "https://www.radiovie.com/", "stream_url": "https://www.radiovie.com/ecouter", "country": "France", "language": "fr", "region": "Europa", "continent": "Europa"},
    {"name": "Phare FM", "url": "https://www.pharefm.com/", "stream_url": "https://www.pharefm.com/", "country": "France", "language": "fr", "region": "Europa", "continent": "Europa"},
    
    # EUROPA - UK
    {"name": "Premier Christian Radio", "url": "https://premierchristianradio.com/", "stream_url": "https://premierchristianradio.com/Listen", "country": "UK", "language": "en", "region": "Europa", "continent": "Europa"},
    {"name": "UCB Radio", "url": "https://www.ucb.co.uk/", "stream_url": "https://www.ucb.co.uk/listen", "country": "UK", "language": "en", "region": "Europa", "continent": "Europa"},
    
    # EUROPA - GERMANIA
    {"name": "ERF Radio", "url": "https://www.erf.de/", "stream_url": "https://www.erf.de/radio", "country": "Deutschland", "language": "de", "region": "Europa", "continent": "Europa"},
    
    # NORD AMERICA - USA
    {"name": "BBN Radio", "url": "https://bbnradio.org/", "stream_url": "https://bbnradio.org/listen-live", "country": "USA", "language": "en", "region": "USA", "continent": "NordAmerica"},
    {"name": "K-LOVE Radio", "url": "https://www.klove.com/", "stream_url": "https://www.klove.com/listen", "country": "USA", "language": "en", "region": "USA", "continent": "NordAmerica"},
    {"name": "Air1 Worship", "url": "https://www.air1.com/", "stream_url": "https://www.air1.com/listen", "country": "USA", "language": "en", "region": "USA", "continent": "NordAmerica"},
    {"name": "Moody Radio", "url": "https://www.moodyradio.org/", "stream_url": "https://www.moodyradio.org/listen", "country": "USA", "language": "en", "region": "USA", "continent": "NordAmerica"},
    {"name": "WAY-FM", "url": "https://www.wayfm.com/", "stream_url": "https://www.wayfm.com/", "country": "USA", "language": "en", "region": "USA", "continent": "NordAmerica"},
    
    # SUD AMERICA - ARGENTINA
    {"name": "Radio Nuevo Tiempo Argentina", "url": "https://nuevotiempo.org/radio/", "stream_url": "https://nuevotiempo.org/radio/", "country": "Argentina", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Cristiana Argentina", "url": "https://radiocristianaargentina.com/", "stream_url": "https://radiocristianaargentina.com/", "country": "Argentina", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Fe Buenos Aires", "url": "https://www.radiofe.com.ar/", "stream_url": "https://www.radiofe.com.ar/", "country": "Argentina", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Mitre Cristiana", "url": "https://radiomitre.cienradios.com/", "stream_url": "https://radiomitre.cienradios.com/", "country": "Argentina", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - PERÚ
    {"name": "Radio Bethel Peru", "url": "https://radiobethel.pe/", "stream_url": "https://radiobethel.pe/en-vivo", "country": "Perú", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Nuevo Tiempo Peru", "url": "https://nuevotiempo.org/peru/", "stream_url": "https://nuevotiempo.org/peru/radio", "country": "Perú", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Logos Peru", "url": "https://radiologos.pe/", "stream_url": "https://radiologos.pe/", "country": "Perú", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - COLOMBIA
    {"name": "Radio Paz Colombia", "url": "https://radiopaz.co/", "stream_url": "https://radiopaz.co/", "country": "Colombia", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "HJCB La Voz de los Andes", "url": "https://hcjb.org.ec/", "stream_url": "https://hcjb.org.ec/", "country": "Colombia", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Caracol Radio Cristiana", "url": "https://www.caracol.com.co/", "stream_url": "https://www.caracol.com.co/", "country": "Colombia", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - CHILE
    {"name": "Radio Corporación Chile", "url": "https://www.corporacion.cl/", "stream_url": "https://www.corporacion.cl/", "country": "Chile", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Nuevo Tiempo Chile", "url": "https://nuevotiempo.org/chile/", "stream_url": "https://nuevotiempo.org/chile/radio", "country": "Chile", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - ECUADOR
    {"name": "HCJB La Voz de los Andes Ecuador", "url": "https://hcjb.org.ec/", "stream_url": "https://hcjb.org.ec/escuchar", "country": "Ecuador", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - VENEZUELA
    {"name": "Radio Fe y Alegría Venezuela", "url": "https://www.radiofeyalegria.org/", "stream_url": "https://www.radiofeyalegria.org/", "country": "Venezuela", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Caracas Cristiana", "url": "https://www.radiocaracascristiana.com/", "stream_url": "https://www.radiocaracascristiana.com/", "country": "Venezuela", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # SUD AMERICA - MÉXICO
    {"name": "Radio Vida México", "url": "https://radiovidamexico.com/", "stream_url": "https://radiovidamexico.com/", "country": "México", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Nuevo Tiempo México", "url": "https://nuevotiempo.org/mexico/", "stream_url": "https://nuevotiempo.org/mexico/radio", "country": "México", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Impacto Monterrey", "url": "https://radioimpacto.mx/", "stream_url": "https://radioimpacto.mx/envivo", "country": "México", "language": "es", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # CARIBE - PUERTO RICO
    {"name": "Radio Paz Puerto Rico", "url": "https://radiopaz.com/", "stream_url": "https://radiopaz.com/en-vivo", "country": "Puerto Rico", "language": "es", "region": "Caribe", "continent": "Caribe"},
    {"name": "Radio Vida Puerto Rico", "url": "https://radiovidapr.com/", "stream_url": "https://radiovidapr.com/", "country": "Puerto Rico", "language": "es", "region": "Caribe", "continent": "Caribe"},
    {"name": "WIVV Radio", "url": "https://wivv.com/", "stream_url": "https://wivv.com/stream", "country": "Puerto Rico", "language": "es", "region": "Caribe", "continent": "Caribe"},
    
    # CARIBE - REPÚBLICA DOMINICANA
    {"name": "Radio Visión Cristiana RD", "url": "https://visioncristianard.com/", "stream_url": "https://visioncristianard.com/radio", "country": "Rep. Dominicana", "language": "es", "region": "Caribe", "continent": "Caribe"},
    {"name": "Radio Amanecer Dominicana", "url": "https://radioamanecer.com/", "stream_url": "https://radioamanecer.com/", "country": "Rep. Dominicana", "language": "es", "region": "Caribe", "continent": "Caribe"},
    {"name": "Radio Paz Dominicana", "url": "https://radiopazrd.com/", "stream_url": "https://radiopazrd.com/live", "country": "Rep. Dominicana", "language": "es", "region": "Caribe", "continent": "Caribe"},
    
    # CARIBE - CUBA
    {"name": "Radio Martí Cristiana", "url": "https://www.radiotelevisionmarti.com/", "stream_url": "https://www.radiotelevisionmarti.com/", "country": "Cuba", "language": "es", "region": "Caribe", "continent": "Caribe"},
    {"name": "Radio Esperanza Cuba", "url": "https://radioesperanzacuba.com/", "stream_url": "https://radioesperanzacuba.com/", "country": "Cuba", "language": "es", "region": "Caribe", "continent": "Caribe"},
    
    # CARIBE - JAMAICA
    {"name": "Love FM Jamaica", "url": "https://lovefm.com/", "stream_url": "https://lovefm.com/listen", "country": "Jamaica", "language": "en", "region": "Caribe", "continent": "Caribe"},
    {"name": "Gospel JA FM", "url": "https://gospeljafm.com/", "stream_url": "https://gospeljafm.com/", "country": "Jamaica", "language": "en", "region": "Caribe", "continent": "Caribe"},
    
    # CARIBE - HAITI
    {"name": "Radio Lumière Haiti", "url": "https://radiolumiere.org/", "stream_url": "https://radiolumiere.org/ecoute", "country": "Haiti", "language": "fr", "region": "Caribe", "continent": "Caribe"},
    {"name": "Radio 4VEH", "url": "https://4veh.org/", "stream_url": "https://4veh.org/live", "country": "Haiti", "language": "fr", "region": "Caribe", "continent": "Caribe"},
    
    # SUD AMERICA - BRASIL
    {"name": "Radio Vida Brasil", "url": "https://radiovida.com.br/", "stream_url": "https://radiovida.com.br/ao-vivo", "country": "Brasil", "language": "pt", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Rádio Trans Mundial", "url": "https://www.transmundial.com.br/", "stream_url": "https://www.transmundial.com.br/aovivo", "country": "Brasil", "language": "pt", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Novo Tempo Brasil", "url": "https://novotempo.com/radio/", "stream_url": "https://novotempo.com/radio/", "country": "Brasil", "language": "pt", "region": "Sudamerica", "continent": "SudAmerica"},
    {"name": "Radio Sara Brasil", "url": "https://radiosara.com.br/", "stream_url": "https://radiosara.com.br/", "country": "Brasil", "language": "pt", "region": "Sudamerica", "continent": "SudAmerica"},
    
    # AFRICA
    {"name": "Radio Palabre Vie", "url": "https://radioparolevie.org/", "stream_url": "https://radioparolevie.org/", "country": "Côte d'Ivoire", "language": "fr", "region": "Africa", "continent": "Africa"},
    {"name": "Transworld Radio Africa", "url": "https://www.twr.org/africa", "stream_url": "https://www.twr.org/africa", "country": "South Africa", "language": "en", "region": "Africa", "continent": "Africa"},
    {"name": "Radio Vie Abondante", "url": "https://rva.fm/", "stream_url": "https://rva.fm/ecouter", "country": "RDC", "language": "fr", "region": "Africa", "continent": "Africa"},
    {"name": "Family Radio Kenya", "url": "https://familyradio.co.ke/", "stream_url": "https://familyradio.co.ke/", "country": "Kenya", "language": "en", "region": "Africa", "continent": "Africa"},
    {"name": "Joy FM Ghana", "url": "https://www.myjoyonline.com/", "stream_url": "https://www.myjoyonline.com/", "country": "Ghana", "language": "en", "region": "Africa", "continent": "Africa"},
    
    # ASIA
    {"name": "FEBC Philippines", "url": "https://www.febc.ph/", "stream_url": "https://www.febc.ph/listen", "country": "Philippines", "language": "en", "region": "Asia", "continent": "Asia"},
    {"name": "Trans World Radio Asia", "url": "https://www.twr.org/asia", "stream_url": "https://www.twr.org/asia", "country": "Hong Kong", "language": "zh", "region": "Asia", "continent": "Asia"},
    {"name": "HCJB Korea", "url": "https://www.hcjb.or.kr/", "stream_url": "https://www.hcjb.or.kr/", "country": "South Korea", "language": "ko", "region": "Asia", "continent": "Asia"},
    
    # OCEANIA
    {"name": "Hope Radio Australia", "url": "https://hope1032.com.au/", "stream_url": "https://hope1032.com.au/listen", "country": "Australia", "language": "en", "region": "Oceania", "continent": "Oceania"},
    {"name": "Rhema FM New Zealand", "url": "https://www.rhema.co.nz/", "stream_url": "https://www.rhema.co.nz/", "country": "New Zealand", "language": "en", "region": "Oceania", "continent": "Oceania"},
]

# Worship/Lodi Content - Multilingual
WORSHIP_CONTENT = [
    # Italiano
    {"title": "Grande è il Signore", "artist": "Hillsong Italia", "type": "song", "language": "it", "youtube_url": "https://www.youtube.com/watch?v=example1", "duration": "5:32"},
    {"title": "Sei Degno", "artist": "Gen Verde", "type": "song", "language": "it", "youtube_url": "https://www.youtube.com/watch?v=example2", "duration": "4:15"},
    {"title": "Tu Sei Fedele", "artist": "Adorazione 5", "type": "song", "language": "it", "youtube_url": "https://www.youtube.com/watch?v=example3", "duration": "6:00"},
    # Español
    {"title": "Reckless Love (Amor Incomparable)", "artist": "Cory Asbury", "type": "song", "language": "es", "youtube_url": "https://www.youtube.com/watch?v=example4", "duration": "5:45"},
    {"title": "Océanos", "artist": "Hillsong United", "type": "song", "language": "es", "youtube_url": "https://www.youtube.com/watch?v=example5", "duration": "8:56"},
    {"title": "Grande es Tu Fidelidad", "artist": "Marco Barrientos", "type": "song", "language": "es", "youtube_url": "https://www.youtube.com/watch?v=example6", "duration": "4:30"},
    {"title": "Poderoso Dios", "artist": "Marcos Witt", "type": "song", "language": "es", "youtube_url": "https://www.youtube.com/watch?v=example7", "duration": "5:12"},
    # English
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "type": "song", "language": "en", "youtube_url": "https://www.youtube.com/watch?v=example8", "duration": "5:42"},
    {"title": "Goodness of God", "artist": "Bethel Music", "type": "song", "language": "en", "youtube_url": "https://www.youtube.com/watch?v=example9", "duration": "7:20"},
    {"title": "Way Maker", "artist": "Sinach", "type": "song", "language": "en", "youtube_url": "https://www.youtube.com/watch?v=example10", "duration": "6:15"},
    # Português
    {"title": "Quão Grande é o Meu Deus", "artist": "Soraya Moraes", "type": "song", "language": "pt", "youtube_url": "https://www.youtube.com/watch?v=example11", "duration": "5:30"},
    {"title": "Deus é Deus", "artist": "Delino Marçal", "type": "song", "language": "pt", "youtube_url": "https://www.youtube.com/watch?v=example12", "duration": "4:45"},
    # French
    {"title": "Roi des Rois", "artist": "Hillsong France", "type": "song", "language": "fr", "youtube_url": "https://www.youtube.com/watch?v=example13", "duration": "6:30"},
    {"title": "Mon Dieu est Plus Grand", "artist": "Glorious", "type": "song", "language": "fr", "youtube_url": "https://www.youtube.com/watch?v=example14", "duration": "5:00"},
]

@api_router.get("/worship")
async def get_worship_content(lang: Optional[str] = None):
    """Get worship/lodi content"""
    if lang:
        return [w for w in WORSHIP_CONTENT if w["language"] == lang]
    return WORSHIP_CONTENT

@api_router.get("/radios")
async def get_radios(lang: Optional[str] = None, region: Optional[str] = None, continent: Optional[str] = None):
    """Get evangelical radio stations filtered by language, region, or continent"""
    radios = EVANGELICAL_RADIOS
    if lang:
        radios = [r for r in radios if r["language"] == lang]
    if region:
        radios = [r for r in radios if r.get("region") == region]
    if continent:
        radios = [r for r in radios if r.get("continent") == continent]
    return radios

@api_router.get("/radios/continents")
async def get_radio_continents():
    """Get list of continents with radio count"""
    continents = {}
    for radio in EVANGELICAL_RADIOS:
        cont = radio.get("continent", "Other")
        if cont not in continents:
            continents[cont] = {"name": cont, "count": 0, "countries": set()}
        continents[cont]["count"] += 1
        continents[cont]["countries"].add(radio.get("country", ""))
    
    result = []
    for name, data in continents.items():
        result.append({
            "name": name,
            "count": data["count"],
            "countries": list(data["countries"])
        })
    return sorted(result, key=lambda x: x["count"], reverse=True)

# ==================== USER SETTINGS ====================

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

# ==================== FEELINGS - COME MI SENTO ====================

@api_router.post("/feelings/analyze")
async def analyze_feeling(data: FeelingRequest, user: User = Depends(require_auth)):
    """Analyze user's feelings and provide personalized Bible verses and guidance"""
    try:
        lang = data.language or user.language or "it"
        
        system_prompts = {
            "it": """Sei un consigliere spirituale cristiano compassionevole. L'utente ti condivide come si sente.
            
Rispondi in italiano con:
1. Empatia e comprensione per il suo stato d'animo
2. 3 versetti biblici specifici che parlano alla sua situazione (con riferimento completo)
3. Una breve riflessione su come questi versetti possono aiutarlo
4. Un'applicazione pratica per la sua vita quotidiana
5. Una preghiera breve e personale

Formatta la risposta in modo chiaro con sezioni separate.""",
            "es": """Eres un consejero espiritual cristiano compasivo. El usuario comparte cómo se siente.
Responde en español con empatía, 3 versículos bíblicos relevantes, reflexión y oración.""",
            "en": """You are a compassionate Christian spiritual counselor. The user shares how they feel.
Respond in English with empathy, 3 relevant Bible verses, reflection and prayer.""",
        }
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"feelings_{user.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message=system_prompts.get(lang, system_prompts["it"])
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=data.text))
        
        # Save feeling entry
        feeling_entry = {
            "feeling_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "text": data.text,
            "response": response,
            "language": lang,
            "created_at": datetime.now(timezone.utc)
        }
        await db.feelings.insert_one(feeling_entry)
        
        # Create notification
        await db.notifications.insert_one({
            "notification_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "title": "La Parola per Te",
            "body": "Ho preparato dei versetti speciali per te oggi",
            "notification_type": "verse",
            "data": {"feeling_id": feeling_entry["feeling_id"]},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "feeling_id": feeling_entry["feeling_id"],
            "response": response,
            "language": lang
        }
    except Exception as e:
        logger.error(f"Feeling analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")

@api_router.get("/feelings/history")
async def get_feelings_history(user: User = Depends(require_auth), limit: int = 20):
    """Get user's feelings history"""
    feelings = await db.feelings.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return feelings

# ==================== BIBLE STUDY NOTES ====================

STUDY_NOTES = {
    "Giovanni:3:16": {
        "historical_context": "Questo versetto fa parte del dialogo tra Gesù e Nicodemo, un fariseo e membro del Sinedrio. Il contesto è la Pasqua ebraica a Gerusalemme, circa 27-30 d.C.",
        "cross_references": ["Romani 5:8", "1 Giovanni 4:9", "Romani 8:32", "Isaia 9:6"],
        "hebrew_greek": "ἀγαπάω (agapao) - amore incondizionato, sacrificale. μονογενής (monogenes) - unigenito, unico nel suo genere.",
        "application": "Questo versetto ci ricorda che la salvezza è un dono gratuito di Dio. Non dobbiamo guadagnarla, ma semplicemente credere.",
        "commentary": "Considerato il 'Vangelo in miniatura', questo versetto riassume l'intero messaggio della salvezza cristiana: l'amore di Dio, il dono del Figlio, la fede come risposta, e la vita eterna come risultato."
    },
    "Salmi:23:1": {
        "historical_context": "Scritto da Davide, che era lui stesso un pastore prima di diventare re. Probabilmente scritto durante un periodo di riflessione sulla fedeltà di Dio.",
        "cross_references": ["Giovanni 10:11", "Ezechiele 34:11-16", "Isaia 40:11", "1 Pietro 2:25"],
        "hebrew_greek": "רָעָה (ra'ah) - pascolare, guidare, proteggere. La metafora del pastore era comune nel Medio Oriente antico per descrivere i re.",
        "application": "Possiamo confidare che Dio provvede per tutti i nostri bisogni, spirituali e materiali.",
        "commentary": "Il pastore nel mondo antico era responsabile della sicurezza, del nutrimento e della guida del gregge. Davide applica questa immagine a Dio."
    },
    "Filippesi:4:13": {
        "historical_context": "Paolo scrisse questa lettera dalla prigione a Roma, circa 61-62 d.C. Nonostante le difficoltà, esprime gioia e gratitudine.",
        "cross_references": ["2 Corinzi 12:9-10", "Giovanni 15:5", "Colossesi 1:11", "Efesini 3:16"],
        "hebrew_greek": "ἰσχύω (ischyo) - avere forza, essere capace. ἐνδυναμόω (endynamoo) - rafforzare internamente.",
        "application": "La vera forza viene da Cristo, non da noi stessi. In ogni situazione possiamo attingere alla Sua potenza.",
        "commentary": "Questo versetto è spesso citato fuori contesto. Paolo parla della capacità di affrontare qualsiasi circostanza, abbondanza o bisogno, attraverso Cristo."
    }
}

@api_router.get("/bible/study/{book}/{chapter}/{verse}")
async def get_study_notes(book: str, chapter: int, verse: int):
    """Get study notes for a specific verse"""
    key = f"{book}:{chapter}:{verse}"
    if key in STUDY_NOTES:
        return {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "notes": STUDY_NOTES[key]
        }
    
    # Generate AI study notes for verses not in database
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"study_{key}",
            system_message="""Sei un esperto biblista. Fornisci note di studio complete per il versetto richiesto in italiano.
            Includi:
            - Contesto storico (2-3 frasi)
            - 4 riferimenti incrociati con altri versetti
            - Note sul greco/ebraico originale
            - Applicazione pratica
            - Breve commentario"""
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=f"Fornisci note di studio per {book} {chapter}:{verse}"))
        
        return {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "notes": {
                "ai_generated": True,
                "content": response
            }
        }
    except Exception as e:
        return {
            "book": book,
            "chapter": chapter, 
            "verse": verse,
            "notes": None,
            "error": "Note di studio non disponibili"
        }

# ==================== GROUPS - FORUM STYLE ====================

GROUP_TOPICS = {
    "prayer": {"name": "Preghiera", "icon": "🙏", "color": "#6B7F5B"},
    "study": {"name": "Studio Biblico", "icon": "📖", "color": "#D4A574"},
    "testimony": {"name": "Testimonianze", "icon": "✨", "color": "#74B9FF"},
    "support": {"name": "Supporto", "icon": "💝", "color": "#FF7675"},
    "worship": {"name": "Adorazione", "icon": "🎵", "color": "#A29BFE"},
    "youth": {"name": "Giovani", "icon": "🌟", "color": "#FDCB6E"},
}

@api_router.get("/groups/topics")
async def get_group_topics():
    """Get available group topics"""
    return GROUP_TOPICS

@api_router.post("/groups")
async def create_group(data: GroupCreate, user: User = Depends(require_auth)):
    """Create a new group"""
    group = {
        "group_id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "topic": data.topic,
        "creator_id": user.user_id,
        "creator_name": user.name,
        "members": [user.user_id],
        "members_count": 1,
        "is_public": data.is_public,
        "language": data.language,
        "created_at": datetime.now(timezone.utc)
    }
    await db.groups.insert_one(group)
    group.pop("_id", None)
    return group

@api_router.get("/groups")
async def get_groups(topic: str = None, lang: str = None, user: User = Depends(require_auth)):
    """Get all public groups"""
    query = {"is_public": True}
    if topic:
        query["topic"] = topic
    if lang:
        query["language"] = lang
    
    groups = await db.groups.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return groups

@api_router.get("/groups/my")
async def get_my_groups(user: User = Depends(require_auth)):
    """Get user's groups"""
    groups = await db.groups.find(
        {"members": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return groups

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user: User = Depends(require_auth)):
    """Get group details"""
    group = await db.groups.find_one({"group_id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    return group

@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: User = Depends(require_auth)):
    """Join a group"""
    result = await db.groups.update_one(
        {"group_id": group_id},
        {
            "$addToSet": {"members": user.user_id},
            "$inc": {"members_count": 1}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    
    # Notify group creator
    group = await db.groups.find_one({"group_id": group_id}, {"_id": 0})
    if group and group["creator_id"] != user.user_id:
        await db.notifications.insert_one({
            "notification_id": str(uuid.uuid4()),
            "user_id": group["creator_id"],
            "title": "Nuovo membro",
            "body": f"{user.name} si è unito al gruppo {group['name']}",
            "notification_type": "group",
            "data": {"group_id": group_id},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        })
    
    return {"message": "Ti sei unito al gruppo"}

@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: User = Depends(require_auth)):
    """Leave a group"""
    await db.groups.update_one(
        {"group_id": group_id},
        {
            "$pull": {"members": user.user_id},
            "$inc": {"members_count": -1}
        }
    )
    return {"message": "Hai lasciato il gruppo"}

# Group Posts (Forum style)
@api_router.post("/groups/{group_id}/posts")
async def create_group_post(group_id: str, data: GroupPostCreate, user: User = Depends(require_auth)):
    """Create a post in a group"""
    # Verify user is member
    group = await db.groups.find_one({"group_id": group_id, "members": user.user_id})
    if not group:
        raise HTTPException(status_code=403, detail="Devi essere membro del gruppo")
    
    post = {
        "post_id": str(uuid.uuid4()),
        "group_id": group_id,
        "user_id": user.user_id,
        "user_name": user.name,
        "content": data.content,
        "post_type": data.post_type,
        "bible_reference": data.bible_reference,
        "likes": 0,
        "liked_by": [],
        "comments": [],
        "comments_count": 0,
        "created_at": datetime.now(timezone.utc)
    }
    await db.group_posts.insert_one(post)
    
    # Notify group members
    for member_id in group["members"]:
        if member_id != user.user_id:
            await db.notifications.insert_one({
                "notification_id": str(uuid.uuid4()),
                "user_id": member_id,
                "title": f"Nuovo post in {group['name']}",
                "body": f"{user.name} ha pubblicato: {data.content[:50]}...",
                "notification_type": "group",
                "data": {"group_id": group_id, "post_id": post["post_id"]},
                "is_read": False,
                "created_at": datetime.now(timezone.utc)
            })
    
    post.pop("_id", None)
    return post

@api_router.get("/groups/{group_id}/posts")
async def get_group_posts(group_id: str, user: User = Depends(require_auth), limit: int = 50):
    """Get posts in a group"""
    posts = await db.group_posts.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return posts

@api_router.post("/groups/{group_id}/posts/{post_id}/like")
async def like_post(group_id: str, post_id: str, user: User = Depends(require_auth)):
    """Like a post"""
    result = await db.group_posts.update_one(
        {"post_id": post_id, "liked_by": {"$ne": user.user_id}},
        {
            "$inc": {"likes": 1},
            "$addToSet": {"liked_by": user.user_id}
        }
    )
    return {"liked": result.modified_count > 0}

@api_router.post("/groups/{group_id}/posts/{post_id}/comment")
async def add_comment(group_id: str, post_id: str, request: Request, user: User = Depends(require_auth)):
    """Add a comment to a post"""
    body = await request.json()
    content = body.get("content", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="Contenuto richiesto")
    
    comment = {
        "comment_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.group_posts.update_one(
        {"post_id": post_id},
        {
            "$push": {"comments": comment},
            "$inc": {"comments_count": 1}
        }
    )
    
    # Notify post author
    post = await db.group_posts.find_one({"post_id": post_id})
    if post and post["user_id"] != user.user_id:
        await db.notifications.insert_one({
            "notification_id": str(uuid.uuid4()),
            "user_id": post["user_id"],
            "title": "Nuovo commento",
            "body": f"{user.name} ha commentato il tuo post",
            "notification_type": "comment",
            "data": {"group_id": group_id, "post_id": post_id},
            "is_read": False,
            "created_at": datetime.now(timezone.utc)
        })
    
    return comment

# ==================== PRIVATE MESSAGES ====================

@api_router.post("/messages")
async def send_private_message(data: PrivateMessageCreate, user: User = Depends(require_auth)):
    """Send a private message"""
    # Verify receiver exists
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
async def get_messages(user: User = Depends(require_auth)):
    """Get all conversations"""
    # Get unique conversation partners
    sent = await db.private_messages.find(
        {"sender_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    received = await db.private_messages.find(
        {"receiver_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Combine and get unique conversations
    all_messages = sent + received
    conversations = {}
    
    for msg in all_messages:
        other_id = msg["receiver_id"] if msg["sender_id"] == user.user_id else msg["sender_id"]
        if other_id not in conversations:
            other_user = await db.users.find_one({"user_id": other_id}, {"_id": 0, "password_hash": 0})
            conversations[other_id] = {
                "user_id": other_id,
                "user_name": other_user["name"] if other_user else "Utente",
                "last_message": msg,
                "unread_count": 0
            }
        if msg["receiver_id"] == user.user_id and not msg["is_read"]:
            conversations[other_id]["unread_count"] += 1
    
    return list(conversations.values())

@api_router.get("/messages/{other_user_id}")
async def get_conversation(other_user_id: str, user: User = Depends(require_auth)):
    """Get messages with a specific user"""
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender_id": user.user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": user.user_id}
            ]
        },
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Mark as read
    await db.private_messages.update_many(
        {"sender_id": other_user_id, "receiver_id": user.user_id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return messages

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

# ==================== QUIZ BIBLICO ====================

BIBLE_QUIZZES = {
    "genesi": {
        "title": "Quiz su Genesi",
        "description": "Testa la tua conoscenza del libro della Genesi",
        "questions": [
            {
                "id": "gen1",
                "question": "Cosa creò Dio nel primo giorno?",
                "options": ["La luce", "Il cielo", "Gli animali", "L'uomo"],
                "correct": 0,
                "explanation": "Nel primo giorno Dio disse: «Sia la luce!» E la luce fu. (Genesi 1:3)",
                "verse_ref": "Genesi 1:3"
            },
            {
                "id": "gen2",
                "question": "In quale giorno Dio creò l'uomo?",
                "options": ["Quinto", "Sesto", "Settimo", "Terzo"],
                "correct": 1,
                "explanation": "Dio creò l'uomo il sesto giorno, a sua immagine e somiglianza.",
                "verse_ref": "Genesi 1:26-27"
            },
            {
                "id": "gen3",
                "question": "Come si chiamava il giardino dove Dio pose l'uomo?",
                "options": ["Paradiso", "Eden", "Canaan", "Betlemme"],
                "correct": 1,
                "explanation": "L'Eterno Dio aveva piantato un giardino in Eden, a oriente.",
                "verse_ref": "Genesi 2:8"
            },
            {
                "id": "gen4",
                "question": "Quale albero era proibito ad Adamo ed Eva?",
                "options": ["Albero della vita", "Albero della conoscenza del bene e del male", "Ulivo", "Fico"],
                "correct": 1,
                "explanation": "Ma dell'albero della conoscenza del bene e del male non ne mangiare.",
                "verse_ref": "Genesi 2:17"
            },
            {
                "id": "gen5",
                "question": "Quanti giorni impiegò Dio per creare tutto?",
                "options": ["5 giorni", "6 giorni", "7 giorni", "3 giorni"],
                "correct": 1,
                "explanation": "Dio creò in sei giorni e si riposò il settimo.",
                "verse_ref": "Genesi 2:2"
            },
        ]
    },
    "salmi": {
        "title": "Quiz sui Salmi",
        "description": "Quanto conosci i Salmi?",
        "questions": [
            {
                "id": "sal1",
                "question": "Chi scrisse la maggior parte dei Salmi?",
                "options": ["Mosè", "Davide", "Salomone", "Asaf"],
                "correct": 1,
                "explanation": "Davide è l'autore della maggior parte dei Salmi.",
                "verse_ref": "Titoli dei Salmi"
            },
            {
                "id": "sal2",
                "question": "Completa: 'L'Eterno è il mio...'",
                "options": ["Re", "Pastore", "Salvatore", "Giudice"],
                "correct": 1,
                "explanation": "L'Eterno è il mio pastore, nulla mi mancherà.",
                "verse_ref": "Salmo 23:1"
            },
            {
                "id": "sal3",
                "question": "Quanti Salmi ci sono nella Bibbia?",
                "options": ["100", "120", "150", "200"],
                "correct": 2,
                "explanation": "Il libro dei Salmi contiene 150 salmi.",
                "verse_ref": "Libro dei Salmi"
            },
        ]
    },
    "vangeli": {
        "title": "Quiz sui Vangeli",
        "description": "La vita di Gesù nei Vangeli",
        "questions": [
            {
                "id": "van1",
                "question": "In quale città nacque Gesù?",
                "options": ["Nazaret", "Gerusalemme", "Betlemme", "Cafarnao"],
                "correct": 2,
                "explanation": "Gesù nacque a Betlemme di Giudea.",
                "verse_ref": "Matteo 2:1"
            },
            {
                "id": "van2",
                "question": "Quanti apostoli scelse Gesù?",
                "options": ["7", "10", "12", "14"],
                "correct": 2,
                "explanation": "Gesù scelse dodici apostoli.",
                "verse_ref": "Matteo 10:1-4"
            },
            {
                "id": "van3",
                "question": "Cosa disse Gesù: 'Io sono la via, la...'",
                "options": ["luce e la vita", "verità e la vita", "porta e la vita", "risurrezione"],
                "correct": 1,
                "explanation": "Io sono la via, la verità e la vita; nessuno viene al Padre se non per mezzo di me.",
                "verse_ref": "Giovanni 14:6"
            },
            {
                "id": "van4",
                "question": "Qual è il versetto più famoso della Bibbia?",
                "options": ["Genesi 1:1", "Salmo 23:1", "Giovanni 3:16", "Romani 8:28"],
                "correct": 2,
                "explanation": "Giovanni 3:16 è considerato il 'Vangelo in miniatura'.",
                "verse_ref": "Giovanni 3:16"
            },
        ]
    },
    "beatitudini": {
        "title": "Le Beatitudini",
        "description": "Il Sermone sul Monte",
        "questions": [
            {
                "id": "beat1",
                "question": "Dove Gesù pronunciò le Beatitudini?",
                "options": ["Nel tempio", "Sul monte", "Al mare", "Nel deserto"],
                "correct": 1,
                "explanation": "Vedendo le folle, Gesù salì sul monte. Il 'Sermone sul Monte' è uno dei discorsi più importanti di Gesù.",
                "verse_ref": "Matteo 5:1"
            },
            {
                "id": "beat2",
                "question": "'Beati i poveri in spirito, perché di loro è...'",
                "options": ["la terra", "il regno dei cieli", "la pace", "la gioia"],
                "correct": 1,
                "explanation": "Beati i poveri in spirito, perché di loro è il regno dei cieli. I poveri in spirito sono coloro che riconoscono la loro dipendenza da Dio.",
                "verse_ref": "Matteo 5:3"
            },
            {
                "id": "beat3",
                "question": "Quante sono le Beatitudini?",
                "options": ["5", "7", "8", "10"],
                "correct": 2,
                "explanation": "Le Beatitudini sono 8, e rappresentano le caratteristiche del vero discepolo di Cristo.",
                "verse_ref": "Matteo 5:3-12"
            },
        ]
    },
    "miracoli": {
        "title": "I Miracoli di Gesù",
        "description": "Le opere potenti del Signore",
        "questions": [
            {
                "id": "mir1",
                "question": "Quale fu il primo miracolo di Gesù?",
                "options": ["Guarire un lebbroso", "Camminare sull'acqua", "Trasformare l'acqua in vino", "Moltiplicare i pani"],
                "correct": 2,
                "explanation": "Alle nozze di Cana, Gesù trasformò l'acqua in vino. Fu il primo dei suoi segni.",
                "verse_ref": "Giovanni 2:1-11"
            },
            {
                "id": "mir2",
                "question": "Quanti pani e pesci usò Gesù per sfamare 5000 persone?",
                "options": ["5 pani e 2 pesci", "7 pani e 3 pesci", "3 pani e 5 pesci", "2 pani e 7 pesci"],
                "correct": 0,
                "explanation": "Un ragazzo aveva cinque pani d'orzo e due pesci. Gesù li moltiplicò per sfamare la folla.",
                "verse_ref": "Giovanni 6:9-11"
            },
            {
                "id": "mir3",
                "question": "Chi era Lazzaro?",
                "options": ["Un apostolo", "Un fariseo", "L'amico che Gesù risuscitò", "Il padre di Giovanni"],
                "correct": 2,
                "explanation": "Lazzaro era il fratello di Marta e Maria. Gesù lo risuscitò dopo quattro giorni dalla morte.",
                "verse_ref": "Giovanni 11:1-44"
            },
            {
                "id": "mir4",
                "question": "Quanti lebbrosi guarì Gesù, ma solo uno tornò a ringraziarlo?",
                "options": ["5", "7", "10", "12"],
                "correct": 2,
                "explanation": "Gesù guarì dieci lebbrosi, ma solo uno (un samaritano) tornò a ringraziarlo.",
                "verse_ref": "Luca 17:11-19"
            },
            {
                "id": "mir5",
                "question": "Chi camminò sull'acqua insieme a Gesù?",
                "options": ["Giovanni", "Pietro", "Giacomo", "Andrea"],
                "correct": 1,
                "explanation": "Pietro chiese a Gesù di poter andare verso di lui sull'acqua, ma poi iniziò ad affondare per la sua poca fede.",
                "verse_ref": "Matteo 14:28-31"
            },
        ]
    },
    "parabole": {
        "title": "Le Parabole di Gesù",
        "description": "Gli insegnamenti attraverso le storie",
        "questions": [
            {
                "id": "par1",
                "question": "Nella parabola del seminatore, cosa rappresenta il seme?",
                "options": ["I discepoli", "La Parola di Dio", "La fede", "Le opere buone"],
                "correct": 1,
                "explanation": "Il seme è la parola di Dio. I diversi terreni rappresentano i diversi modi in cui le persone ricevono la Parola.",
                "verse_ref": "Luca 8:11"
            },
            {
                "id": "par2",
                "question": "Nella parabola del figliol prodigo, cosa chiese il figlio minore?",
                "options": ["Una terra", "La sua parte di eredità", "Un lavoro", "Una sposa"],
                "correct": 1,
                "explanation": "Il figlio minore chiese la sua parte di eredità, la sperperò e poi tornò pentito dal padre che lo accolse con gioia.",
                "verse_ref": "Luca 15:11-32"
            },
            {
                "id": "par3",
                "question": "Chi aiutò l'uomo ferito nella parabola del buon Samaritano?",
                "options": ["Un levita", "Un sacerdote", "Un samaritano", "Un fariseo"],
                "correct": 2,
                "explanation": "Mentre il sacerdote e il levita passarono oltre, un samaritano (disprezzato dagli ebrei) si fermò ad aiutare.",
                "verse_ref": "Luca 10:30-37"
            },
            {
                "id": "par4",
                "question": "Quante vergini c'erano nella parabola delle dieci vergini?",
                "options": ["5 sagge e 5 stolte", "3 sagge e 7 stolte", "7 sagge e 3 stolte", "4 sagge e 6 stolte"],
                "correct": 0,
                "explanation": "Cinque vergini erano sagge (preparate con olio) e cinque stolte (senza olio). La parabola insegna l'importanza di essere sempre pronti.",
                "verse_ref": "Matteo 25:1-13"
            },
        ]
    },
    "profeti": {
        "title": "I Profeti dell'Antico Testamento",
        "description": "I messaggeri di Dio",
        "questions": [
            {
                "id": "pro1",
                "question": "Quale profeta fu inghiottito da un grande pesce?",
                "options": ["Elia", "Eliseo", "Giona", "Daniele"],
                "correct": 2,
                "explanation": "Giona cercò di fuggire dalla chiamata di Dio e fu inghiottito da un grande pesce per tre giorni.",
                "verse_ref": "Giona 1:17"
            },
            {
                "id": "pro2",
                "question": "Chi fu portato in cielo su un carro di fuoco?",
                "options": ["Mosè", "Elia", "Enoc", "Eliseo"],
                "correct": 1,
                "explanation": "Elia fu rapito in cielo in un turbine, con un carro e cavalli di fuoco, sotto gli occhi di Eliseo.",
                "verse_ref": "2 Re 2:11"
            },
            {
                "id": "pro3",
                "question": "Quale profeta ebbe la visione delle ossa secche?",
                "options": ["Isaia", "Geremia", "Ezechiele", "Daniele"],
                "correct": 2,
                "explanation": "Ezechiele ebbe la visione della valle delle ossa secche che tornarono in vita, simbolo della restaurazione di Israele.",
                "verse_ref": "Ezechiele 37:1-14"
            },
            {
                "id": "pro4",
                "question": "Chi interpretò i sogni del re Nabucodonosor?",
                "options": ["Giuseppe", "Daniele", "Elia", "Samuele"],
                "correct": 1,
                "explanation": "Daniele, con l'aiuto di Dio, interpretò i sogni del re babilonese Nabucodonosor.",
                "verse_ref": "Daniele 2:1-49"
            },
            {
                "id": "pro5",
                "question": "Quale profeta annunciò che il Messia sarebbe nato a Betlemme?",
                "options": ["Isaia", "Michea", "Osea", "Amos"],
                "correct": 1,
                "explanation": "Michea profetizzò che da Betlemme sarebbe uscito colui che doveva essere dominatore in Israele.",
                "verse_ref": "Michea 5:1"
            },
        ]
    },
    "apostoli": {
        "title": "Gli Apostoli e la Chiesa Primitiva",
        "description": "I primi seguaci di Cristo",
        "questions": [
            {
                "id": "apo1",
                "question": "Chi era l'apostolo dei Gentili?",
                "options": ["Pietro", "Giovanni", "Paolo", "Giacomo"],
                "correct": 2,
                "explanation": "Paolo (prima chiamato Saulo) ricevette la chiamata speciale di predicare ai Gentili (non ebrei).",
                "verse_ref": "Atti 9:15"
            },
            {
                "id": "apo2",
                "question": "Chi tradì Gesù per trenta denari?",
                "options": ["Pietro", "Giuda Iscariota", "Tommaso", "Matteo"],
                "correct": 1,
                "explanation": "Giuda Iscariota tradì Gesù consegnandolo ai capi dei sacerdoti per trenta monete d'argento.",
                "verse_ref": "Matteo 26:14-16"
            },
            {
                "id": "apo3",
                "question": "Quale apostolo dubitò della risurrezione di Gesù?",
                "options": ["Pietro", "Giovanni", "Tommaso", "Andrea"],
                "correct": 2,
                "explanation": "Tommaso disse che non avrebbe creduto finché non avesse visto e toccato le ferite di Gesù.",
                "verse_ref": "Giovanni 20:24-29"
            },
            {
                "id": "apo4",
                "question": "Chi fu scelto per sostituire Giuda tra gli apostoli?",
                "options": ["Paolo", "Barnaba", "Mattia", "Timoteo"],
                "correct": 2,
                "explanation": "Dopo l'Ascensione, gli apostoli tirarono a sorte e Mattia fu scelto per completare il numero dei Dodici.",
                "verse_ref": "Atti 1:23-26"
            },
        ]
    },
    "dieci_comandamenti": {
        "title": "I Dieci Comandamenti",
        "description": "La Legge di Dio",
        "questions": [
            {
                "id": "cmd1",
                "question": "Dove Dio diede i Dieci Comandamenti a Mosè?",
                "options": ["Monte Carmelo", "Monte Sinai", "Monte Sion", "Monte degli Ulivi"],
                "correct": 1,
                "explanation": "Dio diede i Dieci Comandamenti a Mosè sul Monte Sinai, scritti su tavole di pietra.",
                "verse_ref": "Esodo 20:1-17"
            },
            {
                "id": "cmd2",
                "question": "Qual è il primo comandamento?",
                "options": ["Non uccidere", "Non rubare", "Non avrai altri dèi davanti a me", "Onora tuo padre e tua madre"],
                "correct": 2,
                "explanation": "Il primo comandamento stabilisce che Dio è l'unico vero Dio da adorare.",
                "verse_ref": "Esodo 20:3"
            },
            {
                "id": "cmd3",
                "question": "Quale comandamento riguarda il giorno di riposo?",
                "options": ["Il terzo", "Il quarto", "Il quinto", "Il sesto"],
                "correct": 1,
                "explanation": "Il quarto comandamento dice: 'Ricordati del giorno del riposo per santificarlo'.",
                "verse_ref": "Esodo 20:8-11"
            },
        ]
    }
}

from quiz_data import MULTILINGUAL_QUIZZES, get_quiz_for_language, get_all_topics_for_language
from quiz_1000 import get_quiz_1000_topics, get_quiz_1000_by_category, get_quiz_1000_by_category_translated

@api_router.get("/quiz/topics")
async def get_quiz_topics(lang: str = "it"):
    """Get available quiz topics in specified language"""
    return get_all_topics_for_language(lang)

# ==================== QUIZ 1000 - NEW CATEGORY SYSTEM ====================

@api_router.get("/quiz/categories")
async def get_quiz_categories(lang: str = "it"):
    """Get all quiz categories (1000 questions organized in 33 themes)"""
    return get_quiz_1000_topics(lang)

@api_router.get("/quiz/category/{category_id}")
async def get_quiz_by_category(category_id: str, lang: str = "it", translate: bool = True):
    """Get quiz questions for a specific category with optional translation"""
    if translate and lang != 'it':
        quiz = await get_quiz_1000_by_category_translated(category_id, lang)
    else:
        quiz = get_quiz_1000_by_category(category_id, lang)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    return quiz

@api_router.get("/quiz/{topic}")
async def get_quiz(topic: str, lang: str = "it"):
    """Get quiz by topic in specified language"""
    quiz = get_quiz_for_language(topic, lang)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz non trovato")
    return quiz

class QuizSubmission(BaseModel):
    topic: str
    answers: Dict[str, int]  # question_id -> selected_option_index
    language: str = "it"  # Language for quiz lookup

@api_router.post("/quiz/submit")
async def submit_quiz(data: QuizSubmission, user: User = Depends(require_auth)):
    """Submit quiz answers and get AI feedback - supports both classic and category quizzes"""
    lang = data.language or 'it'
    quiz = None
    quiz_title = ""
    
    # Check if it's a category quiz (new 1000 questions system)
    if data.topic.startswith('cat_'):
        from quiz_1000 import get_quiz_1000_by_category
        category_quiz = get_quiz_1000_by_category(data.topic, lang)
        if category_quiz:
            quiz = {"questions": category_quiz["questions"], "title": category_quiz["title"]}
            quiz_title = category_quiz["title"]
    else:
        # Classic quiz
        quiz = get_quiz_for_language(data.topic, lang)
        if quiz:
            quiz_title = quiz.get("title", data.topic)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz non trovato")
    
    correct_count = 0
    total = len(quiz["questions"])
    results = []
    
    for question in quiz["questions"]:
        user_answer = data.answers.get(question["id"], -1)
        is_correct = user_answer == question["correct"]
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": question["id"],
            "is_correct": is_correct,
            "correct_answer": question["correct"],
            "user_answer": user_answer,
            "explanation": question.get("explanation", ""),
            "verse_ref": question.get("verse_ref", ""),
            "question_text": question.get("question", ""),
            "options": question.get("options", [])
        })
    
    score = (correct_count / total) * 100 if total > 0 else 0
    
    # Language-specific feedback prompts
    feedback_prompts = {
        "it": f"L'utente ha completato il quiz '{quiz_title}' con un punteggio di {score:.0f}% ({correct_count}/{total} risposte corrette). Dai un feedback breve e incoraggiante in italiano.",
        "es": f"El usuario completó el quiz '{quiz_title}' con una puntuación del {score:.0f}% ({correct_count}/{total} respuestas correctas). Da un feedback breve y alentador en español.",
        "en": f"The user completed the quiz '{quiz_title}' with a score of {score:.0f}% ({correct_count}/{total} correct answers). Give brief and encouraging feedback in English.",
        "de": f"Der Benutzer hat das Quiz '{quiz_title}' mit {score:.0f}% ({correct_count}/{total} richtige Antworten) abgeschlossen. Gib kurzes, ermutigendes Feedback auf Deutsch.",
        "fr": f"L'utilisateur a terminé le quiz '{quiz_title}' avec un score de {score:.0f}% ({correct_count}/{total} bonnes réponses). Donne un feedback bref et encourageant en français.",
        "pt": f"O usuário completou o quiz '{quiz_title}' com pontuação de {score:.0f}% ({correct_count}/{total} respostas corretas). Dê um feedback breve e encorajador em português."
    }
    
    # Generate AI feedback
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"quiz_{user.user_id}_{data.topic}",
            system_message="You are a Bible teacher. Give encouraging feedback based on quiz scores."
        ).with_model("openai", "gpt-4o")
        
        feedback = await chat.send_message(UserMessage(
            text=feedback_prompts.get(lang, feedback_prompts["it"])
        ))
    except:
        default_feedback = {
            "it": f"Hai completato il quiz con {correct_count}/{total} risposte corrette!",
            "es": f"¡Completaste el quiz con {correct_count}/{total} respuestas correctas!",
            "en": f"You completed the quiz with {correct_count}/{total} correct answers!",
            "de": f"Du hast das Quiz mit {correct_count}/{total} richtigen Antworten abgeschlossen!",
            "fr": f"Vous avez terminé le quiz avec {correct_count}/{total} bonnes réponses !",
            "pt": f"Você completou o quiz com {correct_count}/{total} respostas corretas!"
        }
        feedback = default_feedback.get(lang, default_feedback["it"])
    
    # Save result
    await db.quiz_results.insert_one({
        "result_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "topic": data.topic,
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "language": lang,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "results": results,
        "feedback": feedback
    }

@api_router.get("/quiz/history")
async def get_quiz_history(user: User = Depends(require_auth)):
    """Get user's quiz history"""
    history = await db.quiz_results.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return history

# ==================== DIZIONARIO BIBLICO ====================

from biblical_dictionary import BIBLICAL_DICTIONARY

# Translations for dictionary UI labels and term metadata
DICT_TRANSLATIONS = {
    "it": {"origin_hebrew": "Ebraico", "origin_greek": "Greco", "origin_aramaic": "Aramaico", "transliteration": "Traslitterazione", "pronunciation": "Pronuncia", "meaning_label": "Significato", "root_label": "Radice", "equivalents": "Equivalenti", "description": "Descrizione", "verses_label": "Versetti di Riferimento", "ask_ai": "Chiedi all'AI", "search_placeholder": "Cerca termine...", "subtitle": "Esplora i termini originali ebraici e greci della Bibbia"},
    "en": {"origin_hebrew": "Hebrew", "origin_greek": "Greek", "origin_aramaic": "Aramaic", "transliteration": "Transliteration", "pronunciation": "Pronunciation", "meaning_label": "Meaning", "root_label": "Root", "equivalents": "Equivalents", "description": "Description", "verses_label": "Reference Verses", "ask_ai": "Ask AI", "search_placeholder": "Search term...", "subtitle": "Explore the original Hebrew and Greek terms of the Bible"},
    "es": {"origin_hebrew": "Hebreo", "origin_greek": "Griego", "origin_aramaic": "Arameo", "transliteration": "Transliteración", "pronunciation": "Pronunciación", "meaning_label": "Significado", "root_label": "Raíz", "equivalents": "Equivalentes", "description": "Descripción", "verses_label": "Versículos de Referencia", "ask_ai": "Preguntar a la IA", "search_placeholder": "Buscar término...", "subtitle": "Explora los términos originales hebreos y griegos de la Biblia"},
    "de": {"origin_hebrew": "Hebräisch", "origin_greek": "Griechisch", "origin_aramaic": "Aramäisch", "transliteration": "Transliteration", "pronunciation": "Aussprache", "meaning_label": "Bedeutung", "root_label": "Wurzel", "equivalents": "Äquivalente", "description": "Beschreibung", "verses_label": "Referenzverse", "ask_ai": "KI fragen", "search_placeholder": "Begriff suchen...", "subtitle": "Erkunde die ursprünglichen hebräischen und griechischen Begriffe der Bibel"},
    "fr": {"origin_hebrew": "Hébreu", "origin_greek": "Grec", "origin_aramaic": "Araméen", "transliteration": "Translittération", "pronunciation": "Prononciation", "meaning_label": "Signification", "root_label": "Racine", "equivalents": "Équivalents", "description": "Description", "verses_label": "Versets de Référence", "ask_ai": "Demander à l'IA", "search_placeholder": "Rechercher un terme...", "subtitle": "Explorez les termes hébreux et grecs originaux de la Bible"},
    "pt": {"origin_hebrew": "Hebraico", "origin_greek": "Grego", "origin_aramaic": "Aramaico", "transliteration": "Transliteração", "pronunciation": "Pronúncia", "meaning_label": "Significado", "root_label": "Raiz", "equivalents": "Equivalentes", "description": "Descrição", "verses_label": "Versículos de Referência", "ask_ai": "Perguntar à IA", "search_placeholder": "Buscar termo...", "subtitle": "Explore os termos originais hebraicos e gregos da Bíblia"},
}

# Translated meanings for dictionary terms
DICT_TERM_TRANSLATIONS = {
    "agape": {
        "en": {"meaning": "Unconditional love, divine love", "description": "Agape is the highest form of love in Christian theology. Unlike eros (romantic love) or philia (friendship), agape is a selfless, unconditional love. It is the love of God for humanity and the love Christians are called to show one another. In the New Testament, agape defines the very nature of God: 'God is love' (1 John 4:8)."},
        "es": {"meaning": "Amor incondicional, amor divino", "description": "Ágape es la forma más alta de amor en la teología cristiana. A diferencia de eros (amor romántico) o philia (amistad), ágape es un amor desinteresado e incondicional. Es el amor de Dios por la humanidad y el amor que los cristianos están llamados a mostrar. En el Nuevo Testamento, ágape define la naturaleza misma de Dios: 'Dios es amor' (1 Juan 4:8)."},
        "de": {"meaning": "Bedingungslose Liebe, göttliche Liebe", "description": "Agape ist die höchste Form der Liebe in der christlichen Theologie. Im Unterschied zu Eros (romantische Liebe) oder Philia (Freundschaft) ist Agape eine selbstlose, bedingungslose Liebe. Sie ist die Liebe Gottes zur Menschheit und die Liebe, zu der Christen aufgerufen sind. Im Neuen Testament definiert Agape das Wesen Gottes: 'Gott ist Liebe' (1. Johannes 4:8)."},
        "fr": {"meaning": "Amour inconditionnel, amour divin", "description": "L'agapè est la forme la plus élevée d'amour dans la théologie chrétienne. Contrairement à éros (amour romantique) ou philia (amitié), l'agapè est un amour désintéressé et inconditionnel. C'est l'amour de Dieu pour l'humanité et l'amour que les chrétiens sont appelés à manifester. Dans le Nouveau Testament, agapè définit la nature même de Dieu : 'Dieu est amour' (1 Jean 4:8)."},
        "pt": {"meaning": "Amor incondicional, amor divino", "description": "Ágape é a forma mais elevada de amor na teologia cristã. Diferente de eros (amor romântico) ou philia (amizade), ágape é um amor abnegado e incondicional. É o amor de Deus pela humanidade e o amor que os cristãos são chamados a demonstrar. No Novo Testamento, ágape define a própria natureza de Deus: 'Deus é amor' (1 João 4:8)."},
    },
    "shalom": {
        "en": {"meaning": "Peace, completeness, welfare, prosperity", "description": "Shalom is much more than just 'peace' or the absence of conflict. It encompasses completeness, wholeness, harmony, well-being, and prosperity. In the Bible, shalom represents God's ideal state for creation and human relationships. It is used as both greeting and blessing."},
        "es": {"meaning": "Paz, completitud, bienestar, prosperidad", "description": "Shalom es mucho más que simplemente 'paz' o ausencia de conflicto. Abarca completitud, totalidad, armonía, bienestar y prosperidad. En la Biblia, shalom representa el estado ideal de Dios para la creación y las relaciones humanas. Se usa tanto como saludo como bendición."},
        "de": {"meaning": "Frieden, Ganzheit, Wohlergehen, Wohlstand", "description": "Schalom ist viel mehr als nur 'Frieden' oder die Abwesenheit von Konflikten. Es umfasst Vollständigkeit, Ganzheit, Harmonie, Wohlergehen und Wohlstand. In der Bibel repräsentiert Schalom Gottes idealen Zustand für die Schöpfung und menschliche Beziehungen. Es wird als Gruß und Segen verwendet."},
        "fr": {"meaning": "Paix, plénitude, bien-être, prospérité", "description": "Shalom est bien plus que simplement 'paix' ou l'absence de conflit. Il englobe la plénitude, l'intégralité, l'harmonie, le bien-être et la prospérité. Dans la Bible, shalom représente l'état idéal de Dieu pour la création et les relations humaines. Il est utilisé comme salutation et bénédiction."},
        "pt": {"meaning": "Paz, plenitude, bem-estar, prosperidade", "description": "Shalom é muito mais do que simplesmente 'paz' ou ausência de conflito. Abrange plenitude, totalidade, harmonia, bem-estar e prosperidade. Na Bíblia, shalom representa o estado ideal de Deus para a criação e as relações humanas. É usado tanto como saudação quanto como bênção."},
    },
    "logos": {
        "en": {"meaning": "Word, Verb, reason, discourse", "description": "In Greek philosophy, Logos was the rational principle governing the cosmos. The apostle John revolutionized this concept by identifying the Logos with Jesus Christ: 'In the beginning was the Word' (John 1:1). The Logos is the self-expression of God, His creative power, and His revelation to humanity."},
        "es": {"meaning": "Palabra, Verbo, razón, discurso", "description": "En la filosofía griega, Logos era el principio racional que gobernaba el cosmos. El apóstol Juan revolucionó este concepto al identificar el Logos con Jesucristo: 'En el principio era el Verbo' (Juan 1:1). El Logos es la autoexpresión de Dios, su poder creativo y su revelación a la humanidad."},
        "de": {"meaning": "Wort, Vernunft, Rede", "description": "In der griechischen Philosophie war Logos das rationale Prinzip, das den Kosmos regiert. Der Apostel Johannes revolutionierte dieses Konzept, indem er den Logos mit Jesus Christus identifizierte: 'Im Anfang war das Wort' (Johannes 1:1). Der Logos ist Gottes Selbstausdruck, seine schöpferische Kraft und seine Offenbarung an die Menschheit."},
        "fr": {"meaning": "Parole, Verbe, raison, discours", "description": "Dans la philosophie grecque, le Logos était le principe rationnel gouvernant le cosmos. L'apôtre Jean a révolutionné ce concept en identifiant le Logos avec Jésus-Christ : 'Au commencement était la Parole' (Jean 1:1). Le Logos est l'auto-expression de Dieu, sa puissance créatrice et sa révélation à l'humanité."},
        "pt": {"meaning": "Palavra, Verbo, razão, discurso", "description": "Na filosofia grega, Logos era o princípio racional que governava o cosmos. O apóstolo João revolucionou este conceito ao identificar o Logos com Jesus Cristo: 'No princípio era o Verbo' (João 1:1). O Logos é a auto-expressão de Deus, seu poder criativo e sua revelação à humanidade."},
    },
    "pneuma": {
        "en": {"meaning": "Spirit, breath, wind", "description": "Pneuma indicates the Spirit of God, the Holy Spirit. In the New Testament it is used over 370 times. Pneuma is the living and active presence of God in the world. Jesus promises the Spirit as 'Comforter' (Parakletos) who will guide believers in all truth."},
        "es": {"meaning": "Espíritu, aliento, viento", "description": "Pneuma indica el Espíritu de Dios, el Espíritu Santo. En el Nuevo Testamento se usa más de 370 veces. Pneuma es la presencia viva y activa de Dios en el mundo. Jesús promete el Espíritu como 'Consolador' (Parakletos) que guiará a los creyentes a toda verdad."},
        "de": {"meaning": "Geist, Atem, Wind", "description": "Pneuma bezeichnet den Geist Gottes, den Heiligen Geist. Im Neuen Testament wird es über 370 Mal verwendet. Pneuma ist die lebendige und aktive Gegenwart Gottes in der Welt. Jesus verspricht den Geist als 'Tröster' (Parakletos), der die Gläubigen in alle Wahrheit leiten wird."},
        "fr": {"meaning": "Esprit, souffle, vent", "description": "Pneuma désigne l'Esprit de Dieu, le Saint-Esprit. Dans le Nouveau Testament, il est utilisé plus de 370 fois. Pneuma est la présence vivante et active de Dieu dans le monde. Jésus promet l'Esprit comme 'Consolateur' (Parakletos) qui guidera les croyants dans toute la vérité."},
        "pt": {"meaning": "Espírito, sopro, vento", "description": "Pneuma indica o Espírito de Deus, o Espírito Santo. No Novo Testamento é usado mais de 370 vezes. Pneuma é a presença viva e ativa de Deus no mundo. Jesus promete o Espírito como 'Consolador' (Parakletos) que guiará os crentes em toda a verdade."},
    },
    "chesed": {
        "en": {"meaning": "Faithful love, kindness, mercy, grace", "description": "Chesed is God's faithful love for His people, based on the covenant. It is a love that never abandons, that forgives, that remains faithful even when the other fails. It is one of the most important attributes of God in the Old Testament."},
        "es": {"meaning": "Amor fiel, bondad, misericordia, gracia", "description": "Chesed es el amor fiel de Dios hacia su pueblo, basado en el pacto. Es un amor que no abandona, que perdona, que permanece fiel incluso cuando el otro falla. Es uno de los atributos más importantes de Dios en el Antiguo Testamento."},
        "de": {"meaning": "Treue Liebe, Güte, Barmherzigkeit, Gnade", "description": "Chesed ist Gottes treue Liebe zu seinem Volk, basierend auf dem Bund. Es ist eine Liebe, die nicht aufgibt, die vergibt, die treu bleibt, auch wenn der andere versagt. Es ist eines der wichtigsten Attribute Gottes im Alten Testament."},
        "fr": {"meaning": "Amour fidèle, bonté, miséricorde, grâce", "description": "Chesed est l'amour fidèle de Dieu envers son peuple, fondé sur l'alliance. C'est un amour qui n'abandonne pas, qui pardonne, qui reste fidèle même quand l'autre échoue. C'est l'un des attributs les plus importants de Dieu dans l'Ancien Testament."},
        "pt": {"meaning": "Amor fiel, bondade, misericórdia, graça", "description": "Chesed é o amor fiel de Deus ao seu povo, baseado na aliança. É um amor que não abandona, que perdoa, que permanece fiel mesmo quando o outro falha. É um dos atributos mais importantes de Deus no Antigo Testamento."},
    },
    "amen": {
        "en": {"meaning": "So be it, truly, certainly", "description": "Amen is a word of affirmation and confirmation. It is used to ratify prayers, blessings, and declarations. Jesus often uses it at the beginning of His statements ('Truly, truly I say to you')."},
        "es": {"meaning": "Así sea, en verdad, ciertamente", "description": "Amén es una palabra de afirmación y confirmación. Se usa para ratificar oraciones, bendiciones y declaraciones. Jesús la usa frecuentemente al inicio de sus afirmaciones ('De cierto, de cierto os digo')."},
        "de": {"meaning": "So sei es, wahrlich, gewiss", "description": "Amen ist ein Wort der Bestätigung und Bekräftigung. Es wird verwendet, um Gebete, Segnungen und Erklärungen zu bestätigen. Jesus verwendet es oft am Anfang seiner Aussagen ('Wahrlich, wahrlich, ich sage euch')."},
        "fr": {"meaning": "Ainsi soit-il, en vérité, certainement", "description": "Amen est un mot d'affirmation et de confirmation. Il est utilisé pour ratifier les prières, bénédictions et déclarations. Jésus l'utilise souvent au début de ses affirmations ('En vérité, en vérité, je vous le dis')."},
        "pt": {"meaning": "Assim seja, em verdade, certamente", "description": "Amém é uma palavra de afirmação e confirmação. É usada para ratificar orações, bênçãos e declarações. Jesus a usa frequentemente no início de suas afirmações ('Em verdade, em verdade vos digo')."},
    },
    "elohim": {
        "en": {"meaning": "God, gods, mighty ones", "description": "Elohim is one of the most common names for God in the Old Testament. Although grammatically plural, when referring to the God of Israel it is used with singular verbs, suggesting unity in plurality (a possible allusion to the Trinity)."},
        "es": {"meaning": "Dios, dioses, poderosos", "description": "Elohim es uno de los nombres más comunes para Dios en el Antiguo Testamento. Aunque es gramaticalmente plural, cuando se refiere al Dios de Israel se usa con verbos en singular, sugiriendo unidad en la pluralidad (posible alusión a la Trinidad)."},
        "de": {"meaning": "Gott, Götter, Mächtige", "description": "Elohim ist einer der häufigsten Namen für Gott im Alten Testament. Obwohl grammatisch Plural, wird es in Bezug auf den Gott Israels mit Verben im Singular verwendet, was Einheit in der Vielfalt nahelegt (möglicher Hinweis auf die Dreieinigkeit)."},
        "fr": {"meaning": "Dieu, dieux, puissants", "description": "Elohim est l'un des noms les plus courants pour Dieu dans l'Ancien Testament. Bien que grammaticalement pluriel, lorsqu'il fait référence au Dieu d'Israël, il est utilisé avec des verbes au singulier, suggérant l'unité dans la pluralité (possible allusion à la Trinité)."},
        "pt": {"meaning": "Deus, deuses, poderosos", "description": "Elohim é um dos nomes mais comuns para Deus no Antigo Testamento. Embora gramaticalmente plural, quando se refere ao Deus de Israel é usado com verbos no singular, sugerindo unidade na pluralidade (possível alusão à Trindade)."},
    },
    "yhwh": {
        "en": {"meaning": "I Am, The One Who Is", "description": "The proper name of God revealed to Moses. It is the sacred tetragrammaton, considered so holy that Jews avoid pronouncing it, replacing it with 'Adonai' (Lord). It indicates God's eternity and self-existence."},
        "es": {"meaning": "Yo Soy, El que Es", "description": "El nombre propio de Dios revelado a Moisés. Es el tetragramatón sagrado, considerado tan santo que los judíos evitan pronunciarlo, sustituyéndolo por 'Adonai' (Señor). Indica la eternidad y autoexistencia de Dios."},
        "de": {"meaning": "Ich Bin, Der der Ist", "description": "Der Eigenname Gottes, der Mose offenbart wurde. Es ist das heilige Tetragrammaton, das als so heilig gilt, dass Juden es vermeiden auszusprechen und es durch 'Adonai' (Herr) ersetzen. Es zeigt Gottes Ewigkeit und Selbstexistenz an."},
        "fr": {"meaning": "Je Suis, Celui qui Est", "description": "Le nom propre de Dieu révélé à Moïse. C'est le tétragramme sacré, considéré si saint que les Juifs évitent de le prononcer, le remplaçant par 'Adonaï' (Seigneur). Il indique l'éternité et l'auto-existence de Dieu."},
        "pt": {"meaning": "Eu Sou, Aquele que É", "description": "O nome próprio de Deus revelado a Moisés. É o tetragrama sagrado, considerado tão santo que os judeus evitam pronunciá-lo, substituindo-o por 'Adonai' (Senhor). Indica a eternidade e auto-existência de Deus."},
    },
}

def translate_dict_term(term_data: dict, term_id: str, lang: str) -> dict:
    """Return dictionary term with translated fields"""
    if lang == "it" or lang not in DICT_TRANSLATIONS:
        return term_data
    translations = DICT_TERM_TRANSLATIONS.get(term_id, {}).get(lang, {})
    labels = DICT_TRANSLATIONS.get(lang, DICT_TRANSLATIONS["it"])
    result = {**term_data}
    if translations.get("meaning"):
        result["meaning"] = translations["meaning"]
    if translations.get("description"):
        result["description"] = translations["description"]
    origin = term_data.get("origin", "")
    if origin == "Ebraico":
        result["origin"] = labels["origin_hebrew"]
    elif origin == "Greco":
        result["origin"] = labels["origin_greek"]
    return result

@api_router.get("/dictionary")
async def get_dictionary_terms(lang: str = "it"):
    """Get all dictionary terms with optional translation, sorted alphabetically"""
    labels = DICT_TRANSLATIONS.get(lang, DICT_TRANSLATIONS["it"])
    
    def get_origin_label(origin: str) -> str:
        if origin == "Ebraico":
            return labels["origin_hebrew"]
        elif origin == "Greco":
            return labels["origin_greek"]
        elif origin == "Aramaico":
            return labels.get("origin_aramaic", "Aramaic")
        elif origin == "Ebraico/Aramaico":
            return f"{labels['origin_hebrew']}/{labels.get('origin_aramaic', 'Aramaic')}"
        return origin
    
    results = []
    
    # First, collect all cached translations from MongoDB
    cached_translations = {}
    cursor = db.dictionary_translations.find({"language": lang}, {"_id": 0})
    async for doc in cursor:
        cached_translations[doc["term_id"]] = doc
    
    for key, term in BIBLICAL_DICTIONARY.items():
        meaning = term["meaning"]
        
        if lang != "it":
            # Check pre-translated versions first
            if key in DICT_TERM_TRANSLATIONS and lang in DICT_TERM_TRANSLATIONS[key]:
                meaning = DICT_TERM_TRANSLATIONS[key][lang].get("meaning", term["meaning"])
            # Check MongoDB cache for AI translations
            elif key in cached_translations and cached_translations[key].get("meaning"):
                meaning = cached_translations[key]["meaning"]
        
        results.append({
            "id": key,
            "term": term["term"],
            "origin": get_origin_label(term["origin"]),
            "meaning": meaning,
        })
    
    # Sort alphabetically by term (ignoring parentheses content)
    results.sort(key=lambda x: x["term"].split(" (")[0].lower())
    
    return results

async def ai_translate_dict_term(term_data: dict, term_id: str, target_lang: str) -> dict:
    """Use AI to translate dictionary term and cache the result"""
    lang_names = {
        "en": "English",
        "es": "Spanish",
        "de": "German",
        "fr": "French",
        "pt": "Portuguese"
    }
    
    if target_lang not in lang_names:
        return term_data
    
    # Check if we already have cached translation in MongoDB
    cached = await db.dictionary_translations.find_one({
        "term_id": term_id,
        "language": target_lang
    }, {"_id": 0})
    
    if cached:
        result = {**term_data}
        result["meaning"] = cached.get("meaning", term_data["meaning"])
        result["description"] = cached.get("description", term_data["description"])
        labels = DICT_TRANSLATIONS.get(target_lang, DICT_TRANSLATIONS["it"])
        if term_data.get("origin") == "Ebraico":
            result["origin"] = labels["origin_hebrew"]
        elif term_data.get("origin") == "Greco":
            result["origin"] = labels["origin_greek"]
        elif term_data.get("origin") == "Aramaico":
            result["origin"] = labels.get("origin_aramaic", "Aramaic")
        return result
    
    try:
        lang_name = lang_names[target_lang]
        prompt = f"""Translate this biblical dictionary entry to {lang_name}.
Return ONLY a valid JSON object with "meaning" and "description" fields.

Term: {term_data['term']}
Meaning (Italian): {term_data['meaning']}
Description (Italian): {term_data['description'][:800]}

Return format: {{"meaning": "translated meaning", "description": "translated description"}}"""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"dict_trans_{term_id}_{target_lang}",
            system_message="You are a biblical translator. Return only valid JSON."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=prompt))
        response = response.strip()
        
        # Clean response
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        if response.startswith("json"):
            response = response[4:].strip()
        
        translation = json.loads(response)
        
        # Cache in MongoDB
        await db.dictionary_translations.update_one(
            {"term_id": term_id, "language": target_lang},
            {"$set": {
                "term_id": term_id,
                "language": target_lang,
                "meaning": translation.get("meaning", ""),
                "description": translation.get("description", ""),
                "created_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        result = {**term_data}
        result["meaning"] = translation.get("meaning", term_data["meaning"])
        result["description"] = translation.get("description", term_data["description"])
        
        labels = DICT_TRANSLATIONS.get(target_lang, DICT_TRANSLATIONS["it"])
        if term_data.get("origin") == "Ebraico":
            result["origin"] = labels["origin_hebrew"]
        elif term_data.get("origin") == "Greco":
            result["origin"] = labels["origin_greek"]
        elif term_data.get("origin") == "Aramaico":
            result["origin"] = labels.get("origin_aramaic", "Aramaic")
        
        return result
        
    except Exception as e:
        logger.error(f"AI translation error for {term_id} to {target_lang}: {e}")
        return translate_dict_term(term_data, term_id, target_lang)

@api_router.get("/dictionary/search/{query}")
async def search_dictionary(query: str):
    """Search dictionary terms"""
    query_lower = query.lower()
    results = []
    for key, term in BIBLICAL_DICTIONARY.items():
        if (query_lower in term["term"].lower() or 
            query_lower in term["meaning"].lower() or
            query_lower in term.get("description", "").lower()):
            results.append({
                "id": key,
                "term": term["term"],
                "origin": term["origin"],
                "meaning": term["meaning"]
            })
    return results

# ==================== DICTIONARY FAVORITES & FLASHCARDS ====================

class FavoriteTermRequest(BaseModel):
    term_id: str

class FlashcardCreateRequest(BaseModel):
    term_id: str
    note: Optional[str] = None

class FlashcardUpdateRequest(BaseModel):
    note: Optional[str] = None
    mastery_level: Optional[int] = None  # 0-5 scale
    last_reviewed: Optional[datetime] = None

@api_router.get("/dictionary/favorites")
async def get_favorite_terms(user: User = Depends(require_auth), lang: str = "it"):
    """Get user's favorite dictionary terms"""
    favorites_cursor = db.dictionary_favorites.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1)
    
    favorites = []
    async for fav in favorites_cursor:
        term_id = fav["term_id"]
        if term_id in BIBLICAL_DICTIONARY:
            term = BIBLICAL_DICTIONARY[term_id]
            meaning = term["meaning"]
            
            # Get translated meaning if available
            if lang != "it":
                if term_id in DICT_TERM_TRANSLATIONS and lang in DICT_TERM_TRANSLATIONS[term_id]:
                    meaning = DICT_TERM_TRANSLATIONS[term_id][lang].get("meaning", term["meaning"])
                else:
                    cached = await db.dictionary_translations.find_one({
                        "term_id": term_id, "language": lang
                    }, {"_id": 0})
                    if cached and cached.get("meaning"):
                        meaning = cached["meaning"]
            
            favorites.append({
                "term_id": term_id,
                "term": term["term"],
                "meaning": meaning,
                "origin": term["origin"],
                "added_at": fav.get("created_at", datetime.now(timezone.utc)).isoformat()
            })
    
    return favorites

@api_router.post("/dictionary/favorites")
async def add_favorite_term(data: FavoriteTermRequest, user: User = Depends(require_auth)):
    """Add a term to user's favorites"""
    if data.term_id not in BIBLICAL_DICTIONARY:
        raise HTTPException(status_code=404, detail="Term not found")
    
    existing = await db.dictionary_favorites.find_one({
        "user_id": user.user_id,
        "term_id": data.term_id
    })
    
    if existing:
        return {"message": "Term already in favorites", "term_id": data.term_id}
    
    await db.dictionary_favorites.insert_one({
        "user_id": user.user_id,
        "term_id": data.term_id,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"message": "Term added to favorites", "term_id": data.term_id}

@api_router.delete("/dictionary/favorites/{term_id}")
async def remove_favorite_term(term_id: str, user: User = Depends(require_auth)):
    """Remove a term from user's favorites"""
    result = await db.dictionary_favorites.delete_one({
        "user_id": user.user_id,
        "term_id": term_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Term removed from favorites", "term_id": term_id}

@api_router.get("/dictionary/favorites/check/{term_id}")
async def check_favorite(term_id: str, user: User = Depends(require_auth)):
    """Check if a term is in user's favorites"""
    exists = await db.dictionary_favorites.find_one({
        "user_id": user.user_id,
        "term_id": term_id
    })
    return {"is_favorite": exists is not None}

# Flashcards for spaced repetition learning
@api_router.get("/dictionary/flashcards")
async def get_flashcards(user: User = Depends(require_auth), lang: str = "it"):
    """Get user's flashcards for study"""
    flashcards_cursor = db.dictionary_flashcards.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("next_review", 1)  # Sort by next review date
    
    flashcards = []
    async for card in flashcards_cursor:
        term_id = card["term_id"]
        if term_id in BIBLICAL_DICTIONARY:
            term = BIBLICAL_DICTIONARY[term_id]
            meaning = term["meaning"]
            description = term["description"]
            
            # Get translated content if available
            if lang != "it":
                if term_id in DICT_TERM_TRANSLATIONS and lang in DICT_TERM_TRANSLATIONS[term_id]:
                    trans = DICT_TERM_TRANSLATIONS[term_id][lang]
                    meaning = trans.get("meaning", term["meaning"])
                    description = trans.get("description", term["description"])
                else:
                    cached = await db.dictionary_translations.find_one({
                        "term_id": term_id, "language": lang
                    }, {"_id": 0})
                    if cached:
                        meaning = cached.get("meaning", meaning)
                        description = cached.get("description", description)
            
            flashcards.append({
                "flashcard_id": card.get("flashcard_id", ""),
                "term_id": term_id,
                "term": term["term"],
                "meaning": meaning,
                "description": description[:200] + "..." if len(description) > 200 else description,
                "origin": term["origin"],
                "note": card.get("note", ""),
                "mastery_level": card.get("mastery_level", 0),
                "last_reviewed": card.get("last_reviewed", "").isoformat() if card.get("last_reviewed") else None,
                "next_review": card.get("next_review", "").isoformat() if card.get("next_review") else None,
                "review_count": card.get("review_count", 0),
                "created_at": card.get("created_at", datetime.now(timezone.utc)).isoformat()
            })
    
    return flashcards

@api_router.get("/dictionary/flashcards/due")
async def get_due_flashcards(user: User = Depends(require_auth), lang: str = "it"):
    """Get flashcards due for review"""
    now = datetime.now(timezone.utc)
    
    due_cursor = db.dictionary_flashcards.find({
        "user_id": user.user_id,
        "$or": [
            {"next_review": {"$lte": now}},
            {"next_review": None}
        ]
    }, {"_id": 0}).sort("next_review", 1).limit(20)
    
    flashcards = []
    async for card in due_cursor:
        term_id = card["term_id"]
        if term_id in BIBLICAL_DICTIONARY:
            term = BIBLICAL_DICTIONARY[term_id]
            meaning = term["meaning"]
            
            if lang != "it":
                if term_id in DICT_TERM_TRANSLATIONS and lang in DICT_TERM_TRANSLATIONS[term_id]:
                    meaning = DICT_TERM_TRANSLATIONS[term_id][lang].get("meaning", meaning)
                else:
                    cached = await db.dictionary_translations.find_one({
                        "term_id": term_id, "language": lang
                    }, {"_id": 0})
                    if cached and cached.get("meaning"):
                        meaning = cached["meaning"]
            
            flashcards.append({
                "flashcard_id": card.get("flashcard_id", ""),
                "term_id": term_id,
                "term": term["term"],
                "meaning": meaning,
                "origin": term["origin"],
                "mastery_level": card.get("mastery_level", 0)
            })
    
    return flashcards

@api_router.post("/dictionary/flashcards")
async def create_flashcard(data: FlashcardCreateRequest, user: User = Depends(require_auth)):
    """Create a flashcard from a dictionary term"""
    if data.term_id not in BIBLICAL_DICTIONARY:
        raise HTTPException(status_code=404, detail="Term not found")
    
    existing = await db.dictionary_flashcards.find_one({
        "user_id": user.user_id,
        "term_id": data.term_id
    })
    
    if existing:
        return {"message": "Flashcard already exists", "flashcard_id": existing.get("flashcard_id", "")}
    
    flashcard_id = f"fc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    await db.dictionary_flashcards.insert_one({
        "flashcard_id": flashcard_id,
        "user_id": user.user_id,
        "term_id": data.term_id,
        "note": data.note or "",
        "mastery_level": 0,
        "review_count": 0,
        "last_reviewed": None,
        "next_review": now,  # Due immediately
        "created_at": now
    })
    
    return {"message": "Flashcard created", "flashcard_id": flashcard_id}

@api_router.put("/dictionary/flashcards/{flashcard_id}/review")
async def review_flashcard(flashcard_id: str, quality: int, user: User = Depends(require_auth)):
    """
    Review a flashcard using spaced repetition algorithm.
    Quality: 0-5 scale (0=complete blackout, 5=perfect recall)
    """
    if quality < 0 or quality > 5:
        raise HTTPException(status_code=400, detail="Quality must be between 0 and 5")
    
    card = await db.dictionary_flashcards.find_one({
        "flashcard_id": flashcard_id,
        "user_id": user.user_id
    }, {"_id": 0})
    
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Simple spaced repetition: increase interval based on quality
    now = datetime.now(timezone.utc)
    current_level = card.get("mastery_level", 0)
    review_count = card.get("review_count", 0) + 1
    
    # Calculate new mastery level and next review date
    if quality >= 3:
        # Good recall - increase mastery
        new_level = min(5, current_level + 1)
        # Interval increases exponentially: 1, 2, 4, 8, 16, 32 days
        days_until_review = 2 ** new_level
    else:
        # Poor recall - decrease mastery
        new_level = max(0, current_level - 1)
        # Review again soon
        days_until_review = 1 if quality == 0 else 2
    
    next_review = now + timedelta(days=days_until_review)
    
    await db.dictionary_flashcards.update_one(
        {"flashcard_id": flashcard_id, "user_id": user.user_id},
        {"$set": {
            "mastery_level": new_level,
            "last_reviewed": now,
            "next_review": next_review,
            "review_count": review_count
        }}
    )
    
    return {
        "message": "Flashcard reviewed",
        "new_mastery_level": new_level,
        "next_review": next_review.isoformat(),
        "days_until_review": days_until_review
    }

@api_router.delete("/dictionary/flashcards/{flashcard_id}")
async def delete_flashcard(flashcard_id: str, user: User = Depends(require_auth)):
    """Delete a flashcard"""
    result = await db.dictionary_flashcards.delete_one({
        "flashcard_id": flashcard_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    return {"message": "Flashcard deleted"}

@api_router.get("/dictionary/flashcards/stats")
async def get_flashcard_stats(user: User = Depends(require_auth)):
    """Get user's flashcard study statistics"""
    total = await db.dictionary_flashcards.count_documents({"user_id": user.user_id})
    
    now = datetime.now(timezone.utc)
    due_count = await db.dictionary_flashcards.count_documents({
        "user_id": user.user_id,
        "$or": [
            {"next_review": {"$lte": now}},
            {"next_review": None}
        ]
    })
    
    # Count by mastery level
    mastery_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    cursor = db.dictionary_flashcards.find(
        {"user_id": user.user_id},
        {"mastery_level": 1, "_id": 0}
    )
    async for card in cursor:
        level = card.get("mastery_level", 0)
        mastery_counts[level] = mastery_counts.get(level, 0) + 1
    
    # Calculate mastered (level 4-5)
    mastered = mastery_counts.get(4, 0) + mastery_counts.get(5, 0)
    
    return {
        "total_flashcards": total,
        "due_for_review": due_count,
        "mastered": mastered,
        "mastery_distribution": mastery_counts
    }

# NOTE: This route MUST be after all specific /dictionary/* routes to avoid path conflicts
@api_router.get("/dictionary/{term_id}")
async def get_dictionary_term(term_id: str, lang: str = "it"):
    """Get full dictionary entry with optional translation (uses AI if needed)"""
    if term_id not in BIBLICAL_DICTIONARY:
        raise HTTPException(status_code=404, detail="Term not found")
    
    term_data = BIBLICAL_DICTIONARY[term_id]
    
    # For Italian, return as-is
    if lang == "it":
        return term_data
    
    # Check if we have pre-translated version
    if term_id in DICT_TERM_TRANSLATIONS and lang in DICT_TERM_TRANSLATIONS[term_id]:
        return translate_dict_term(term_data, term_id, lang)
    
    # Use AI translation for terms without pre-translated versions
    return await ai_translate_dict_term(term_data, term_id, lang)

@api_router.get("/search")
async def global_search(q: str, user: User = Depends(require_auth)):
    """Global search across notes, bookmarks, highlights, users, and content"""
    query_lower = q.lower()
    results = {
        "notes": [],
        "bookmarks": [],
        "highlights": [],
        "users": [],
        "dictionary": [],
        "radios": [],
        "quizzes": []
    }
    
    # Search user's notes
    notes_cursor = db.study_notes.find({
        "user_id": user.user_id,
        "$or": [
            {"content": {"$regex": q, "$options": "i"}},
            {"verse_ref": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10)
    async for note in notes_cursor:
        results["notes"].append({
            "type": "note",
            "id": str(note.get("_id", "")),
            "verse_ref": note.get("verse_ref", ""),
            "content": note.get("content", "")[:100] + "...",
            "created_at": note.get("created_at", "").isoformat() if note.get("created_at") else ""
        })
    
    # Search user's bookmarks
    bookmarks_cursor = db.bookmarks.find({
        "user_id": user.user_id,
        "$or": [
            {"verse_ref": {"$regex": q, "$options": "i"}},
            {"text": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10)
    async for bm in bookmarks_cursor:
        results["bookmarks"].append({
            "type": "bookmark",
            "id": str(bm.get("_id", "")),
            "verse_ref": bm.get("verse_ref", ""),
            "text": bm.get("text", "")[:100] + "..."
        })
    
    # Search user's highlights
    highlights_cursor = db.highlights.find({
        "user_id": user.user_id,
        "$or": [
            {"verse_ref": {"$regex": q, "$options": "i"}},
            {"text": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10)
    async for hl in highlights_cursor:
        results["highlights"].append({
            "type": "highlight",
            "id": str(hl.get("_id", "")),
            "verse_ref": hl.get("verse_ref", ""),
            "text": hl.get("text", "")[:100] + "...",
            "color": hl.get("color", "yellow")
        })
    
    # Search users (friends)
    users_cursor = db.users.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10)
    async for u in users_cursor:
        if u.get("user_id") != user.user_id:  # Exclude self
            results["users"].append({
                "type": "user",
                "id": u.get("user_id", ""),
                "name": u.get("name", ""),
                "email": u.get("email", "")[:3] + "***"  # Privacy
            })
    
    # Search dictionary
    for key, term in BIBLICAL_DICTIONARY.items():
        if (query_lower in term["term"].lower() or 
            query_lower in term["meaning"].lower()):
            results["dictionary"].append({
                "type": "dictionary",
                "id": key,
                "term": term["term"],
                "meaning": term["meaning"][:50] + "..."
            })
            if len(results["dictionary"]) >= 5:
                break
    
    # Search radios
    for radio in EVANGELICAL_RADIOS:
        if (query_lower in radio["name"].lower() or 
            query_lower in radio["country"].lower()):
            results["radios"].append({
                "type": "radio",
                "name": radio["name"],
                "country": radio["country"],
                "url": radio["stream_url"]
            })
            if len(results["radios"]) >= 5:
                break
    
    # Count total results
    total = sum(len(v) for v in results.values())
    
    return {
        "query": q,
        "total_results": total,
        "results": results
    }

class DictionaryStudyRequest(BaseModel):
    term_id: str
    question: str

@api_router.post("/dictionary/ai-study")
async def ai_dictionary_study(data: DictionaryStudyRequest, user: User = Depends(require_auth)):
    """AI-powered study of biblical terms"""
    if data.term_id not in BIBLICAL_DICTIONARY:
        raise HTTPException(status_code=404, detail="Termine non trovato")
    
    term = BIBLICAL_DICTIONARY[data.term_id]
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"dict_study_{user.user_id}_{data.term_id}",
            system_message=f"""Sei un esperto di lingue bibliche (ebraico e greco). 
            Stai spiegando il termine: {term['term']}
            Origine: {term['origin']}
            Significato: {term['meaning']}
            Radice: {term['root']}
            
            Rispondi in italiano in modo chiaro e accessibile."""
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=data.question))
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore AI: {str(e)}")

# ==================== DOMANDE APERTE A TEMA ====================

class OpenQuestionRequest(BaseModel):
    question: str
    topic: Optional[str] = None
    language: str = "it"

@api_router.post("/study/ask")
async def ask_open_question(data: OpenQuestionRequest, user: User = Depends(require_auth)):
    """AI-powered open questions about the Bible"""
    try:
        system_prompts = {
            "it": """Sei un esperto teologo e biblista cristiano evangelico. Rispondi alle domande sulla Bibbia in modo:
- Fedele al testo biblico
- Chiaro e accessibile
- Con riferimenti ai versetti pertinenti
- In italiano

Se la domanda non riguarda la Bibbia o la fede cristiana, gentilmente reindirizza verso temi biblici.""",
            "es": "Eres un teólogo cristiano experto. Responde en español con referencias bíblicas.",
            "en": "You are an expert Christian theologian. Respond in English with biblical references."
        }
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"study_ask_{user.user_id}_{uuid.uuid4().hex[:8]}",
            system_message=system_prompts.get(data.language, system_prompts["it"])
        ).with_model("openai", "gpt-4o")
        
        prompt = data.question
        if data.topic:
            prompt = f"[Argomento: {data.topic}] {data.question}"
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Save to history
        await db.study_questions.insert_one({
            "question_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "question": data.question,
            "topic": data.topic,
            "answer": response,
            "language": data.language,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {str(e)}")

@api_router.get("/study/history")
async def get_study_history(user: User = Depends(require_auth), limit: int = 30):
    """Get user's study question history"""
    history = await db.study_questions.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return history

# ==================== FORUM COLLABORATIVO ====================

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
        "is_approved": True,  # AI mentor can flag for review
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.forum_posts.insert_one(post)
    post.pop("_id", None)
    return post

@api_router.get("/forum/posts")
async def get_forum_posts(
    category: Optional[str] = None,
    sort: str = "recent",  # recent, popular, unanswered
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
    
    # Increment views
    await db.forum_posts.update_one({"post_id": post_id}, {"$inc": {"views": 1}})
    
    # Get replies
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
        # Remove vote
        await db.forum_posts.update_one(
            {"post_id": post_id},
            {"$inc": {"votes": -1}, "$pull": {"voters": user.user_id}}
        )
        return {"voted": False, "votes": post["votes"] - 1}
    else:
        # Add vote
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
        
        # Save AI mentor reply
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

# ==================== MAPPE BIBLICHE ====================

BIBLICAL_MAPS = {
    "palestine": {
        "id": "palestine",
        "name": "Terra Santa",
        "description": "La terra promessa ad Abramo e conquistata da Giosuè",
        "center": {"lat": 31.7683, "lng": 35.2137},
        "zoom": 8,
        "locations": [
            {"name": "Gerusalemme", "lat": 31.7683, "lng": 35.2137, "type": "city", "description": "La città santa, capitale del regno di Davide e luogo della crocifissione di Gesù"},
            {"name": "Betlemme", "lat": 31.7054, "lng": 35.2024, "type": "city", "description": "Città natale di Gesù e del re Davide"},
            {"name": "Nazaret", "lat": 32.6996, "lng": 35.3035, "type": "city", "description": "Città dove Gesù crebbe"},
            {"name": "Mar di Galilea", "lat": 32.8231, "lng": 35.5831, "type": "water", "description": "Lago dove Gesù chiamò i primi discepoli e camminò sulle acque"},
            {"name": "Gerico", "lat": 31.8711, "lng": 35.4442, "type": "city", "description": "Prima città conquistata da Giosuè"},
            {"name": "Mar Morto", "lat": 31.5, "lng": 35.5, "type": "water", "description": "Il punto più basso della terra, vicino a Sodoma e Gomorra"},
            {"name": "Monte degli Ulivi", "lat": 31.778, "lng": 35.245, "type": "mountain", "description": "Luogo dell'ascensione di Gesù"},
            {"name": "Giordano", "lat": 32.0, "lng": 35.55, "type": "river", "description": "Fiume dove Gesù fu battezzato"},
        ]
    },
    "exodus": {
        "id": "exodus",
        "name": "Viaggio dell'Esodo",
        "description": "Il percorso degli Israeliti dall'Egitto alla Terra Promessa",
        "center": {"lat": 29.5, "lng": 33.0},
        "zoom": 6,
        "locations": [
            {"name": "Ramses (Egitto)", "lat": 30.79, "lng": 31.83, "type": "city", "description": "Punto di partenza dell'Esodo"},
            {"name": "Mar Rosso", "lat": 28.0, "lng": 34.0, "type": "water", "description": "Mare diviso da Mosè"},
            {"name": "Monte Sinai", "lat": 28.5392, "lng": 33.9756, "type": "mountain", "description": "Dove Mosè ricevette i Dieci Comandamenti"},
            {"name": "Cades-Barnea", "lat": 30.6, "lng": 34.4, "type": "city", "description": "Luogo dove gli Israeliti vagarono per 40 anni"},
            {"name": "Monte Nebo", "lat": 31.767, "lng": 35.725, "type": "mountain", "description": "Dove Mosè vide la Terra Promessa"},
        ]
    },
    "paul_journeys": {
        "id": "paul_journeys",
        "name": "Viaggi Missionari di Paolo",
        "description": "I tre viaggi missionari dell'apostolo Paolo",
        "center": {"lat": 38.0, "lng": 30.0},
        "zoom": 5,
        "locations": [
            {"name": "Antiochia", "lat": 36.2, "lng": 36.16, "type": "city", "description": "Base dei viaggi missionari di Paolo"},
            {"name": "Tarso", "lat": 36.9167, "lng": 34.8833, "type": "city", "description": "Città natale di Paolo"},
            {"name": "Efeso", "lat": 37.9394, "lng": 27.3417, "type": "city", "description": "Centro del ministero di Paolo in Asia"},
            {"name": "Corinto", "lat": 37.9061, "lng": 22.8783, "type": "city", "description": "Dove Paolo fondò una chiesa importante"},
            {"name": "Atene", "lat": 37.9838, "lng": 23.7275, "type": "city", "description": "Dove Paolo predicò all'Areopago"},
            {"name": "Roma", "lat": 41.9028, "lng": 12.4964, "type": "city", "description": "Destinazione finale di Paolo"},
            {"name": "Filippi", "lat": 41.0128, "lng": 24.2875, "type": "city", "description": "Prima chiesa in Europa"},
        ]
    },
    "jesus_ministry": {
        "id": "jesus_ministry",
        "name": "Ministero di Gesù",
        "description": "I luoghi principali del ministero terreno di Gesù",
        "center": {"lat": 32.5, "lng": 35.3},
        "zoom": 9,
        "locations": [
            {"name": "Cafarnao", "lat": 32.8814, "lng": 35.5753, "type": "city", "description": "Centro del ministero di Gesù in Galilea"},
            {"name": "Cana", "lat": 32.8267, "lng": 35.3433, "type": "city", "description": "Primo miracolo: acqua in vino"},
            {"name": "Monte delle Beatitudini", "lat": 32.8811, "lng": 35.5553, "type": "mountain", "description": "Sermone sul Monte"},
            {"name": "Tabga", "lat": 32.8739, "lng": 35.5467, "type": "city", "description": "Moltiplicazione dei pani e pesci"},
            {"name": "Cesarea di Filippo", "lat": 33.2489, "lng": 35.6931, "type": "city", "description": "Confessione di Pietro"},
            {"name": "Getsemani", "lat": 31.7794, "lng": 35.2397, "type": "site", "description": "Dove Gesù pregò prima dell'arresto"},
            {"name": "Golgota", "lat": 31.7789, "lng": 35.2297, "type": "site", "description": "Luogo della crocifissione"},
        ]
    }
}

@api_router.get("/maps")
async def get_available_maps():
    """Get list of available biblical maps"""
    return [
        {
            "id": map_data["id"],
            "name": map_data["name"],
            "description": map_data["description"],
            "locations_count": len(map_data["locations"])
        }
        for map_data in BIBLICAL_MAPS.values()
    ]

@api_router.get("/maps/{map_id}")
async def get_map_data(map_id: str):
    """Get full map data with locations"""
    if map_id not in BIBLICAL_MAPS:
        raise HTTPException(status_code=404, detail="Mappa non trovata")
    return BIBLICAL_MAPS[map_id]

@api_router.get("/maps/{map_id}/location/{location_name}")
async def get_location_details(map_id: str, location_name: str):
    """Get AI-generated details about a biblical location"""
    if map_id not in BIBLICAL_MAPS:
        raise HTTPException(status_code=404, detail="Mappa non trovata")
    
    location = None
    for loc in BIBLICAL_MAPS[map_id]["locations"]:
        if loc["name"].lower() == location_name.lower():
            location = loc
            break
    
    if not location:
        raise HTTPException(status_code=404, detail="Luogo non trovato")
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"map_location_{map_id}_{location_name}",
            system_message="Sei una guida biblica esperta. Fornisci informazioni storiche e bibliche sui luoghi."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(
            text=f"Parlami del luogo biblico '{location['name']}' in modo breve ma informativo. Includi eventi biblici importanti e versetti chiave."
        ))
        
        return {
            **location,
            "detailed_description": response
        }
    except Exception as e:
        return {
            **location,
            "detailed_description": location["description"]
        }

# ==================== EVENTI LIVE ====================

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
        "created_at": datetime.now(timezone.utc)
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
        # By default, show upcoming and live events
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
            {"$push": {"participants": user.user_id}}
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
        {"$set": {"status": "live", "started_at": datetime.now(timezone.utc)}}
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
        {"$set": {"status": "ended", "ended_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "status": "ended"}

# ==================== FAQ E AIUTO ====================

FAQ_DATA = [
    {
        "id": "faq1",
        "category": "generale",
        "question": "Cos'è Amen!?",
        "answer": "Amen! è un'app cristiana evangelica per la crescita spirituale. Include lettura della Bibbia (Nuova Diodati e Reina Valera), assistente AI spirituale, diario personale, quiz biblici, dizionario dei termini antichi, e una comunità di credenti."
    },
    {
        "id": "faq2",
        "category": "bibbia",
        "question": "Quali traduzioni bibliche sono disponibili?",
        "answer": "L'app include la Nuova Diodati (italiano) e Reina Valera 1960 (spagnolo). Altre traduzioni saranno aggiunte in futuro."
    },
    {
        "id": "faq3",
        "category": "account",
        "question": "Come posso cancellare il mio account?",
        "answer": "Puoi richiedere la cancellazione del tuo account contattandoci a andrehangar@live.it. I tuoi dati saranno rimossi entro 30 giorni."
    },
    {
        "id": "faq4",
        "category": "donazioni",
        "question": "Come posso sostenere l'app?",
        "answer": "Puoi fare una donazione tramite PayPal (andrehangar@live.it) o bonifico bancario. Le donazioni aiutano a mantenere l'app gratuita e ad aggiungere nuove funzionalità."
    },
    {
        "id": "faq5",
        "category": "community",
        "question": "Come funziona il forum?",
        "answer": "Il forum permette di discutere, condividere testimonianze, fare domande bibliche e richiedere preghiere. Un mentore AI modera le discussioni per mantenere un ambiente rispettoso."
    },
    {
        "id": "faq6",
        "category": "studio",
        "question": "Cosa sono i quiz biblici?",
        "answer": "I quiz biblici sono test interattivi per verificare e approfondire la tua conoscenza della Bibbia. Ogni risposta include spiegazioni e riferimenti ai versetti."
    },
    {
        "id": "faq7",
        "category": "studio",
        "question": "Come funziona il dizionario biblico?",
        "answer": "Il dizionario spiega i termini originali ebraici e greci con le loro radici semantiche, pronuncia, significato e versetti di riferimento."
    },
    {
        "id": "faq8",
        "category": "eventi",
        "question": "Cosa sono gli eventi live?",
        "answer": "Gli eventi live permettono di partecipare a letture bibliche sincronizzate, momenti di lode e preghiera comunitaria con altri utenti dell'app."
    }
]

@api_router.get("/faq")
async def get_faq(category: Optional[str] = None):
    """Get FAQ items"""
    if category:
        return [f for f in FAQ_DATA if f["category"] == category]
    return FAQ_DATA

@api_router.get("/faq/categories")
async def get_faq_categories():
    """Get FAQ categories"""
    categories = set(f["category"] for f in FAQ_DATA)
    category_names = {
        "generale": "Generale",
        "bibbia": "Bibbia",
        "account": "Account",
        "donazioni": "Donazioni",
        "community": "Community",
        "studio": "Studio",
        "eventi": "Eventi"
    }
    return [{"id": c, "name": category_names.get(c, c.title())} for c in categories]

@api_router.post("/support/contact")
async def contact_support(request: Request, user: User = Depends(require_auth)):
    """Send support message"""
    body = await request.json()
    message = body.get("message", "")
    
    support_ticket = {
        "ticket_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_email": user.email,
        "user_name": user.name,
        "message": message,
        "status": "open",
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.support_tickets.insert_one(support_ticket)
    
    return {"success": True, "message": "Messaggio inviato! Ti risponderemo presto.", "ticket_id": support_ticket["ticket_id"]}

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Amen! API", "version": "2.0.0", "features": ["multilang", "community", "translation"]}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
