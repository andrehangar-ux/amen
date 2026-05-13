"""
Amen! API server entrypoint.

Models, core infrastructure (db/app/api_router/logger), and shared dependencies
have been extracted into separate modules:
- core.py: FastAPI app, MongoDB client, env vars, logger, supported languages,
  safety messages, content moderation lists.
- models.py: All Pydantic models.
- dependencies.py: Auth helpers, age helpers, friendship check, translate_text,
  check_content_moderation.
"""
from fastapi import HTTPException, Depends, Request, Response, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import re
import json
import asyncio
import hashlib
import resend
from emergentintegrations.llm.chat import LlmChat, UserMessage
from bible_data import NUOVA_DIODATI, REINA_VALERA_1960, get_bible_chapter
from bible_titles import get_book_info, get_chapter_title

# Core infrastructure
from core import (
    app,
    api_router,
    client,
    db,
    logger,
    ROOT_DIR,
    EMERGENT_LLM_KEY,
    SENDER_EMAIL,
    SUPPORTED_LANGUAGES,
    SAFETY_MESSAGES,
    BAD_WORDS,
)

# Pydantic models
from models import (
    User,
    UserSession,
    SessionDataResponse,
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    JournalEntry,
    JournalCreate,
    Bookmark,
    BookmarkCreate,
    ChatMessage,
    ChatRequest,
    MoodCheckIn,
    MoodRequest,
    Progress,
    DonationRequest,
    TranslateRequest,
    CommunityMessage,
    CommunityMessageCreate,
    StudyGroupMember,
    StudyGroup,
    StudyGroupCreate,
    StudyGroupMessage,
    StudyGroupMessageCreate,
    StudyGroupInvite,
    FeelingRequest,
    BibleGroup,
    GroupCreate,
    GroupPost,
    GroupPostCreate,
    PostComment,
    PrivateMessage,
    PrivateMessageCreate,
    Notification,
    StudyNote,
    StudyNoteCreate,
)

# Shared dependencies
from dependencies import (
    get_current_user,
    require_auth,
    calculate_age,
    is_minor,
    check_users_are_friends,
    translate_text,
    check_content_moderation,
)

# Route modules - importing registers endpoints on api_router (side effect)
from routes import auth as _auth_routes  # noqa: F401
from routes import notifications_friends as _nf_routes  # noqa: F401
from routes import journal_bookmarks_progress as _jbp_routes  # noqa: F401
from routes import forum as _forum_routes  # noqa: F401
from routes import parental_safety as _ps_routes  # noqa: F401
from routes import legal_donations as _ld_routes  # noqa: F401
from routes import community as _community_routes  # noqa: F401
from routes import private_messages as _pm_routes  # noqa: F401
from routes import users_presence as _up_routes  # noqa: F401
from routes import maps as _maps_routes  # noqa: F401
from routes import events as _events_routes  # noqa: F401
from routes import faq as _faq_routes  # noqa: F401
from routes import study_groups as _sg_routes  # noqa: F401
from routes import quiz as _quiz_routes  # noqa: F401

# ==================== AUTH ENDPOINTS ====================
# Moved to /app/backend/routes/auth.py (imported below as side-effect)

# ==================== BIBLE EDITIONS ====================

