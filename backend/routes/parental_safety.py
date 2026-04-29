"""
Parental Controls and Safety routes:
- /safety/status, /safety/acknowledge-reminder, /safety/parental-consent, /safety/can-share-info
- /parental-controls/status, /set-pin, /verify-pin, /update, /can-use-social
- /users/birth-date
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Depends, Query
from pydantic import BaseModel

from core import db, SAFETY_MESSAGES, api_router
from models import User
from dependencies import require_auth, calculate_age, is_minor


# ==================== SAFETY ENDPOINTS ====================

@api_router.get("/safety/status")
async def get_safety_status(user: User = Depends(require_auth)):
    """Get user's minor status, safety settings and parental controls"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    birth_date = user_doc.get("birth_date")
    user_is_minor = is_minor(birth_date)
    age = calculate_age(birth_date)

    return {
        "is_minor": user_is_minor,
        "age": age,
        "birth_date": birth_date,
        "parental_consent": user_doc.get("parental_consent", False),
        "safety_reminder_shown": user_doc.get("safety_reminder_shown", False),
        "safety_message": SAFETY_MESSAGES.get(user_doc.get("language", "it"), SAFETY_MESSAGES["it"]) if user_is_minor else None,
        "parental_controls_enabled": user_doc.get("parental_controls_enabled", user_is_minor),
        "parent_pin_set": bool(user_doc.get("parent_pin")),
        "social_features_enabled": user_doc.get("social_features_enabled", False),
        "social_level": user_doc.get("social_level", "friends_only"),
        "media_sharing_enabled": user_doc.get("media_sharing_enabled", False)
    }


@api_router.post("/safety/acknowledge-reminder")
async def acknowledge_safety_reminder(user: User = Depends(require_auth)):
    """Mark safety reminder as shown to user"""
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"safety_reminder_shown": True}}
    )
    return {"success": True, "message": "Promemoria di sicurezza confermato"}


class ParentalConsentRequest(BaseModel):
    consent_code: str
    consent_given: bool


@api_router.post("/safety/parental-consent")
async def set_parental_consent(data: ParentalConsentRequest, user: User = Depends(require_auth)):
    """Set parental consent for a minor user"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    stored_code = user_doc.get("parental_consent_code")

    if not stored_code:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "parental_consent_code": data.consent_code,
                "parental_consent": data.consent_given,
                "parental_consent_date": datetime.now(timezone.utc)
            }}
        )
        return {"success": True, "message": "Codice di controllo genitori impostato"}

    if stored_code != data.consent_code:
        raise HTTPException(status_code=403, detail="Codice di controllo genitori non valido")

    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "parental_consent": data.consent_given,
            "parental_consent_date": datetime.now(timezone.utc)
        }}
    )
    return {"success": True, "message": "Consenso genitoriale aggiornato"}


@api_router.get("/safety/can-share-info")
async def can_share_personal_info(user: User = Depends(require_auth)):
    """Check if user can share personal information (requires parental consent if minor)"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    birth_date = user_doc.get("birth_date")
    user_is_minor = is_minor(birth_date)

    if not user_is_minor:
        return {"can_share": True, "reason": "adult"}

    parental_consent = user_doc.get("parental_consent", False)
    return {
        "can_share": parental_consent,
        "reason": "parental_consent_given" if parental_consent else "parental_consent_required",
        "message": "Richiedi il permesso di un genitore per condividere informazioni personali." if not parental_consent else None
    }


# ==================== PARENTAL CONTROLS ====================

class ParentalControlsRequest(BaseModel):
    parent_pin: str
    social_features_enabled: Optional[bool] = None
    social_level: Optional[str] = None
    media_sharing_enabled: Optional[bool] = None


class SetParentPinRequest(BaseModel):
    new_pin: str


