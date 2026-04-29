"""
Core infrastructure: FastAPI app, MongoDB client, environment variables,
logger, supported languages, safety messages, content moderation lists.

This module must NOT import from models.py, dependencies.py, or server.py
to avoid circular dependencies.
"""
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Resend Email
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

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

# ==================== SAFETY MESSAGES (multi-language for minors) ====================
SAFETY_MESSAGES = {
    "it": {
        "title": "Promemoria Sicurezza Online",
        "message": "Ricorda: non condividere mai informazioni personali come indirizzo, scuola o numero di telefono con persone che non conosci. Se qualcuno ti fa sentire a disagio, parlane con un adulto di fiducia.",
        "confirm": "Ho capito"
    },
    "en": {
        "title": "Online Safety Reminder",
        "message": "Remember: never share personal information like address, school, or phone number with people you don't know. If someone makes you feel uncomfortable, talk to a trusted adult.",
        "confirm": "I understand"
    },
    "es": {
        "title": "Recordatorio de Seguridad en Línea",
        "message": "Recuerda: nunca compartas información personal como dirección, escuela o número de teléfono con personas que no conoces. Si alguien te hace sentir incómodo, habla con un adulto de confianza.",
        "confirm": "Entendido"
    },
    "de": {
        "title": "Online-Sicherheitserinnerung",
        "message": "Denk daran: Teile niemals persönliche Informationen wie Adresse, Schule oder Telefonnummer mit Personen, die du nicht kennst. Wenn dich jemand unwohl fühlen lässt, sprich mit einem vertrauenswürdigen Erwachsenen.",
        "confirm": "Verstanden"
    },
    "fr": {
        "title": "Rappel de Sécurité en Ligne",
        "message": "N'oublie pas : ne partage jamais d'informations personnelles comme ton adresse, ton école ou ton numéro de téléphone avec des personnes que tu ne connais pas. Si quelqu'un te met mal à l'aise, parle à un adulte de confiance.",
        "confirm": "J'ai compris"
    },
    "pt": {
        "title": "Lembrete de Segurança Online",
        "message": "Lembre-se: nunca compartilhe informações pessoais como endereço, escola ou número de telefone com pessoas que você não conhece. Se alguém fizer você se sentir desconfortável, fale com um adulto de confiança.",
        "confirm": "Entendi"
    }
}

# ==================== CONTENT MODERATION LISTS ====================
BAD_WORDS = {
    "it": ["cazzo", "minchia", "stronzo", "merda", "vaffanculo", "puttana", "coglione", "idiota", "deficiente"],
    "es": ["mierda", "puta", "joder", "coño", "cabrón", "pendejo", "idiota"],
    "en": ["fuck", "shit", "ass", "bitch", "damn", "bastard", "idiot"],
    "generic": ["nazi", "hitler", "satan", "666"]
}