BIBLE_EDITIONS = {
    # Italian editions — all sourced from laparola.net
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
    "riveduta": {
        "name": "Nuova Riveduta",
        "language": "it",
        "year": "1994",
        "description": "Revisione contemporanea della Bibbia Riveduta"
    },
    # Spanish — single public-domain edition
    "reina_valera": {
        "name": "Reina Valera 1960",
        "language": "es",
        "year": "1960",
        "description": "La clásica traducción española protestante"
    },
    # English — multiple distinct public-domain editions via bible-api.com
    "kjv": {
        "name": "King James Version",
        "language": "en",
        "year": "1769",
        "description": "The classic English translation (1611, 1769 revision)"
    },
    "web": {
        "name": "World English Bible",
        "language": "en",
        "year": "2000",
        "description": "A modern public-domain English translation"
    },
    "asv": {
        "name": "American Standard Version",
        "language": "en",
        "year": "1901",
        "description": "Revision of the KJV, widely used historically"
    },
    "bbe": {
        "name": "Bible in Basic English",
        "language": "en",
        "year": "1965",
        "description": "Simplified English vocabulary (≈1000 base words)"
    },
    "ylt": {
        "name": "Young's Literal Translation",
        "language": "en",
        "year": "1898",
        "description": "Strictly literal English rendering of the original texts"
    },
    # Other languages — single public-domain edition each
    "almeida": {
        "name": "Almeida",
        "language": "pt",
        "year": "1911",
        "description": "Clássica tradução portuguesa de João Ferreira de Almeida"
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
        "year": "1912",
        "description": "Die klassische deutsche Übersetzung von Martin Luther"
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
        {"name": "1 Cronache", "chapters": 29, "abbrev": "1Cr"},
        {"name": "2 Cronache", "chapters": 36, "abbrev": "2Cr"},
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
        {"name": "Naum", "chapters": 3, "abbrev": "Naum"},
        {"name": "Abacuc", "chapters": 3, "abbrev": "Ab"},
        {"name": "Sofonia", "chapters": 3, "abbrev": "Sof"},
        {"name": "Aggeo", "chapters": 2, "abbrev": "Agg"},
        {"name": "Zaccaria", "chapters": 14, "abbrev": "Zac"},
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
        {"name": "1 Crónicas", "chapters": 29, "abbrev": "1Cr"},
        {"name": "2 Crónicas", "chapters": 36, "abbrev": "2Cr"},
        {"name": "Esdras", "chapters": 10, "abbrev": "Esd"},
        {"name": "Nehemías", "chapters": 13, "abbrev": "Neh"},
        {"name": "Ester", "chapters": 10, "abbrev": "Est"},
        {"name": "Job", "chapters": 42, "abbrev": "Job"},
        {"name": "Salmos", "chapters": 150, "abbrev": "Sal"},
        {"name": "Proverbios", "chapters": 31, "abbrev": "Prov"},
        {"name": "Eclesiastés", "chapters": 12, "abbrev": "Ecl"},
        {"name": "Cantar de los Cantares", "chapters": 8, "abbrev": "Cant"},
        {"name": "Isaías", "chapters": 66, "abbrev": "Is"},
        {"name": "Jeremías", "chapters": 52, "abbrev": "Jer"},
        {"name": "Lamentaciones", "chapters": 5, "abbrev": "Lam"},
        {"name": "Ezequiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Oseas", "chapters": 14, "abbrev": "Os"},
        {"name": "Joel", "chapters": 3, "abbrev": "Jl"},
        {"name": "Amós", "chapters": 9, "abbrev": "Am"},
        {"name": "Abdías", "chapters": 1, "abbrev": "Abd"},
        {"name": "Jonás", "chapters": 4, "abbrev": "Jon"},
        {"name": "Miqueas", "chapters": 7, "abbrev": "Mi"},
        {"name": "Nahum", "chapters": 3, "abbrev": "Nah"},
        {"name": "Habacuc", "chapters": 3, "abbrev": "Hab"},
        {"name": "Sofonías", "chapters": 3, "abbrev": "Sof"},
        {"name": "Hageo", "chapters": 2, "abbrev": "Hag"},
        {"name": "Zacarías", "chapters": 14, "abbrev": "Zac"},
        {"name": "Malaquías", "chapters": 4, "abbrev": "Mal"},
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
        {"name": "1 Tesalonicenses", "chapters": 5, "abbrev": "1Tes"},
        {"name": "2 Tesalonicenses", "chapters": 3, "abbrev": "2Tes"},
        {"name": "1 Timoteo", "chapters": 6, "abbrev": "1Tim"},
        {"name": "2 Timoteo", "chapters": 4, "abbrev": "2Tim"},
        {"name": "Tito", "chapters": 3, "abbrev": "Tit"},
        {"name": "Filemón", "chapters": 1, "abbrev": "Flm"},
        {"name": "Hebreos", "chapters": 13, "abbrev": "Heb"},
        {"name": "Santiago", "chapters": 5, "abbrev": "Stg"},
        {"name": "1 Pedro", "chapters": 5, "abbrev": "1Pe"},
        {"name": "2 Pedro", "chapters": 3, "abbrev": "2Pe"},
        {"name": "1 Juan", "chapters": 5, "abbrev": "1Jn"},
        {"name": "2 Juan", "chapters": 1, "abbrev": "2Jn"},
        {"name": "3 Juan", "chapters": 1, "abbrev": "3Jn"},
        {"name": "Judas", "chapters": 1, "abbrev": "Jud"},
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
        {"name": "1 Chronicles", "chapters": 29, "abbrev": "1Chr"},
        {"name": "2 Chronicles", "chapters": 36, "abbrev": "2Chr"},
        {"name": "Ezra", "chapters": 10, "abbrev": "Ezra"},
        {"name": "Nehemiah", "chapters": 13, "abbrev": "Neh"},
        {"name": "Esther", "chapters": 10, "abbrev": "Esth"},
        {"name": "Job", "chapters": 42, "abbrev": "Job"},
        {"name": "Psalms", "chapters": 150, "abbrev": "Ps"},
        {"name": "Proverbs", "chapters": 31, "abbrev": "Prov"},
        {"name": "Ecclesiastes", "chapters": 12, "abbrev": "Eccl"},
        {"name": "Song of Songs", "chapters": 8, "abbrev": "Song"},
        {"name": "Isaiah", "chapters": 66, "abbrev": "Isa"},
        {"name": "Jeremiah", "chapters": 52, "abbrev": "Jer"},
        {"name": "Lamentations", "chapters": 5, "abbrev": "Lam"},
        {"name": "Ezekiel", "chapters": 48, "abbrev": "Ezek"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Hosea", "chapters": 14, "abbrev": "Hos"},
        {"name": "Joel", "chapters": 3, "abbrev": "Joel"},
        {"name": "Amos", "chapters": 9, "abbrev": "Amos"},
        {"name": "Obadiah", "chapters": 1, "abbrev": "Obad"},
        {"name": "Jonah", "chapters": 4, "abbrev": "Jonah"},
        {"name": "Micah", "chapters": 7, "abbrev": "Mic"},
        {"name": "Nahum", "chapters": 3, "abbrev": "Nah"},
        {"name": "Habakkuk", "chapters": 3, "abbrev": "Hab"},
        {"name": "Zephaniah", "chapters": 3, "abbrev": "Zeph"},
        {"name": "Haggai", "chapters": 2, "abbrev": "Hag"},
        {"name": "Zechariah", "chapters": 14, "abbrev": "Zech"},
        {"name": "Malachi", "chapters": 4, "abbrev": "Mal"},
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
        {"name": "1 Thessalonians", "chapters": 5, "abbrev": "1Thess"},
        {"name": "2 Thessalonians", "chapters": 3, "abbrev": "2Thess"},
        {"name": "1 Timothy", "chapters": 6, "abbrev": "1Tim"},
        {"name": "2 Timothy", "chapters": 4, "abbrev": "2Tim"},
        {"name": "Titus", "chapters": 3, "abbrev": "Titus"},
        {"name": "Philemon", "chapters": 1, "abbrev": "Phlm"},
        {"name": "Hebrews", "chapters": 13, "abbrev": "Heb"},
        {"name": "James", "chapters": 5, "abbrev": "Jas"},
        {"name": "1 Peter", "chapters": 5, "abbrev": "1Pet"},
        {"name": "2 Peter", "chapters": 3, "abbrev": "2Pet"},
        {"name": "1 John", "chapters": 5, "abbrev": "1John"},
        {"name": "2 John", "chapters": 1, "abbrev": "2John"},
        {"name": "3 John", "chapters": 1, "abbrev": "3John"},
        {"name": "Jude", "chapters": 1, "abbrev": "Jude"},
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
        {"name": "1 Crônicas", "chapters": 29, "abbrev": "1Cr"},
        {"name": "2 Crônicas", "chapters": 36, "abbrev": "2Cr"},
        {"name": "Esdras", "chapters": 10, "abbrev": "Ed"},
        {"name": "Neemias", "chapters": 13, "abbrev": "Ne"},
        {"name": "Ester", "chapters": 10, "abbrev": "Et"},
        {"name": "Jó", "chapters": 42, "abbrev": "Jó"},
        {"name": "Salmos", "chapters": 150, "abbrev": "Sl"},
        {"name": "Provérbios", "chapters": 31, "abbrev": "Pv"},
        {"name": "Eclesiastes", "chapters": 12, "abbrev": "Ec"},
        {"name": "Cântico dos Cânticos", "chapters": 8, "abbrev": "Ct"},
        {"name": "Isaías", "chapters": 66, "abbrev": "Is"},
        {"name": "Jeremias", "chapters": 52, "abbrev": "Jr"},
        {"name": "Lamentações", "chapters": 5, "abbrev": "Lm"},
        {"name": "Ezequiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dn"},
        {"name": "Oseias", "chapters": 14, "abbrev": "Os"},
        {"name": "Joel", "chapters": 3, "abbrev": "Jl"},
        {"name": "Amós", "chapters": 9, "abbrev": "Am"},
        {"name": "Obadias", "chapters": 1, "abbrev": "Ob"},
        {"name": "Jonas", "chapters": 4, "abbrev": "Jn"},
        {"name": "Miqueias", "chapters": 7, "abbrev": "Mq"},
        {"name": "Naum", "chapters": 3, "abbrev": "Na"},
        {"name": "Habacuque", "chapters": 3, "abbrev": "Hc"},
        {"name": "Sofonias", "chapters": 3, "abbrev": "Sf"},
        {"name": "Ageu", "chapters": 2, "abbrev": "Ag"},
        {"name": "Zacarias", "chapters": 14, "abbrev": "Zc"},
        {"name": "Malaquias", "chapters": 4, "abbrev": "Ml"},
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
        {"name": "1 Tessalonicenses", "chapters": 5, "abbrev": "1Ts"},
        {"name": "2 Tessalonicenses", "chapters": 3, "abbrev": "2Ts"},
        {"name": "1 Timóteo", "chapters": 6, "abbrev": "1Tm"},
        {"name": "2 Timóteo", "chapters": 4, "abbrev": "2Tm"},
        {"name": "Tito", "chapters": 3, "abbrev": "Tt"},
        {"name": "Filemom", "chapters": 1, "abbrev": "Fm"},
        {"name": "Hebreus", "chapters": 13, "abbrev": "Hb"},
        {"name": "Tiago", "chapters": 5, "abbrev": "Tg"},
        {"name": "1 Pedro", "chapters": 5, "abbrev": "1Pe"},
        {"name": "2 Pedro", "chapters": 3, "abbrev": "2Pe"},
        {"name": "1 João", "chapters": 5, "abbrev": "1Jo"},
        {"name": "2 João", "chapters": 1, "abbrev": "2Jo"},
        {"name": "3 João", "chapters": 1, "abbrev": "3Jo"},
        {"name": "Judas", "chapters": 1, "abbrev": "Jd"},
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
        {"name": "1 Chroniques", "chapters": 29, "abbrev": "1Ch"},
        {"name": "2 Chroniques", "chapters": 36, "abbrev": "2Ch"},
        {"name": "Esdras", "chapters": 10, "abbrev": "Esd"},
        {"name": "Néhémie", "chapters": 13, "abbrev": "Né"},
        {"name": "Esther", "chapters": 10, "abbrev": "Est"},
        {"name": "Job", "chapters": 42, "abbrev": "Jb"},
        {"name": "Psaumes", "chapters": 150, "abbrev": "Ps"},
        {"name": "Proverbes", "chapters": 31, "abbrev": "Pr"},
        {"name": "Ecclésiaste", "chapters": 12, "abbrev": "Ec"},
        {"name": "Cantique des Cantiques", "chapters": 8, "abbrev": "Ct"},
        {"name": "Ésaïe", "chapters": 66, "abbrev": "Es"},
        {"name": "Jérémie", "chapters": 52, "abbrev": "Jr"},
        {"name": "Lamentations", "chapters": 5, "abbrev": "Lm"},
        {"name": "Ézéchiel", "chapters": 48, "abbrev": "Ez"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dn"},
        {"name": "Osée", "chapters": 14, "abbrev": "Os"},
        {"name": "Joël", "chapters": 3, "abbrev": "Jl"},
        {"name": "Amos", "chapters": 9, "abbrev": "Am"},
        {"name": "Abdias", "chapters": 1, "abbrev": "Ab"},
        {"name": "Jonas", "chapters": 4, "abbrev": "Jon"},
        {"name": "Michée", "chapters": 7, "abbrev": "Mi"},
        {"name": "Nahum", "chapters": 3, "abbrev": "Na"},
        {"name": "Habacuc", "chapters": 3, "abbrev": "Ha"},
        {"name": "Sophonie", "chapters": 3, "abbrev": "So"},
        {"name": "Aggée", "chapters": 2, "abbrev": "Ag"},
        {"name": "Zacharie", "chapters": 14, "abbrev": "Za"},
        {"name": "Malachie", "chapters": 4, "abbrev": "Ml"},
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
        {"name": "1 Thessaloniciens", "chapters": 5, "abbrev": "1Th"},
        {"name": "2 Thessaloniciens", "chapters": 3, "abbrev": "2Th"},
        {"name": "1 Timothée", "chapters": 6, "abbrev": "1Tm"},
        {"name": "2 Timothée", "chapters": 4, "abbrev": "2Tm"},
        {"name": "Tite", "chapters": 3, "abbrev": "Tt"},
        {"name": "Philémon", "chapters": 1, "abbrev": "Phm"},
        {"name": "Hébreux", "chapters": 13, "abbrev": "He"},
        {"name": "Jacques", "chapters": 5, "abbrev": "Jc"},
        {"name": "1 Pierre", "chapters": 5, "abbrev": "1P"},
        {"name": "2 Pierre", "chapters": 3, "abbrev": "2P"},
        {"name": "1 Jean", "chapters": 5, "abbrev": "1Jn"},
        {"name": "2 Jean", "chapters": 1, "abbrev": "2Jn"},
        {"name": "3 Jean", "chapters": 1, "abbrev": "3Jn"},
        {"name": "Jude", "chapters": 1, "abbrev": "Jude"},
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
        {"name": "1 Chronik", "chapters": 29, "abbrev": "1Chr"},
        {"name": "2 Chronik", "chapters": 36, "abbrev": "2Chr"},
        {"name": "Esra", "chapters": 10, "abbrev": "Esr"},
        {"name": "Nehemia", "chapters": 13, "abbrev": "Neh"},
        {"name": "Ester", "chapters": 10, "abbrev": "Est"},
        {"name": "Hiob", "chapters": 42, "abbrev": "Hi"},
        {"name": "Psalmen", "chapters": 150, "abbrev": "Ps"},
        {"name": "Sprüche", "chapters": 31, "abbrev": "Spr"},
        {"name": "Prediger", "chapters": 12, "abbrev": "Pred"},
        {"name": "Hohelied", "chapters": 8, "abbrev": "Hld"},
        {"name": "Jesaja", "chapters": 66, "abbrev": "Jes"},
        {"name": "Jeremia", "chapters": 52, "abbrev": "Jer"},
        {"name": "Klagelieder", "chapters": 5, "abbrev": "Klg"},
        {"name": "Hesekiel", "chapters": 48, "abbrev": "Hes"},
        {"name": "Daniel", "chapters": 12, "abbrev": "Dan"},
        {"name": "Hosea", "chapters": 14, "abbrev": "Hos"},
        {"name": "Joel", "chapters": 3, "abbrev": "Joel"},
        {"name": "Amos", "chapters": 9, "abbrev": "Am"},
        {"name": "Obadja", "chapters": 1, "abbrev": "Obd"},
        {"name": "Jona", "chapters": 4, "abbrev": "Jona"},
        {"name": "Micha", "chapters": 7, "abbrev": "Mi"},
        {"name": "Nahum", "chapters": 3, "abbrev": "Nah"},
        {"name": "Habakuk", "chapters": 3, "abbrev": "Hab"},
        {"name": "Zefanja", "chapters": 3, "abbrev": "Zef"},
        {"name": "Haggai", "chapters": 2, "abbrev": "Hag"},
        {"name": "Sacharja", "chapters": 14, "abbrev": "Sach"},
        {"name": "Maleachi", "chapters": 4, "abbrev": "Mal"},
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
        {"name": "1 Thessalonicher", "chapters": 5, "abbrev": "1Thess"},
        {"name": "2 Thessalonicher", "chapters": 3, "abbrev": "2Thess"},
        {"name": "1 Timotheus", "chapters": 6, "abbrev": "1Tim"},
        {"name": "2 Timotheus", "chapters": 4, "abbrev": "2Tim"},
        {"name": "Titus", "chapters": 3, "abbrev": "Tit"},
        {"name": "Philemon", "chapters": 1, "abbrev": "Phlm"},
        {"name": "Hebräer", "chapters": 13, "abbrev": "Heb"},
        {"name": "Jakobus", "chapters": 5, "abbrev": "Jak"},
        {"name": "1 Petrus", "chapters": 5, "abbrev": "1Pt"},
        {"name": "2 Petrus", "chapters": 3, "abbrev": "2Pt"},
        {"name": "1 Johannes", "chapters": 5, "abbrev": "1Joh"},
        {"name": "2 Johannes", "chapters": 1, "abbrev": "2Joh"},
        {"name": "3 Johannes", "chapters": 1, "abbrev": "3Joh"},
        {"name": "Judas", "chapters": 1, "abbrev": "Jud"},
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
    "de": {
        "Johannes:3": [
            {"verse": 16, "text": "Denn also hat Gott die Welt geliebt, dass er seinen eingeborenen Sohn gab, damit alle, die an ihn glauben, nicht verloren werden, sondern das ewige Leben haben."},
        ],
        "Psalm:23": [
            {"verse": 1, "text": "Der Herr ist mein Hirte, mir wird nichts mangeln."},
            {"verse": 2, "text": "Er weidet mich auf einer grünen Aue und führet mich zum frischen Wasser."},
            {"verse": 3, "text": "Er erquicket meine Seele. Er führet mich auf rechter Straße um seines Namens willen."},
            {"verse": 4, "text": "Und ob ich schon wanderte im finstern Tal, fürchte ich kein Unglück; denn du bist bei mir."},
        ],
        "Römer:8": [
            {"verse": 28, "text": "Wir wissen aber, dass denen, die Gott lieben, alle Dinge zum Besten dienen."},
            {"verse": 31, "text": "Was wollen wir nun hierzu sagen? Ist Gott für uns, wer kann wider uns sein?"},
        ],
        "Philipper:4": [
            {"verse": 13, "text": "Ich vermag alles durch den, der mich mächtig macht, Christus."},
        ],
    },
}

# Mood verses in multiple languages
MOOD_VERSES_MULTILANG = {
    "it": {
        "felice": [
            {"ref": "Salmi 118:24", "text": "Questo è il giorno che l'Eterno ha fatto; rallegriamoci e gioisciamo in esso."},
            {"ref": "Salmi 16:11", "text": "Tu mi farai conoscere il sentiero della vita; c'è abbondanza di gioia alla tua presenza."},
            {"ref": "Neemia 8:10", "text": "La gioia dell'Eterno è la vostra forza."},
            {"ref": "Romani 15:13", "text": "Il Dio della speranza vi riempia di ogni gioia e pace nel credere."},
            {"ref": "Salmi 126:3", "text": "L'Eterno ha fatto grandi cose per noi e ne siamo lieti."},
            {"ref": "Isaia 55:12", "text": "Voi uscirete con gioia e sarete ricondotti in pace."},
        ],
        "triste": [
            {"ref": "Salmi 34:18", "text": "L'Eterno è vicino a quelli che hanno il cuore rotto."},
            {"ref": "Salmi 30:5", "text": "Il pianto può durare una notte, ma la mattina viene la gioia."},
            {"ref": "Salmi 147:3", "text": "Egli sana quelli che hanno il cuore rotto e fascia le loro ferite."},
            {"ref": "2 Corinzi 1:3-4", "text": "Dio di ogni consolazione, che ci consola in ogni nostra afflizione."},
            {"ref": "Apocalisse 21:4", "text": "Egli asciugherà ogni lacrima dai loro occhi."},
            {"ref": "Salmi 42:11", "text": "Perché ti abbatti, anima mia? Spera in Dio, perché io lo celebrerò ancora."},
        ],
        "ansioso": [
            {"ref": "Filippesi 4:6-7", "text": "Non angustiatevi di nulla, ma in ogni cosa fate conoscere le vostre richieste a Dio."},
            {"ref": "1 Pietro 5:7", "text": "Gettando su di lui ogni vostra preoccupazione, perché egli ha cura di voi."},
            {"ref": "Isaia 41:10", "text": "Non temere, perché io sono con te; non smarrirti, perché io sono il tuo Dio."},
            {"ref": "Matteo 6:34", "text": "Non siate dunque in ansia per il domani, perché il domani si preoccuperà di se stesso."},
            {"ref": "Salmi 55:22", "text": "Getta sull'Eterno il tuo peso, ed egli ti sosterrà."},
            {"ref": "Giovanni 14:27", "text": "Vi lascio la pace, vi do la mia pace. Non come il mondo la dà, io la do a voi."},
        ],
        "arrabbiato": [
            {"ref": "Efesini 4:26", "text": "Adiratevi e non peccate; il sole non tramonti sopra la vostra ira."},
            {"ref": "Proverbi 15:1", "text": "Una risposta dolce calma il furore, ma una parola dura eccita l'ira."},
            {"ref": "Giacomo 1:19-20", "text": "Ogni uomo sia pronto ad ascoltare, lento a parlare, lento all'ira."},
            {"ref": "Colossesi 3:8", "text": "Ora deponete anche voi tutte queste cose: ira, collera, malignità."},
            {"ref": "Proverbi 29:11", "text": "Lo stolto dà sfogo a tutta la sua ira, ma il saggio la reprime."},
        ],
        "grato": [
            {"ref": "1 Tessalonicesi 5:18", "text": "In ogni cosa rendete grazie."},
            {"ref": "Salmi 100:4", "text": "Entrate nelle sue porte con ringraziamento, nei suoi cortili con lode."},
            {"ref": "Colossesi 3:17", "text": "Qualunque cosa facciate, in parola o in opera, fate ogni cosa nel nome del Signore Gesù, ringraziando Dio."},
            {"ref": "Salmi 107:1", "text": "Celebrate l'Eterno, perché è buono, perché la sua benignità dura in eterno."},
            {"ref": "Salmi 136:1", "text": "Lodate l'Eterno perché è buono, perché la sua benignità dura in eterno."},
        ],
        "confuso": [
            {"ref": "Proverbi 3:5-6", "text": "Confida nell'Eterno con tutto il cuore e non appoggiarti sul tuo intendimento."},
            {"ref": "Giacomo 1:5", "text": "Se qualcuno di voi manca di sapienza, la chieda a Dio che dona a tutti liberamente."},
            {"ref": "Salmi 32:8", "text": "Io ti istruirò e t'insegnerò la via per la quale devi camminare."},
            {"ref": "Isaia 30:21", "text": "Le tue orecchie udranno una parola dietro a te: Questa è la via, camminate in essa."},
            {"ref": "Salmi 119:105", "text": "La tua parola è una lampada al mio piede e una luce sul mio sentiero."},
        ],
        "speranzoso": [
            {"ref": "Geremia 29:11", "text": "Poiché io conosco i pensieri che ho per voi, pensieri di pace e non di male."},
            {"ref": "Romani 8:28", "text": "Tutte le cose cooperano al bene di quelli che amano Dio."},
            {"ref": "Isaia 40:31", "text": "Quelli che sperano nell'Eterno acquistano nuove forze."},
            {"ref": "Salmi 27:14", "text": "Spera nell'Eterno! Sii forte, il tuo cuore si faccia animo; sì, spera nell'Eterno!"},
            {"ref": "Ebrei 11:1", "text": "La fede è certezza di cose che si sperano, dimostrazione di realtà che non si vedono."},
        ],
        "stanco": [
            {"ref": "Matteo 11:28", "text": "Venite a me, voi tutti che siete travagliati e aggravati, e io vi darò riposo."},
            {"ref": "Isaia 40:29", "text": "Egli dà forza allo stanco e accresce vigore a chi è spossato."},
            {"ref": "Salmi 23:2-3", "text": "Egli mi fa riposare in verdeggianti pascoli, mi guida lungo le acque calme, egli ristora la mia anima."},
            {"ref": "Esodo 33:14", "text": "La mia presenza andrà con te e io ti darò riposo."},
            {"ref": "Salmi 62:1", "text": "Solo in Dio l'anima mia trova riposo; da lui viene la mia salvezza."},
        ],
    },
    "en": {
        "felice": [
            {"ref": "Psalm 118:24", "text": "This is the day which the Lord hath made; we will rejoice and be glad in it."},
            {"ref": "Psalm 16:11", "text": "You make known to me the path of life; in your presence there is fullness of joy."},
            {"ref": "Nehemiah 8:10", "text": "The joy of the Lord is your strength."},
            {"ref": "Romans 15:13", "text": "May the God of hope fill you with all joy and peace in believing."},
            {"ref": "Psalm 126:3", "text": "The Lord has done great things for us, and we are filled with joy."},
        ],
        "triste": [
            {"ref": "Psalm 34:18", "text": "The Lord is nigh unto them that are of a broken heart."},
            {"ref": "Psalm 30:5", "text": "Weeping may endure for a night, but joy comes in the morning."},
            {"ref": "Psalm 147:3", "text": "He heals the brokenhearted and binds up their wounds."},
            {"ref": "Revelation 21:4", "text": "He will wipe every tear from their eyes."},
            {"ref": "Psalm 42:11", "text": "Why are you cast down, O my soul? Hope in God, for I shall yet praise Him."},
        ],
        "ansioso": [
            {"ref": "Philippians 4:6-7", "text": "Be careful for nothing; but in every thing by prayer let your requests be made known unto God."},
            {"ref": "1 Peter 5:7", "text": "Cast all your anxiety on Him because He cares for you."},
            {"ref": "Isaiah 41:10", "text": "Fear not, for I am with you; be not dismayed, for I am your God."},
            {"ref": "John 14:27", "text": "Peace I leave with you; my peace I give you. Not as the world gives do I give to you."},
            {"ref": "Psalm 55:22", "text": "Cast your burden on the Lord, and He shall sustain you."},
        ],
        "arrabbiato": [
            {"ref": "Ephesians 4:26", "text": "Be angry and sin not; let not the sun go down upon your wrath."},
            {"ref": "Proverbs 15:1", "text": "A soft answer turns away wrath, but a harsh word stirs up anger."},
            {"ref": "James 1:19-20", "text": "Let every man be swift to hear, slow to speak, slow to wrath."},
        ],
        "grato": [
            {"ref": "1 Thessalonians 5:18", "text": "In every thing give thanks."},
            {"ref": "Psalm 100:4", "text": "Enter His gates with thanksgiving, and His courts with praise."},
            {"ref": "Colossians 3:17", "text": "Whatever you do in word or deed, do all in the name of the Lord Jesus, giving thanks to God."},
        ],
        "confuso": [
            {"ref": "Proverbs 3:5-6", "text": "Trust in the Lord with all your heart and lean not on your own understanding."},
            {"ref": "James 1:5", "text": "If any of you lacks wisdom, let him ask of God, who gives to all liberally."},
            {"ref": "Psalm 119:105", "text": "Your word is a lamp to my feet and a light to my path."},
        ],
        "speranzoso": [
            {"ref": "Jeremiah 29:11", "text": "For I know the plans I have for you, plans to prosper you and not to harm you."},
            {"ref": "Romans 8:28", "text": "All things work together for good to those who love God."},
            {"ref": "Isaiah 40:31", "text": "Those who hope in the Lord will renew their strength."},
        ],
        "stanco": [
            {"ref": "Matthew 11:28", "text": "Come unto me, all ye that labour and are heavy laden, and I will give you rest."},
            {"ref": "Isaiah 40:29", "text": "He gives strength to the weary and increases the power of the weak."},
            {"ref": "Psalm 23:2-3", "text": "He makes me lie down in green pastures, He leads me beside still waters, He restores my soul."},
        ],
    },
    "es": {
        "felice": [
            {"ref": "Salmos 118:24", "text": "Este es el día que hizo Jehová; nos gozaremos y alegraremos en él."},
            {"ref": "Salmos 16:11", "text": "Me mostrarás la senda de la vida; en tu presencia hay plenitud de gozo."},
            {"ref": "Nehemías 8:10", "text": "El gozo de Jehová es vuestra fuerza."},
        ],
        "triste": [
            {"ref": "Salmos 34:18", "text": "Cercano está Jehová a los quebrantados de corazón."},
            {"ref": "Salmos 30:5", "text": "El llanto puede durar toda la noche, pero a la mañana viene la alegría."},
            {"ref": "Apocalipsis 21:4", "text": "Enjugará Dios toda lágrima de los ojos de ellos."},
        ],
        "ansioso": [
            {"ref": "Filipenses 4:6-7", "text": "Por nada estéis afanosos, sino sean conocidas vuestras peticiones delante de Dios."},
            {"ref": "1 Pedro 5:7", "text": "Echando toda vuestra ansiedad sobre él, porque él tiene cuidado de vosotros."},
            {"ref": "Isaías 41:10", "text": "No temas, porque yo estoy contigo; no desmayes, porque yo soy tu Dios."},
        ],
        "stanco": [
            {"ref": "Mateo 11:28", "text": "Venid a mí todos los que estáis trabajados y cargados, y yo os haré descansar."},
            {"ref": "Isaías 40:29", "text": "Él da esfuerzo al cansado, y multiplica las fuerzas al que no tiene ningunas."},
        ],
        "arrabbiato": [
            {"ref": "Efesios 4:26", "text": "Airaos, pero no pequéis; no se ponga el sol sobre vuestro enojo."},
        ],
        "grato": [
            {"ref": "1 Tesalonicenses 5:18", "text": "Dad gracias en todo."},
        ],
        "confuso": [
            {"ref": "Proverbios 3:5-6", "text": "Fíate de Jehová de todo tu corazón, y no te apoyes en tu propia prudencia."},
        ],
        "speranzoso": [
            {"ref": "Jeremías 29:11", "text": "Porque yo sé los pensamientos que tengo acerca de vosotros, pensamientos de paz, y no de mal."},
        ],
    },
    "pt": {
        "felice": [
            {"ref": "Salmos 118:24", "text": "Este é o dia que o Senhor fez; regozijemo-nos e alegremo-nos nele."},
            {"ref": "Salmos 16:11", "text": "Tu me farás ver a vereda da vida; na tua presença há fartura de alegrias."},
        ],
        "triste": [
            {"ref": "Salmos 34:18", "text": "Perto está o Senhor dos que têm o coração quebrantado."},
            {"ref": "Salmos 30:5", "text": "O choro pode durar uma noite, mas a alegria vem pela manhã."},
        ],
        "ansioso": [
            {"ref": "Filipenses 4:6-7", "text": "Não estejais inquietos por coisa alguma; antes as vossas petições sejam conhecidas diante de Deus."},
            {"ref": "1 Pedro 5:7", "text": "Lançando sobre ele toda a vossa ansiedade, porque ele tem cuidado de vós."},
        ],
        "stanco": [
            {"ref": "Mateus 11:28", "text": "Vinde a mim, todos os que estais cansados e oprimidos, e eu vos aliviarei."},
            {"ref": "Isaías 40:29", "text": "Ele dá forças ao cansado e multiplica as forças ao que não tem nenhum vigor."},
        ],
        "speranzoso": [
            {"ref": "Jeremias 29:11", "text": "Eu é que sei que pensamentos tenho a vosso respeito, pensamentos de paz e não de mal."},
        ],
        "confuso": [
            {"ref": "Provérbios 3:5-6", "text": "Confia no Senhor de todo o teu coração, e não te estribes no teu próprio entendimento."},
        ],
    },
    "fr": {
        "felice": [
            {"ref": "Psaume 118:24", "text": "C'est ici la journée que l'Éternel a faite: Qu'elle soit pour nous un sujet d'allégresse et de joie!"},
            {"ref": "Psaume 16:11", "text": "Tu me feras connaître le sentier de la vie; il y a d'abondantes joies devant ta face."},
        ],
        "triste": [
            {"ref": "Psaume 34:18", "text": "L'Éternel est près de ceux qui ont le cœur brisé."},
            {"ref": "Psaume 30:5", "text": "Les pleurs peuvent durer toute une nuit, mais le matin la joie est là."},
        ],
        "ansioso": [
            {"ref": "Philippiens 4:6-7", "text": "Ne vous inquiétez de rien; mais en toute chose faites connaître vos besoins à Dieu."},
            {"ref": "1 Pierre 5:7", "text": "Déchargez-vous sur lui de tous vos soucis, car lui-même prend soin de vous."},
        ],
        "stanco": [
            {"ref": "Matthieu 11:28", "text": "Venez à moi, vous tous qui êtes fatigués et chargés, et je vous donnerai du repos."},
            {"ref": "Ésaïe 40:29", "text": "Il donne de la force à celui qui est las, et il augmente la vigueur de celui qui tombe en défaillance."},
        ],
        "speranzoso": [
            {"ref": "Jérémie 29:11", "text": "Car je connais les projets que j'ai formés sur vous, projets de paix et non de malheur."},
        ],
        "confuso": [
            {"ref": "Proverbes 3:5-6", "text": "Confie-toi en l'Éternel de tout ton cœur, et ne t'appuie pas sur ta sagesse."},
        ],
    },
    "de": {
        "felice": [
            {"ref": "Psalm 118:24", "text": "Dies ist der Tag, den der Herr macht; lasst uns freuen und fröhlich an ihm sein."},
            {"ref": "Psalm 16:11", "text": "Du tust mir kund den Weg zum Leben: Vor dir ist Freude die Fülle."},
        ],
        "triste": [
            {"ref": "Psalm 34:18", "text": "Der Herr ist nahe denen, die zerbrochenen Herzens sind."},
            {"ref": "Psalm 30:5", "text": "Den Abend lang währet das Weinen, aber des Morgens ist Freude."},
        ],
        "ansioso": [
            {"ref": "Philipper 4:6-7", "text": "Sorgt euch um nichts, sondern in allen Dingen lasst eure Bitten vor Gott kundwerden."},
            {"ref": "1 Petrus 5:7", "text": "Alle eure Sorge werft auf ihn; denn er sorgt für euch."},
        ],
        "arrabbiato": [
            {"ref": "Epheser 4:26", "text": "Zürnet ihr, so sündigt nicht; lasst die Sonne nicht über eurem Zorn untergehen."},
        ],
        "grato": [
            {"ref": "1. Thessalonicher 5:18", "text": "Seid dankbar in allen Dingen."},
        ],
        "confuso": [
            {"ref": "Sprüche 3:5-6", "text": "Verlass dich auf den Herrn von ganzem Herzen und verlass dich nicht auf deinen Verstand."},
        ],
        "speranzoso": [
            {"ref": "Jeremia 29:11", "text": "Denn ich weiß wohl, was ich für Gedanken über euch habe, Gedanken des Friedens und nicht des Leides."},
        ],
        "stanco": [
            {"ref": "Matthäus 11:28", "text": "Kommt her zu mir, alle, die ihr mühselig und beladen seid; ich will euch erquicken."},
            {"ref": "Jesaja 40:29", "text": "Er gibt dem Müden Kraft und Stärke genug dem Unvermögenden."},
        ],
    },
}

@api_router.get("/bible/books")
async def get_bible_books(lang: str = "it"):
    """Get list of Bible books in specified language"""
    return BIBLE_BOOKS_MULTILANG.get(lang, BIBLE_BOOKS_MULTILANG["it"])

# Helper function to fetch Bible text from laparola.net
async def fetch_from_laparola(book: str, chapter: int, version: str = "Nuova+Diodati") -> list:
    """Fetch Bible chapter from laparola.net.

    Supported versions on laparola.net (Italian):
      - Nuova+Diodati (default, Protestant 1991)
      - Diodati (Diodati Classica 1641)
      - NRiveduta (Nuova Riveduta 1994)
      - CEI (Conferenza Episcopale Italiana 2008)
    """
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

async def fetch_from_bible_api(book: str, chapter: int, lang: str = "en", edition: str = None) -> list:
    """Fetch Bible chapter from bible-api.com supporting multiple translations.

    Map of supported public-domain translations on bible-api.com:
      English: kjv (1769), web (World English Bible), asv (American Standard 1901),
               bbe (Bible in Basic English 1965), ylt (Young's Literal 1898),
               dra (Douay-Rheims 1899, Catholic)
      Other languages currently rely on the WEB fallback.
    """
    try:
        # Map any-language book name to English for the API
        book_en = get_book_name_for_lang(book, "en")

        # Edition → bible-api.com translation code
        edition_to_code = {
            # English public-domain
            "kjv": "kjv",
            "asv": "asv",
            "web": "web",
            "bbe": "bbe",
            "ylt": "ylt",
            "dra": "dra",
            # NIV is copyrighted → fallback to WEB
            "niv": "web",
            # Italian, Spanish, French, German, Portuguese have no distinct
            # public-domain alternates on bible-api.com. They are served from
            # the static NUOVA_DIODATI / REINA_VALERA_1960 caches first, then
            # fall back to the WEB English text (for any-lang) if missing.
        }

        if edition and edition in edition_to_code:
            translation = edition_to_code[edition]
        else:
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

            logger.info(f"Fetched {len(verses)} verses from bible-api.com for {book} {chapter} ({lang}/{translation})")
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

async def fetch_bible_chapter_any_lang(book: str, chapter: int, lang: str, edition: str = None) -> list:
    """Fetch Bible chapter in any language using multiple free APIs.

    If `edition` is provided, the source is selected to honor that edition:
      - Italian editions (nuova_diodati, diodati_classica, riveduta, cei) → laparola.net
      - English editions (kjv, web, asv, bbe, ylt, dra) → bible-api.com
      - Other languages have a single public-domain source per language.
    """

    # Italian: laparola.net supports multiple Italian versions
    if lang == "it":
        edition_to_version = {
            "nuova_diodati": "Nuova+Diodati",
            "diodati_classica": "Diodati",
            "riveduta": "NRiveduta",
            "cei": "CEI",
        }
        version = edition_to_version.get(edition, "Nuova+Diodati")
        verses = await fetch_from_laparola(book, chapter, version=version)
        if verses and len(verses) > 3:
            return verses

    # English: bible-api.com supports multiple public-domain translations
    if lang == "en":
        verses = await fetch_from_bible_api(book, chapter, lang="en", edition=edition)
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
async def get_chapter(book: str, chapter: int, lang: str = "it", edition: str = None):
    """Get verses for a chapter in specified language and edition.

    `edition` is a key from BIBLE_EDITIONS (e.g. "nuova_diodati", "kjv", "web", "asv").
    If omitted, the system uses the default edition per language.
    The cache key includes `edition` so different editions don't overwrite each other.
    """
    key = f"{book}:{chapter}"

    # Section title metadata (always included)
    book_info = get_book_info(book, lang)
    chapter_title = get_chapter_title(book, chapter, lang)

    # Resolve edition default per language
    default_editions = {"it": "nuova_diodati", "es": "reina_valera", "en": "kjv",
                        "pt": "almeida", "fr": "louis_segond", "de": "luther"}
    resolved_edition = edition or default_editions.get(lang, "")

    # For default Italian/Spanish editions, prefer the static curated data
    use_static = (
        (lang == "it" and resolved_edition == "nuova_diodati") or
        (lang == "es" and resolved_edition == "reina_valera")
    )

    if use_static:
        if lang == "it":
            verses = NUOVA_DIODATI.get(key, [])
        else:
            verses = REINA_VALERA_1960.get(key, [])

        if verses:
            return {"book": book, "chapter": chapter, "verses": verses, "language": lang,
                    "edition": resolved_edition,
                    "book_info": book_info, "chapter_title": chapter_title}

    # Check MongoDB cache (per edition!)
    cache_query = {"book": book, "chapter": chapter, "language": lang, "edition": resolved_edition}
    cached = await db.bible_cache.find_one(cache_query)
    if cached and cached.get("verses") and len(cached.get("verses", [])) > 3:
        return {"book": book, "chapter": chapter, "verses": cached["verses"], "language": lang,
                "edition": resolved_edition,
                "book_info": book_info, "chapter_title": chapter_title}

    # Fetch from external APIs with edition awareness
    fetched_verses = await fetch_bible_chapter_any_lang(book, chapter, lang, edition=resolved_edition)

    if fetched_verses and len(fetched_verses) > 3:
        # Cache in MongoDB (key includes edition)
        await db.bible_cache.update_one(
            cache_query,
            {"$set": {**cache_query, "verses": fetched_verses, "source": "external_api",
                      "cached_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        return {"book": book, "chapter": chapter, "verses": fetched_verses, "language": lang,
                "edition": resolved_edition,
                "book_info": book_info, "chapter_title": chapter_title}

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

    return {"book": book, "chapter": chapter, "verses": verses, "language": lang,
            "edition": resolved_edition,
            "book_info": book_info, "chapter_title": chapter_title}


@api_router.get("/bible/section-title/{book}/{chapter}")
async def get_bible_section_title(book: str, chapter: int, lang: str = "it"):
    """Get standalone book info + chapter section title (for headers/previews)"""
    return {
        "book": book,
        "chapter": chapter,
        "language": lang,
        "book_info": get_book_info(book, lang),
        "chapter_title": get_chapter_title(book, chapter, lang),
    }

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
    
    # Get user's bookmarks for this chapter
    user_bookmarks = await db.bookmarks.find(
        {"user_id": user.user_id, "book": book, "chapter": chapter},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "book": book,
        "chapter": chapter,
        "cross_references": cross_refs,
        "dictionary_links": dict_links,
        "study_context": context,
        "user_notes": user_notes,
        "user_bookmarks": user_bookmarks
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
    """Get daily verse in specified language - changes every day of the year"""
    from data.daily_verses import DAILY_VERSES_365
    
    # Get day of year (1-365)
    today = datetime.now(timezone.utc)
    day_of_year = today.timetuple().tm_yday
    
    # Select verse for today (cycling through available verses)
    index = (day_of_year - 1) % len(DAILY_VERSES_365)
    verse_data = DAILY_VERSES_365[index]
    
    # Get text in requested language, fallback to Italian
    text = verse_data.get(lang, verse_data.get("it", ""))
    
    return {
        "reference": verse_data["reference"],
        "text": text,
        "language": lang,
        "day_of_year": day_of_year
    }

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

        system_messages = {
            "it": "Sei un assistente spirituale cristiano. Rispondi in italiano con compassione e saggezza biblica.",
            "es": "Eres un asistente espiritual cristiano. Responde en español con compasión y sabiduría bíblica.",
            "en": "You are a Christian spiritual assistant. Respond in English with compassion and biblical wisdom.",
            "pt": "Você é um assistente espiritual cristão. Responda em português com compaixão e sabedoria bíblica.",
            "fr": "Tu es un assistant spirituel chrétien. Réponds en français avec compassion et sagesse biblique.",
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
        
        # Map English mood keys to language-specific keys
        mood_key_mapping = {
            "it": {"happy": "felice", "sad": "triste", "anxious": "ansioso", "angry": "arrabbiato", 
                   "grateful": "grato", "confused": "confuso", "hopeful": "speranzoso", "tired": "stanco"},
            "en": {"happy": "happy", "sad": "sad", "anxious": "anxious", "angry": "angry",
                   "grateful": "grateful", "confused": "confused", "hopeful": "hopeful", "tired": "tired"},
            "es": {"happy": "feliz", "sad": "triste", "anxious": "ansioso", "angry": "enojado",
                   "grateful": "agradecido", "confused": "confundido", "hopeful": "esperanzado", "tired": "cansado"},
            "pt": {"happy": "feliz", "sad": "triste", "anxious": "ansioso", "angry": "irritado",
                   "grateful": "grato", "confused": "confuso", "hopeful": "esperançoso", "tired": "cansado"},
            "fr": {"happy": "heureux", "sad": "triste", "anxious": "anxieux", "angry": "en colère",
                   "grateful": "reconnaissant", "confused": "confus", "hopeful": "plein d'espoir", "tired": "fatigué"},
            "de": {"happy": "glücklich", "sad": "traurig", "anxious": "ängstlich", "angry": "wütend",
                   "grateful": "dankbar", "confused": "verwirrt", "hopeful": "hoffnungsvoll", "tired": "müde"},
        }
        
        mood_verses = MOOD_VERSES_MULTILANG.get(lang, MOOD_VERSES_MULTILANG["it"])
        input_mood = data.mood.lower()
        
        # Try to map the mood key, or use as-is if already in correct format
        lang_mapping = mood_key_mapping.get(lang, mood_key_mapping["it"])
        mood = lang_mapping.get(input_mood, input_mood)
        
        # Get verses for the mood, with fallback
        mood_data = mood_verses.get(mood)
        if not mood_data:
            # Try with the original input mood
            mood_data = mood_verses.get(input_mood)
        if not mood_data:
            # Default fallback
            first_mood = list(mood_verses.keys())[0] if mood_verses else "speranzoso"
            mood_data = mood_verses.get(first_mood, [{"ref": "Salmi 23:1", "text": "Il Signore è il mio pastore."}])
        
        # Random selection: different verse each time user taps a mood
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
# Moved to /app/backend/routes/community.py

# Online users + user settings moved to /app/backend/routes/users_presence.py

# ==================== PRIVATE MESSAGES + COMMUNITY GET/LIKE/USERS ====================
# Moved to /app/backend/routes/private_messages.py and /app/backend/routes/community.py


# ==================== JOURNAL ENDPOINTS ====================

# ==================== JOURNAL & BOOKMARKS & PROGRESS ====================
# Moved to /app/backend/routes/journal_bookmarks_progress.py

# ==================== LEGAL & CONSENT & DONATIONS ====================
# Moved to /app/backend/routes/legal_donations.py

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
    except Exception:
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

# Legacy /messages routes moved to /app/backend/routes/private_messages.py

# ==================== NOTIFICATIONS ====================

# ==================== NOTIFICATIONS & FRIENDS ====================
# Moved to /app/backend/routes/notifications_friends.py

# ==================== QUIZ BIBLICO ====================
# Moved to /app/backend/routes/quiz.py

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

@api_router.get("/dictionary/ai-search/{query}")
async def ai_search_dictionary(query: str, lang: str = "it"):
    """Use AI to search and generate a definition for any biblical term"""
    # First check if it exists in our static dictionary
    query_lower = query.lower()
    for key, term in BIBLICAL_DICTIONARY.items():
        if query_lower == term["term"].lower():
            return {"source": "dictionary", "term": translate_dict_term(term, key, lang)}
    
    # Check cache
    cached = await db.ai_dictionary_cache.find_one(
        {"query": query_lower, "language": lang}, {"_id": 0}
    )
    if cached:
        return {"source": "ai_cached", "term": cached["result"]}
    
    # Use AI to generate definition
    lang_names = {"it": "italiano", "en": "English", "es": "español", "de": "Deutsch", "fr": "français", "pt": "português"}
    lang_name = lang_names.get(lang, "italiano")
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"dict_search_{uuid.uuid4()}",
            system_message=f"Sei un esperto biblista. Rispondi SOLO in {lang_name}. Rispondi SEMPRE in formato JSON valido."
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""Cerca il termine biblico "{query}" e restituisci un JSON con questa struttura esatta:
{{
  "term": "{query}",
  "origin": "lingua di origine (ebraico/greco/aramaico)",
  "meaning": "significato breve in {lang_name}",
  "description": "descrizione dettagliata in {lang_name} (2-3 frasi)",
  "verses": [{{"ref": "Genesi 1:1", "text": "testo del versetto"}}],
  "found": true
}}
Se il termine non è biblico o non lo conosci, restituisci {{"found": false, "term": "{query}", "suggestion": "suggerimento alternativo"}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse AI response
        import re as regex
        json_match = regex.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = json.loads(json_match.group())
            if result.get("found", False):
                # Cache the result
                await db.ai_dictionary_cache.update_one(
                    {"query": query_lower, "language": lang},
                    {"$set": {"query": query_lower, "language": lang, "result": result, "created_at": datetime.now(timezone.utc)}},
                    upsert=True
                )
                return {"source": "ai", "term": result}
            else:
                return {"source": "ai", "term": result}
        
        return {"source": "ai", "term": {"found": False, "term": query, "suggestion": "Nessun risultato trovato"}}
    except Exception as e:
        logger.error(f"AI dictionary search error: {e}")
        raise HTTPException(status_code=500, detail="Errore nella ricerca AI")



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
    ).sort("created_at", -1).limit(200)
    
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
    ).sort("next_review", 1).limit(200)
    
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
async def global_search(q: str, lang: str = "it", user: User = Depends(require_auth)):
    """Global search across verses, books, chapters, dictionary, notes, bookmarks"""
    query_lower = q.lower().strip()
    results = {
        "verses": [],
        "books": [],
        "notes": [],
        "bookmarks": [],
        "dictionary": [],
    }
    
    # 1. Search Bible books (instant, from memory)
    books = BIBLE_BOOKS_MULTILANG.get(lang, BIBLE_BOOKS_MULTILANG["it"])
    for book in books:
        if query_lower in book["name"].lower() or query_lower in book["abbrev"].lower():
            results["books"].append({
                "type": "book",
                "name": book["name"],
                "chapters": book["chapters"],
                "abbrev": book["abbrev"],
            })
    
    # 2. Search cached Bible verses (from DB)
    if len(query_lower) >= 3:
        verses_cursor = db.bible_cache.find({
            "language": lang,
            "verses": {"$elemMatch": {"text": {"$regex": q, "$options": "i"}}}
        }, {"_id": 0, "book": 1, "chapter": 1, "verses": 1}).limit(10)
        
        async for doc in verses_cursor:
            book_name = doc.get("book", "")
            chapter_num = doc.get("chapter", 0)
            for v in doc.get("verses", []):
                if q.lower() in v.get("text", "").lower():
                    results["verses"].append({
                        "type": "verse",
                        "book": book_name,
                        "chapter": chapter_num,
                        "verse": v.get("verse", 0),
                        "text": v.get("text", "")[:150],
                        "ref": f"{book_name} {chapter_num}:{v.get('verse', 0)}",
                    })
                    if len(results["verses"]) >= 20:
                        break
            if len(results["verses"]) >= 20:
                break
    
    # 3. Search user's notes
    notes_cursor = db.study_notes.find({
        "user_id": user.user_id,
        "$or": [
            {"content": {"$regex": q, "$options": "i"}},
            {"verse_ref": {"$regex": q, "$options": "i"}}
        ]
    }, {"_id": 0}).limit(10)
    async for note in notes_cursor:
        results["notes"].append({
            "type": "note",
            "id": note.get("note_id", ""),
            "verse_ref": note.get("verse_ref", ""),
            "content": note.get("content", "")[:120],
        })
    
    # 4. Search user's bookmarks
    bookmarks_cursor = db.bookmarks.find({
        "user_id": user.user_id,
        "$or": [
            {"verse_ref": {"$regex": q, "$options": "i"}},
            {"text": {"$regex": q, "$options": "i"}}
        ]
    }, {"_id": 0}).limit(10)
    async for bm in bookmarks_cursor:
        results["bookmarks"].append({
            "type": "bookmark",
            "id": bm.get("bookmark_id", ""),
            "verse_ref": bm.get("verse_ref", ""),
            "text": bm.get("text", "")[:120],
        })
    
    # 5. Search dictionary (in source Italian + translated meanings)
    for key, term in BIBLICAL_DICTIONARY.items():
        matched = False
        display_term = term["term"]
        display_meaning = term["meaning"]
        
        # Check Italian source
        if (query_lower in term["term"].lower() or 
            query_lower in term["meaning"].lower()):
            matched = True
        
        # Check translated meaning/description for the requested language
        if not matched and lang != "it" and key in DICT_TERM_TRANSLATIONS:
            trans = DICT_TERM_TRANSLATIONS.get(key, {}).get(lang, {})
            trans_meaning = trans.get("meaning", "")
            trans_desc = trans.get("description", "")
            if (query_lower in trans_meaning.lower() or 
                query_lower in trans_desc.lower()):
                matched = True
        
        if matched:
            # Use translated meaning if available
            if lang != "it" and key in DICT_TERM_TRANSLATIONS:
                trans = DICT_TERM_TRANSLATIONS.get(key, {}).get(lang, {})
                if trans.get("meaning"):
                    display_meaning = trans["meaning"]
            
            results["dictionary"].append({
                "type": "dictionary",
                "id": key,
                "term": display_term,
                "meaning": display_meaning[:80],
            })
            if len(results["dictionary"]) >= 8:
                break
    
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
# Moved to /app/backend/routes/forum.py

# ==================== MAPPE BIBLICHE ====================
# Moved to /app/backend/routes/maps.py

# ==================== EVENTI LIVE ====================
# Moved to /app/backend/routes/events.py

# ==================== FAQ E AIUTO ====================
# Moved to /app/backend/routes/faq.py

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Amen! API", "version": "2.0.0", "features": ["multilang", "community", "translation"]}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# ==================== MINOR PROTECTION & PARENTAL CONTROLS ====================
# Moved to /app/backend/routes/parental_safety.py


# ==================== STUDY GROUPS ENDPOINTS ====================
# Moved to /app/backend/routes/study_groups.py

# APK Download endpoint
@api_router.get("/download/apk")
async def download_apk():
    """Download the Android APK file"""
    apk_path = ROOT_DIR / "static" / "amen_app.apk"
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK file not found")
    return FileResponse(
        path=str(apk_path),
        filename="Amen-Bible-App.apk",
        media_type="application/vnd.android.package-archive"
    )

# AAB Download endpoint
@api_router.get("/download/aab")
async def download_aab():
    """Download the Android App Bundle (AAB) file"""
    aab_path = ROOT_DIR / "static" / "amen_app.aab"
    if not aab_path.exists():
        raise HTTPException(status_code=404, detail="AAB file not found")
    return FileResponse(
        path=str(aab_path),
        filename="Amen-Bible-App.aab",
        media_type="application/octet-stream"
    )

# ==================== APP-ADS.TXT FOR ADMOB ====================
@app.get("/app-ads.txt")
async def get_app_ads_txt():
    """Serve app-ads.txt for AdMob verification"""
    return Response(
        content="google.com, pub-1876565863299921, DIRECT, f08c47fec0942fa0\n",
        media_type="text/plain"
    )

# ==================== DIGITAL ASSET LINKS (Android App Links) ====================
@app.get("/.well-known/assetlinks.json")
async def get_assetlinks():
    """Serve Digital Asset Links for Android App verification"""
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.amen.myapp",
                "sha256_cert_fingerprints": [
                    "DB:ED:7B:F3:4F:B8:F2:43:58:9F:84:6B:3F:D1:03:5B:8B:8C:99:C5:57:1B:97:9C:65:DC:1B:80:32:8A:9E:D9"
                ]
            }
        }
    ]

# ==================== CHILD SAFETY & FAMILIES POLICY ====================
@app.get("/child-safety-policy")
async def child_safety_policy():
    """Public child safety policy page for Google Play Families Policy compliance.
    No authentication required - accessible by Google Play reviewers."""
    return Response(content="""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Amen! - Child Safety Policy / Politica di Sicurezza per Minori</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;line-height:1.7}
h1{color:#4A7C59}h2{color:#5B8F6B;border-bottom:2px solid #e0e0e0;padding-bottom:8px}
.section{margin:24px 0;padding:16px;background:#f9f9f9;border-radius:12px;border-left:4px solid #4A7C59}
.warning{background:#fff3e0;border-left-color:#F39C12}
ul{padding-left:20px}li{margin:8px 0}
.badge{display:inline-block;background:#4A7C59;color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;margin:4px}
</style>
</head>
<body>
<h1>Amen! - Child Safety Policy</h1>
<p><strong>App:</strong> Amen! Bible Study App<br>
<strong>Package:</strong> com.amen.myapp<br>
<strong>Last Updated:</strong> April 2026<br>
<strong>Target Audience:</strong> All ages (with parental controls for minors)</p>

<h2>1. Safety Measures for Minors</h2>
<div class="section">
<p>Amen! implements comprehensive child safety protections:</p>
<ul>
<li><strong>Date of Birth Verification:</strong> Required at registration to identify minor users</li>
<li><strong>Parental PIN Required:</strong> All social features are <strong>disabled by default</strong> for minors. A parent or guardian must set a Parental Control PIN in Settings before any social interaction is possible</li>
<li><strong>Safety Reminder Every Session:</strong> Minors see a mandatory safety warning about real-world risks of online interaction before accessing any social features, every time they open the app</li>
<li><strong>Friends-Only Chat:</strong> Minors in "friends_only" mode cannot see or contact unknown users. The "Discover People" section is hidden</li>
<li><strong>No Personal Info Exchange:</strong> Minors are warned NOT to share personal information (address, school, phone, photos). Adult supervision is required through Parental Controls</li>
<li><strong>Content Moderation:</strong> Community posts are moderated for inappropriate content</li>
<li><strong>Study Groups Blocked:</strong> Minors cannot access group features without parental approval</li>
</ul>
</div>

<h2>2. Parental Controls</h2>
<div class="section">
<p>Parents and guardians have full control over their child's social experience:</p>
<ul>
<li><span class="badge">PIN Protected</span> A 4-digit PIN must be set by a parent to manage social settings</li>
<li><span class="badge">Enable/Disable</span> Social features can be completely enabled or disabled</li>
<li><span class="badge">Level Control</span> Choose between "Friends Only" (recommended for minors) or "All Users"</li>
<li><span class="badge">Media Sharing</span> Media/image sharing can be independently enabled or disabled</li>
</ul>
</div>

<h2>3. Data Collection for Minors</h2>
<div class="section warning">
<p><strong>Minimal Data Collection:</strong></p>
<ul>
<li>We collect only: name, email, date of birth (for age verification), and app usage data (reading progress, notes)</li>
<li>We do NOT collect: location, contacts, photos, device identifiers for advertising, or any data beyond what is necessary for app functionality</li>
<li>We do NOT use interest-based advertising for minor users</li>
<li>We do NOT share minor user data with third parties</li>
<li>Parents can request data deletion by contacting us</li>
</ul>
</div>

<h2>4. Educational Content</h2>
<div class="section">
<p>Amen! is a Bible study app designed to support spiritual education and growth:</p>
<ul>
<li>Bible reading in multiple languages (IT, EN, ES, PT, FR, DE)</li>
<li>Biblical dictionary with Hebrew/Greek/Aramaic terms</li>
<li>Interactive quizzes for Bible knowledge</li>
<li>Personal journal and study notes</li>
<li>Daily verse for reflection</li>
<li>All content is age-appropriate and promotes positive values</li>
</ul>
</div>

<h2>5. For Teachers and Educators</h2>
<div class="section">
<p>Amen! can be used in educational settings:</p>
<ul>
<li>Study groups allow supervised group Bible study (adults only by default, or with parental approval)</li>
<li>Reading progress tracking helps monitor engagement</li>
<li>Quiz system supports knowledge assessment</li>
<li>All social features can be disabled for classroom use via Parental Controls</li>
<li>No ads or in-app purchases disrupt the learning experience</li>
</ul>
</div>

<h2>6. Contact</h2>
<div class="section">
<p>For questions about our child safety practices:<br>
<strong>Email:</strong> support@cibospirituale.it<br>
<strong>Developer:</strong> Amen! App Team</p>
</div>

<h2>7. COPPA & GDPR-K Compliance</h2>
<div class="section">
<p>This app complies with the Children's Online Privacy Protection Act (COPPA) and GDPR provisions for children. We obtain verifiable parental consent through the Parental Controls PIN system before enabling any social or interactive features for users under 13 (or under 16 in applicable jurisdictions).</p>
</div>
</body>
</html>""", media_type="text/html")



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