@api_router.get("/parental-controls/status")
async def get_parental_controls_status(user: User = Depends(require_auth)):
    """Get current parental control settings for a user"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    birth_date = user_doc.get("birth_date")
    user_is_minor = is_minor(birth_date)

    return {
        "is_minor": user_is_minor,
        "age": calculate_age(birth_date),
        "parental_controls_enabled": user_doc.get("parental_controls_enabled", user_is_minor),
        "parent_pin_set": bool(user_doc.get("parent_pin")),
        "social_features_enabled": user_doc.get("social_features_enabled", False),
        "social_level": user_doc.get("social_level", "friends_only"),
        "media_sharing_enabled": user_doc.get("media_sharing_enabled", False),
        "parental_consent": user_doc.get("parental_consent", False),
        "safety_reminder_shown": user_doc.get("safety_reminder_shown", False)
    }


@api_router.post("/parental-controls/set-pin")
async def set_parent_pin(data: SetParentPinRequest, user: User = Depends(require_auth)):
    """Set or update the parental control PIN"""
    if not data.new_pin.isdigit() or len(data.new_pin) < 4 or len(data.new_pin) > 6:
        raise HTTPException(status_code=400, detail="Il PIN deve essere di 4-6 cifre")

    pin_hash = hashlib.sha256(data.new_pin.encode()).hexdigest()

    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "parent_pin": pin_hash,
            "parental_controls_enabled": True,
            "pin_set_date": datetime.now(timezone.utc)
        }}
    )

    return {"success": True, "message": "PIN controllo genitori impostato"}


@api_router.post("/parental-controls/verify-pin")
async def verify_parent_pin(pin: str = Query(...), user: User = Depends(require_auth)):
    """Verify the parental control PIN"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    stored_hash = user_doc.get("parent_pin")
    if not stored_hash:
        raise HTTPException(status_code=400, detail="Nessun PIN impostato")

    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    if pin_hash != stored_hash:
        raise HTTPException(status_code=403, detail="PIN non valido")

    return {"success": True, "verified": True}


@api_router.put("/parental-controls/update")
async def update_parental_controls(data: ParentalControlsRequest, user: User = Depends(require_auth)):
    """Update parental control settings (requires PIN verification)"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    stored_hash = user_doc.get("parent_pin")
    if stored_hash:
        pin_hash = hashlib.sha256(data.parent_pin.encode()).hexdigest()
        if pin_hash != stored_hash:
            raise HTTPException(status_code=403, detail="PIN non valido")

    update_fields = {}
    if data.social_features_enabled is not None:
        update_fields["social_features_enabled"] = data.social_features_enabled
    if data.social_level is not None:
        if data.social_level not in ["disabled", "friends_only", "all"]:
            raise HTTPException(status_code=400, detail="Livello social non valido")
        update_fields["social_level"] = data.social_level
    if data.media_sharing_enabled is not None:
        update_fields["media_sharing_enabled"] = data.media_sharing_enabled

    if update_fields:
        update_fields["parental_controls_updated"] = datetime.now(timezone.utc)
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": update_fields}
        )

    return {"success": True, "message": "Impostazioni controllo genitori aggiornate"}


@api_router.get("/parental-controls/can-use-social")
async def can_use_social_features(user: User = Depends(require_auth)):
    """Check if user can use social features based on parental controls"""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    birth_date = user_doc.get("birth_date")
    user_is_minor = is_minor(birth_date)

    if not user_is_minor:
        return {
            "can_use_social": True,
            "social_level": "all",
            "media_sharing": True,
            "reason": "adult",
            "is_minor": False,
            "parent_pin_set": False
        }

    parent_pin_set = bool(user_doc.get("parent_pin"))
    if not parent_pin_set:
        return {
            "can_use_social": False,
            "social_level": "disabled",
            "media_sharing": False,
            "reason": "no_parent_pin",
            "is_minor": True,
            "parent_pin_set": False,
            "message": "Un genitore deve prima impostare un PIN di controllo nelle Impostazioni per abilitare le funzionalità social."
        }

    social_enabled = user_doc.get("social_features_enabled", False)
    social_level = user_doc.get("social_level", "friends_only")
    media_sharing = user_doc.get("media_sharing_enabled", False)

    if not social_enabled or social_level == "disabled":
        return {
            "can_use_social": False,
            "social_level": "disabled",
            "media_sharing": False,
            "reason": "parental_controls_disabled",
            "is_minor": True,
            "parent_pin_set": True,
            "message": "Le funzionalità social sono state disabilitate dal controllo genitori. Chiedi a un genitore di modificare le impostazioni."
        }

    return {
        "can_use_social": True,
        "social_level": social_level,
        "media_sharing": media_sharing,
        "reason": "parental_controls_allowed",
        "is_minor": True,
        "parent_pin_set": True
    }


@api_router.put("/users/birth-date")
async def update_birth_date(birth_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"), user: User = Depends(require_auth)):
    """Update user's birth date"""
    try:
        datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD")

    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"birth_date": birth_date}}
    )

    if is_minor(birth_date):
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"parental_consent": False, "safety_reminder_shown": False}}
        )

    return {"success": True, "birth_date": birth_date, "is_minor": is_minor(birth_date)}
