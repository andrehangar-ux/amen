from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    preferred_bible: str = "nuova_diodati"
    language: str = "it"
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

class LoginRequest(BaseModel):
    email: str
    password: str

class JournalEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    mood: str
    ai_insight: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JournalCreate(BaseModel):
    content: str
    mood: str

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
    role: str  # user or assistant
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str
    mood: Optional[str] = None

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

class Progress(BaseModel):
    user_id: str
    reading_streak: int = 0
    total_chapters_read: int = 0
    total_journal_entries: int = 0
    last_reading_date: Optional[datetime] = None
    achievements: List[str] = []

class DonationRequest(BaseModel):
    amount: float
    method: str  # paypal, bonifico, mock
    message: Optional[str] = None

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None
    
    # Check expiry with timezone awareness
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

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/google-callback")
async def google_callback(request: Request, response: Response):
    """Exchange session_id for user data and create session"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id mancante")
    
    # Call Emergent Auth API
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Sessione non valida")
        
        user_data = auth_response.json()
    
    session_data = SessionDataResponse(**user_data)
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": session_data.email}, {"_id": 0})
    
    if not existing_user:
        # Create new user
        new_user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": new_user_id,
            "email": session_data.email,
            "name": session_data.name,
            "picture": session_data.picture,
            "preferred_bible": "nuova_diodati",
            "language": "it",
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(new_user)
        user_id = new_user_id
    else:
        user_id = existing_user["user_id"]
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_data.session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Set cookie
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
    """Register with email/password"""
    # Check if user exists
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Create user
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
        "language": "it",
        "created_at": datetime.now(timezone.utc)
    }
    await db.users.insert_one(user)
    
    # Create session
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
    """Login with email/password"""
    import hashlib
    password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    
    user = await db.users.find_one(
        {"email": data.email, "password_hash": password_hash}, 
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    # Create session
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
    """Get current user"""
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Disconnesso con successo"}

# ==================== BIBLE ENDPOINTS ====================

# Bible data - Italian Nuova Diodati structure
BIBLE_BOOKS = {
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
        {"name": "1 Cronache", "chapters": 29, "abbrev": "1Cron"},
        {"name": "2 Cronache", "chapters": 36, "abbrev": "2Cron"},
        {"name": "Esdra", "chapters": 10, "abbrev": "Esd"},
        {"name": "Neemia", "chapters": 13, "abbrev": "Nee"},
        {"name": "Ester", "chapters": 10, "abbrev": "Est"},
        {"name": "Giobbe", "chapters": 42, "abbrev": "Giob"},
        {"name": "Salmi", "chapters": 150, "abbrev": "Sal"},
        {"name": "Proverbi", "chapters": 31, "abbrev": "Prov"},
        {"name": "Ecclesiaste", "chapters": 12, "abbrev": "Eccl"},
        {"name": "Cantico dei Cantici", "chapters": 8, "abbrev": "Cant"},
        {"name": "Isaia", "chapters": 66, "abbrev": "Is"},
        {"name": "Geremia", "chapters": 52, "abbrev": "Ger"},
        {"name": "Lamentazioni", "chapters": 5, "abbrev": "Lam"},
        {"name": "Ezechiele", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniele", "chapters": 12, "abbrev": "Dan"},
        {"name": "Osea", "chapters": 14, "abbrev": "Os"},
        {"name": "Gioele", "chapters": 3, "abbrev": "Gioe"},
        {"name": "Amos", "chapters": 9, "abbrev": "Am"},
        {"name": "Abdia", "chapters": 1, "abbrev": "Abd"},
        {"name": "Giona", "chapters": 4, "abbrev": "Gion"},
        {"name": "Michea", "chapters": 7, "abbrev": "Mic"},
        {"name": "Naum", "chapters": 3, "abbrev": "Nau"},
        {"name": "Abacuc", "chapters": 3, "abbrev": "Abac"},
        {"name": "Sofonia", "chapters": 3, "abbrev": "Sof"},
        {"name": "Aggeo", "chapters": 2, "abbrev": "Agg"},
        {"name": "Zaccaria", "chapters": 14, "abbrev": "Zacc"},
        {"name": "Malachia", "chapters": 4, "abbrev": "Mal"},
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
        {"name": "1 Tessalonicesi", "chapters": 5, "abbrev": "1Tess"},
        {"name": "2 Tessalonicesi", "chapters": 3, "abbrev": "2Tess"},
        {"name": "1 Timoteo", "chapters": 6, "abbrev": "1Tim"},
        {"name": "2 Timoteo", "chapters": 4, "abbrev": "2Tim"},
        {"name": "Tito", "chapters": 3, "abbrev": "Tito"},
        {"name": "Filemone", "chapters": 1, "abbrev": "Filem"},
        {"name": "Ebrei", "chapters": 13, "abbrev": "Ebr"},
        {"name": "Giacomo", "chapters": 5, "abbrev": "Giac"},
        {"name": "1 Pietro", "chapters": 5, "abbrev": "1Pt"},
        {"name": "2 Pietro", "chapters": 3, "abbrev": "2Pt"},
        {"name": "1 Giovanni", "chapters": 5, "abbrev": "1Giov"},
        {"name": "2 Giovanni", "chapters": 1, "abbrev": "2Giov"},
        {"name": "3 Giovanni", "chapters": 1, "abbrev": "3Giov"},
        {"name": "Giuda", "chapters": 1, "abbrev": "Giuda"},
        {"name": "Apocalisse", "chapters": 22, "abbrev": "Apoc"},
    ]
}

# Sample verses for demonstration (in real app, would use Bible API)
SAMPLE_VERSES = {
    "Giovanni:3": [
        {"verse": 1, "text": "Or c'era tra i farisei un uomo di nome Nicodemo, un capo dei Giudei."},
        {"verse": 2, "text": "Egli venne a Gesù di notte e gli disse: «Maestro, noi sappiamo che tu sei un dottore venuto da Dio, perché nessuno può fare i segni che tu fai, se Dio non è con lui»."},
        {"verse": 3, "text": "Gesù gli rispose e disse: «In verità, in verità ti dico che se uno non è nato di nuovo, non può vedere il regno di Dio»."},
        {"verse": 16, "text": "Poiché Dio ha tanto amato il mondo, che ha dato il suo unigenito Figlio, affinché chiunque crede in lui non perisca, ma abbia vita eterna."},
        {"verse": 17, "text": "Dio infatti non ha mandato il proprio Figlio nel mondo per condannare il mondo, ma affinché il mondo sia salvato per mezzo di lui."},
    ],
    "Salmi:23": [
        {"verse": 1, "text": "L'Eterno è il mio pastore, nulla mi mancherà."},
        {"verse": 2, "text": "Egli mi fa riposare in verdi pascoli, mi guida lungo le acque tranquille."},
        {"verse": 3, "text": "Egli ristora la mia anima, mi guida per sentieri di giustizia per amore del suo nome."},
        {"verse": 4, "text": "Anche se camminassi nella valle dell'ombra della morte, non temerei alcun male, perché tu sei con me; il tuo bastone e la tua verga mi danno conforto."},
        {"verse": 5, "text": "Tu apparecchi davanti a me una mensa al cospetto dei miei nemici; ungi il mio capo con olio; la mia coppa trabocca."},
        {"verse": 6, "text": "Certo, bontà e benignità mi accompagneranno tutti i giorni della mia vita; e io abiterò nella casa dell'Eterno per lunghi giorni."},
    ],
    "Romani:8": [
        {"verse": 28, "text": "Or noi sappiamo che tutte le cose cooperano al bene di quelli che amano Dio, i quali sono chiamati secondo il suo proponimento."},
        {"verse": 31, "text": "Che diremo dunque di queste cose? Se Dio è per noi, chi sarà contro di noi?"},
        {"verse": 37, "text": "Ma in tutte queste cose noi siamo più che vincitori in virtù di colui che ci ha amati."},
        {"verse": 38, "text": "Infatti io sono persuaso che né morte né vita, né angeli né principati, né potenze, né cose presenti né cose future,"},
        {"verse": 39, "text": "né altezze né profondità, né alcun'altra creatura potrà separarci dall'amore di Dio che è in Cristo Gesù, nostro Signore."},
    ],
    "Filippesi:4": [
        {"verse": 4, "text": "Rallegratevi sempre nel Signore; lo ripeto: rallegratevi."},
        {"verse": 6, "text": "Non angustiatevi di nulla, ma in ogni cosa fate conoscere le vostre richieste a Dio in preghiere e suppliche, accompagnate da ringraziamenti."},
        {"verse": 7, "text": "E la pace di Dio, che sopravanza ogni intelligenza, custodirà i vostri cuori e i vostri pensieri in Cristo Gesù."},
        {"verse": 13, "text": "Io posso ogni cosa in Cristo che mi fortifica."},
    ],
    "Matteo:11": [
        {"verse": 28, "text": "Venite a me, voi tutti che siete travagliati e aggravati, e io vi darò riposo."},
        {"verse": 29, "text": "Prendete su di voi il mio giogo e imparate da me, perché io sono mansueto e umile di cuore; e voi troverete riposo per le anime vostre."},
        {"verse": 30, "text": "Perché il mio giogo è dolce e il mio carico è leggero»."},
    ],
    "Isaia:41": [
        {"verse": 10, "text": "Non temere, perché io sono con te; non smarrirti, perché io sono il tuo DIO; io ti fortifico, io ti aiuto, io ti sostengo con la destra della mia giustizia."},
    ],
    "Geremia:29": [
        {"verse": 11, "text": "Poiché io conosco i pensieri che ho per voi», dice l'Eterno, «pensieri di pace e non di male, per darvi un futuro e una speranza."},
    ],
    "Proverbi:3": [
        {"verse": 5, "text": "Confida nell'Eterno con tutto il cuore e non appoggiarti sul tuo intendimento."},
        {"verse": 6, "text": "Riconoscilo in tutte le tue vie, ed egli raddrizzerà i tuoi sentieri."},
    ]
}

# Daily verses based on mood
MOOD_VERSES = {
    "felice": [
        {"ref": "Salmi 118:24", "text": "Questo è il giorno che l'Eterno ha fatto; rallegriamoci e gioisciamo in esso."},
        {"ref": "Filippesi 4:4", "text": "Rallegratevi sempre nel Signore; lo ripeto: rallegratevi."},
    ],
    "triste": [
        {"ref": "Salmi 34:18", "text": "L'Eterno è vicino a quelli che hanno il cuore rotto e salva quelli che sono affranti nello spirito."},
        {"ref": "Matteo 5:4", "text": "Beati coloro che fanno cordoglio, perché saranno consolati."},
    ],
    "ansioso": [
        {"ref": "Filippesi 4:6-7", "text": "Non angustiatevi di nulla, ma in ogni cosa fate conoscere le vostre richieste a Dio... E la pace di Dio custodirà i vostri cuori."},
        {"ref": "1 Pietro 5:7", "text": "Gettando su di lui ogni vostra ansietà, perché egli ha cura di voi."},
    ],
    "arrabbiato": [
        {"ref": "Efesini 4:26", "text": "Adiratevi e non peccate; il sole non tramonti sopra la vostra ira."},
        {"ref": "Proverbi 15:1", "text": "Una risposta dolce calma il furore, ma una parola dura eccita l'ira."},
    ],
    "grato": [
        {"ref": "1 Tessalonicesi 5:18", "text": "In ogni cosa rendete grazie, perché questa è la volontà di Dio in Cristo Gesù verso di voi."},
        {"ref": "Salmi 100:4", "text": "Entrate nelle sue porte con ringraziamento e nei suoi cortili con lode; celebratelo, benedite il suo nome."},
    ],
    "confuso": [
        {"ref": "Proverbi 3:5-6", "text": "Confida nell'Eterno con tutto il cuore e non appoggiarti sul tuo intendimento. Riconoscilo in tutte le tue vie, ed egli raddrizzerà i tuoi sentieri."},
        {"ref": "Giacomo 1:5", "text": "Ma se qualcuno di voi manca di sapienza, la chieda a Dio... e gli sarà data."},
    ],
    "speranzoso": [
        {"ref": "Geremia 29:11", "text": "Poiché io conosco i pensieri che ho per voi, pensieri di pace e non di male, per darvi un futuro e una speranza."},
        {"ref": "Romani 15:13", "text": "Or il Dio della speranza vi riempia di ogni gioia e pace nel credere."},
    ],
    "stanco": [
        {"ref": "Matteo 11:28", "text": "Venite a me, voi tutti che siete travagliati e aggravati, e io vi darò riposo."},
        {"ref": "Isaia 40:31", "text": "Ma quelli che sperano nell'Eterno acquistano nuove forze, si alzano a volo come aquile."},
    ],
}

@api_router.get("/bible/books")
async def get_bible_books(lang: str = "it"):
    """Get list of Bible books"""
    return BIBLE_BOOKS.get(lang, BIBLE_BOOKS["it"])

@api_router.get("/bible/chapter/{book}/{chapter}")
async def get_chapter(book: str, chapter: int):
    """Get verses for a chapter"""
    key = f"{book}:{chapter}"
    if key in SAMPLE_VERSES:
        return {"book": book, "chapter": chapter, "verses": SAMPLE_VERSES[key]}
    
    # Generate sample verses for demo
    verses = []
    for i in range(1, min(20, chapter * 2)):
        verses.append({
            "verse": i,
            "text": f"Versetto {i} di {book} capitolo {chapter}. (Contenuto di esempio)"
        })
    return {"book": book, "chapter": chapter, "verses": verses}

@api_router.get("/bible/daily-verse")
async def get_daily_verse():
    """Get daily verse"""
    import random
    all_verses = []
    for ref, verses in SAMPLE_VERSES.items():
        book, chap = ref.split(":")
        for v in verses:
            all_verses.append({
                "reference": f"{book} {chap}:{v['verse']}",
                "text": v["text"]
            })
    
    # Use date as seed for consistency throughout the day
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    random.seed(int(today))
    verse = random.choice(all_verses)
    return verse

# ==================== AI ASSISTANT ENDPOINTS ====================

@api_router.post("/ai/chat")
async def ai_chat(data: ChatRequest, user: User = Depends(require_auth)):
    """Chat with AI spiritual assistant"""
    try:
        session_id = f"chat_{user.user_id}"
        
        system_message = """Sei un assistente spirituale cristiano di nome "Cibo Spirituale". 
        Rispondi in italiano con compassione, saggezza biblica e incoraggiamento.
        Cita versetti biblici quando appropriato.
        Offri guida spirituale pratica basata sulla Scrittura.
        Sii empatico e comprensivo verso le emozioni dell'utente.
        Non giudicare mai, ma guida gentilmente verso la verità biblica."""
        
        if data.mood:
            system_message += f"\n\nL'utente si sente attualmente: {data.mood}. Tieni conto del suo stato emotivo."
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=data.message)
        response = await chat.send_message(user_message)
        
        # Save chat history
        await db.chat_history.insert_one({
            "message_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "role": "user",
            "content": data.message,
            "created_at": datetime.now(timezone.utc)
        })
        
        await db.chat_history.insert_one({
            "message_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "role": "assistant",
            "content": response,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {"response": response}
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore AI: {str(e)}")

@api_router.get("/ai/chat-history")
async def get_chat_history(user: User = Depends(require_auth), limit: int = 50):
    """Get chat history"""
    messages = await db.chat_history.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return list(reversed(messages))

@api_router.delete("/ai/chat-history")
async def clear_chat_history(user: User = Depends(require_auth)):
    """Clear chat history"""
    await db.chat_history.delete_many({"user_id": user.user_id})
    return {"message": "Cronologia cancellata"}

@api_router.post("/ai/mood-checkin")
async def mood_checkin(data: MoodRequest, user: User = Depends(require_auth)):
    """Get AI-generated reflection based on mood"""
    try:
        import random
        
        mood = data.mood.lower()
        mood_data = MOOD_VERSES.get(mood, MOOD_VERSES["speranzoso"])
        verse = random.choice(mood_data)
        
        # Generate personalized reflection with AI
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mood_{user.user_id}_{datetime.now().strftime('%Y%m%d')}",
            system_message="Sei un consolatore spirituale cristiano. Genera una breve riflessione (2-3 frasi) basata sul versetto e sullo stato emotivo dell'utente. Sii incoraggiante e pieno di speranza. Rispondi in italiano."
        ).with_model("openai", "gpt-4o")
        
        prompt = f"L'utente si sente {mood}. Il versetto del giorno è: {verse['ref']} - \"{verse['text']}\". Genera una breve riflessione spirituale personalizzata."
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Save mood checkin
        checkin = {
            "checkin_id": str(uuid.uuid4()),
            "user_id": user.user_id,
            "mood": mood,
            "verse_reference": verse["ref"],
            "verse_text": verse["text"],
            "reflection": response,
            "created_at": datetime.now(timezone.utc)
        }
        await db.mood_checkins.insert_one(checkin)
        
        return {
            "mood": mood,
            "verse": verse,
            "reflection": response
        }
    except Exception as e:
        logger.error(f"Mood checkin error: {e}")
        # Fallback without AI
        import random
        mood_data = MOOD_VERSES.get(data.mood.lower(), MOOD_VERSES["speranzoso"])
        verse = random.choice(mood_data)
        return {
            "mood": data.mood,
            "verse": verse,
            "reflection": "Che Dio ti benedica e ti dia pace oggi."
        }

# ==================== JOURNAL ENDPOINTS ====================

@api_router.post("/journal")
async def create_journal_entry(data: JournalCreate, user: User = Depends(require_auth)):
    """Create journal entry with optional AI insight"""
    try:
        # Generate AI insight
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"journal_{user.user_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
            system_message="Sei un consigliere spirituale. Basandoti sul diario dell'utente, offri una breve riflessione spirituale (1-2 frasi) con un versetto pertinente. Rispondi in italiano."
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
        "ai_insight": ai_insight,
        "created_at": datetime.now(timezone.utc)
    }
    await db.journal_entries.insert_one(entry)
    
    # Update progress
    await db.progress.update_one(
        {"user_id": user.user_id},
        {"$inc": {"total_journal_entries": 1}},
        upsert=True
    )
    
    entry.pop("_id", None)
    return entry

@api_router.get("/journal")
async def get_journal_entries(user: User = Depends(require_auth), limit: int = 50):
    """Get journal entries"""
    entries = await db.journal_entries.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return entries

@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str, user: User = Depends(require_auth)):
    """Delete journal entry"""
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
    """Create bookmark"""
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
    """Get bookmarks"""
    bookmarks = await db.bookmarks.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return bookmarks

@api_router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, user: User = Depends(require_auth)):
    """Delete bookmark"""
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
    """Get user progress"""
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
    """Update reading progress"""
    today = datetime.now(timezone.utc).date()
    progress = await db.progress.find_one({"user_id": user.user_id}, {"_id": 0})
    
    if progress:
        last_date = progress.get("last_reading_date")
        if last_date:
            if isinstance(last_date, datetime):
                last_date = last_date.date()
            
            if last_date == today:
                # Already read today
                return progress
            elif (today - last_date).days == 1:
                # Continue streak
                await db.progress.update_one(
                    {"user_id": user.user_id},
                    {
                        "$inc": {"reading_streak": 1, "total_chapters_read": 1},
                        "$set": {"last_reading_date": datetime.now(timezone.utc)}
                    }
                )
            else:
                # Reset streak
                await db.progress.update_one(
                    {"user_id": user.user_id},
                    {
                        "$set": {"reading_streak": 1, "last_reading_date": datetime.now(timezone.utc)},
                        "$inc": {"total_chapters_read": 1}
                    }
                )
        else:
            # First reading
            await db.progress.update_one(
                {"user_id": user.user_id},
                {
                    "$set": {"reading_streak": 1, "last_reading_date": datetime.now(timezone.utc)},
                    "$inc": {"total_chapters_read": 1}
                }
            )
    else:
        # Create new progress
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
    """Create donation (MOCK)"""
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
    """Get user donations"""
    donations = await db.donations.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return donations

# ==================== RADIO ENDPOINTS ====================

EVANGELICAL_RADIOS = [
    {"name": "Radio Evangelo", "url": "https://www.radioevangeloroma.it/", "country": "Italia", "language": "Italiano"},
    {"name": "Radio Luce", "url": "https://www.radioluce.it/", "country": "Italia", "language": "Italiano"},
    {"name": "Onda Gospel", "url": "https://www.ondagospel.it/", "country": "Italia", "language": "Italiano"},
    {"name": "BBN Radio", "url": "https://bbnradio.org/", "country": "USA", "language": "English"},
    {"name": "Radio Cristiana", "url": "https://www.radiocristiana.com/", "country": "Spagna", "language": "Español"},
]

@api_router.get("/radios")
async def get_radios():
    """Get evangelical radio stations"""
    return EVANGELICAL_RADIOS

# ==================== USER SETTINGS ====================

@api_router.put("/users/settings")
async def update_settings(request: Request, user: User = Depends(require_auth)):
    """Update user settings"""
    body = await request.json()
    allowed_fields = ["preferred_bible", "language", "name", "picture"]
    update_data = {k: v for k, v in body.items() if k in allowed_fields}
    
    if update_data:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return updated_user

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Cibo Spirituale API", "version": "1.0.0"}

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
