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
app = FastAPI(title="Cibo Spirituale API")

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

@api_router.get("/bible/chapter/{book}/{chapter}")
async def get_chapter(book: str, chapter: int, lang: str = "it"):
    """Get verses for a chapter in specified language"""
    verses_dict = SAMPLE_VERSES_MULTILANG.get(lang, SAMPLE_VERSES_MULTILANG["it"])
    key = f"{book}:{chapter}"
    
    if key in verses_dict:
        return {"book": book, "chapter": chapter, "verses": verses_dict[key], "language": lang}
    
    # Generate sample verses
    verses = []
    for i in range(1, min(20, chapter * 2)):
        verses.append({
            "verse": i,
            "text": f"Versetto {i} di {book} capitolo {chapter}. (Contenuto di esempio)"
        })
    return {"book": book, "chapter": chapter, "verses": verses, "language": lang}

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

@api_router.post("/community/messages")
async def create_community_message(data: CommunityMessageCreate, user: User = Depends(require_auth)):
    """Create a community message"""
    message = {
        "message_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "user_country": user.country,
        "content": data.content,
        "original_language": data.language,
        "translations": {},
        "message_type": data.message_type,
        "likes": 0,
        "created_at": datetime.now(timezone.utc)
    }
    await db.community_messages.insert_one(message)
    message.pop("_id", None)
    return message

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
        progress = {
            "user_id": user.user_id,
            "reading_streak": 0,
            "total_chapters_read": 0,
            "total_journal_entries": 0,
            "last_reading_date": None,
            "achievements": []
        }
        await db.progress.insert_one(progress)
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

# ==================== DONATION ENDPOINTS ====================

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
            "iban": "IT00X0000000000000000000000",
            "intestatario": "Cibo Spirituale Ministry",
            "causale": f"Donazione - {donation['donation_id'][:8]}"
        }
    elif data.method == "paypal":
        donation["paypal_link"] = "https://paypal.me/cibospirituale"
    
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
    {"name": "Radio Evangelo", "url": "https://www.radioevangeloroma.it/", "country": "Italia", "language": "it"},
    {"name": "Radio Luce", "url": "https://www.radioluce.it/", "country": "Italia", "language": "it"},
    {"name": "BBN Radio", "url": "https://bbnradio.org/", "country": "USA", "language": "en"},
    {"name": "Radio Cristiana", "url": "https://www.radiocristiana.com/", "country": "España", "language": "es"},
    {"name": "Rádio Trans Mundial", "url": "https://www.transmundial.com.br/", "country": "Brasil", "language": "pt"},
    {"name": "Radio Vie", "url": "https://www.radiovie.com/", "country": "France", "language": "fr"},
]

@api_router.get("/radios")
async def get_radios(lang: str = None):
    if lang:
        return [r for r in EVANGELICAL_RADIOS if r["language"] == lang]
    return EVANGELICAL_RADIOS

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

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Cibo Spirituale API", "version": "2.0.0", "features": ["multilang", "community", "translation"]}

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
