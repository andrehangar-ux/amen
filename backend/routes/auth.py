"""
Authentication routes:
- /auth/mobile-redirect (deep link bridge for OAuth callback)
- /auth/google-callback (Google OAuth via Emergent demo backend)
- /auth/register (email/password)
- /auth/login (email/password)
- /auth/forgot-password (sends reset code via Resend)
- /auth/reset-password (verifies code + updates password)
- /auth/me (current user)
- /auth/logout
- /auth/delete-account (GDPR-compliant full deletion)
"""
import asyncio
import hashlib
import random
import uuid
from datetime import datetime, timezone, timedelta

import httpx
import resend
from fastapi import HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse

from core import db, logger, SENDER_EMAIL, api_router
from models import (
    User,
    SessionDataResponse,
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from dependencies import require_auth


@api_router.get("/auth/mobile-redirect")
async def mobile_auth_redirect(request: Request):
    """Bridge page: reads session_id from hash fragment and redirects to app deep link."""
    scheme = request.query_params.get("scheme", "amen")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reindirizzamento...</title>
<style>body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#f5f5f0;color:#333;text-align:center}}
.loader{{border:4px solid #e0e0e0;border-top:4px solid #4A7C59;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 16px}}
@keyframes spin{{0%{{transform:rotate(0)}}100%{{transform:rotate(360deg)}}}}</style></head>
<body><div><div class="loader"></div><p>Accesso in corso...</p><p id="err" style="color:red;display:none"></p></div>
<script>
(function(){{
  var hash=window.location.hash.substring(1);
  var p=new URLSearchParams(hash);
  var sid=p.get('session_id');
  if(!sid){{var m=window.location.hash.match(/session_id=([^&]+)/);if(m)sid=m[1];}}
  if(sid){{window.location.href='{scheme}://auth-callback?session_id='+sid;setTimeout(function(){{document.getElementById('err').style.display='block';document.getElementById('err').textContent='Se l\\'app non si apre, torna all\\'app e riprova.';}},3000);}}
  else{{document.getElementById('err').style.display='block';document.getElementById('err').textContent='Sessione non trovata. Torna all\\'app e riprova.';}}
}})();
</script></body></html>"""
    return HTMLResponse(content=html)


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
        "birth_date": data.birth_date,
        "parental_consent": False,
        "safety_reminder_shown": False,
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


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        # Return success even if user not found (prevent email enumeration)
        return {"message": "Se l'email è registrata, riceverai un codice di reset."}

    # Check if user registered via Google (no password_hash)
    if not user.get("password_hash"):
        return {"message": "Se l'email è registrata, riceverai un codice di reset."}

    # Generate 6-digit reset code
    reset_code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Store reset token (upsert: one active token per email)
    await db.password_reset_tokens.update_one(
        {"email": data.email},
        {"$set": {
            "email": data.email,
            "code": reset_code,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
            "used": False
        }},
        upsert=True
    )

    # Send email via Resend
    html_content = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#f5f5f0;border-radius:12px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#4A7C59;font-size:28px;margin:0;">Amen!</h1>
        <p style="color:#666;margin-top:4px;">Reset Password</p>
      </div>
      <div style="background:#fff;padding:24px;border-radius:8px;text-align:center;">
        <p style="color:#333;font-size:16px;">Il tuo codice di verifica è:</p>
        <div style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#4A7C59;padding:16px;background:#f0f7f0;border-radius:8px;margin:16px 0;">
          {reset_code}
        </div>
        <p style="color:#888;font-size:14px;">Il codice scade tra 15 minuti.</p>
        <p style="color:#888;font-size:13px;margin-top:16px;">Se non hai richiesto il reset, ignora questa email.</p>
      </div>
    </div>
    """

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [data.email],
            "subject": "Amen! - Codice Reset Password",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Password reset email sent to {data.email}")
    except Exception as e:
        # Log internally but don't leak to user (privacy: no email enumeration)
        # and don't fail when 3rd-party email provider is unavailable or rate-limited.
        logger.error(f"Failed to send reset email to {data.email}: {e}")

    return {"message": "Se l'email è registrata, riceverai un codice di reset."}


@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    token = await db.password_reset_tokens.find_one(
        {"email": data.email, "code": data.code, "used": False},
        {"_id": 0}
    )

    if not token:
        raise HTTPException(status_code=400, detail="Codice non valido o scaduto")

    # Handle timezone-naive datetime from MongoDB
    expires_at = token["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Codice scaduto. Richiedine uno nuovo.")

    # Update password
    new_hash = hashlib.sha256(data.new_password.encode()).hexdigest()
    result = await db.users.update_one(
        {"email": data.email},
        {"$set": {"password_hash": new_hash}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # Mark token as used
    await db.password_reset_tokens.update_one(
        {"email": data.email, "code": data.code},
        {"$set": {"used": True}}
    )

    return {"message": "Password aggiornata con successo"}


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

        # Delete all user data from all collections
        await db.users.delete_one({"user_id": user_id})
        await db.user_sessions.delete_many({"user_id": user_id})
        await db.journal_entries.delete_many({"user_id": user_id})
        await db.community_messages.delete_many({"user_id": user_id})
        await db.user_notes.delete_many({"user_id": user_id})
        await db.reading_progress.delete_many({"user_id": user_id})
        await db.reading_history.delete_many({"user_id": user_id})
        await db.user_consent_log.delete_many({"user_id": user_id})
        await db.quiz_results.delete_many({"user_id": user_id})
        await db.bookmarks.delete_many({"user_id": user_id})
        await db.chat_history.delete_many({"user_id": user_id})
        await db.mood_checkins.delete_many({"user_id": user_id})
        await db.feelings_history.delete_many({"user_id": user_id})
        await db.private_messages.delete_many({"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]})
        await db.notifications.delete_many({"user_id": user_id})
        await db.group_members.delete_many({"user_id": user_id})
        await db.dictionary_favorites.delete_many({"user_id": user_id})
        await db.flashcards.delete_many({"user_id": user_id})

        logger.info(f"Account and all data deleted for user: {user_id}")

        return {"message": "Account e tutti i dati eliminati con successo"}
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail="Errore durante l'eliminazione dell'account")
