"""
Legal, Consent, Policy & Donations routes:
- /consent/status, /consent/accept, /consent/withdraw
- /policy/check
- /donations/config, /donations (POST + GET)
"""
import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Depends, Request, Query

from core import db, api_router
from models import User, DonationRequest
from dependencies import require_auth


# ==================== LEGAL & CONSENT ====================

@api_router.get("/consent/status")
async def get_consent_status(user: User = Depends(require_auth)):
    """Check if user has accepted terms and conditions"""
    consent = await db.consent_logs.find_one(
        {"user_id": user.user_id},
        {"_id": 0, "user_id": 0}
    )
    if consent:
        return {"accepted": True, "version": consent.get("version"), "accepted_at": consent.get("timestamp")}
    return {"accepted": False}


@api_router.post("/consent/accept")
async def accept_terms(
    version: str = Query(...),
    user: User = Depends(require_auth),
    request: Request = None
):
    """Log user acceptance of terms and conditions (Click-wrap protocol)"""
    now = datetime.now(timezone.utc)

    doc_hash = hashlib.sha256(f"amen_legal_v{version}_{now.isoformat()}".encode()).hexdigest()

    client_ip = request.client.host if request and request.client else "unknown"
    ip_parts = client_ip.split('.')
    masked_ip = '.'.join(ip_parts[:3] + ['xxx']) if len(ip_parts) == 4 else "masked"

    consent_record = {
        "user_id": user.user_id,
        "version": version,
        "timestamp": now,
        "document_hash": doc_hash,
        "ip_masked": masked_ip,
        "user_agent": request.headers.get("user-agent", "unknown") if request else "unknown",
        "consent_type": "click-wrap",
        "pre_tick": False,
    }

    await db.consent_logs.update_one(
        {"user_id": user.user_id},
        {"$set": consent_record},
        upsert=True
    )

    return {
        "success": True,
        "version": version,
        "document_hash": doc_hash,
        "timestamp": now.isoformat()
    }


@api_router.delete("/consent/withdraw")
async def withdraw_consent(user: User = Depends(require_auth)):
    """Withdraw consent and request data deletion (GDPR Art. 17)"""
    await db.consent_logs.delete_one({"user_id": user.user_id})
    return {"success": True, "message": "Consent withdrawn. Contact andrehangar@live.it for complete data deletion."}


@api_router.get("/policy/check")
async def check_policy_violation(content: str = Query(...)):
    """Check content for policy violations - returns 403 if violated"""
    prohibited_patterns = ["reverse engineer", "scrape model", "extract algorithm"]
    content_lower = content.lower()

    for pattern in prohibited_patterns:
        if pattern in content_lower:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "POLICY_VIOLATION_403",
                    "reason": f"Content violates policy: {pattern}",
                    "legal_reference": "T&C Section 2 - Explicit Prohibitions"
                }
            )

    return {"status": "ok", "content_cleared": True}


# ==================== DONATIONS ====================

DONATION_CONFIG = {
    "paypal_email": "andrehangar@live.it",
    "paypal_link": "https://www.paypal.com/paypalme/andrehangar",
    "iban": "IT46 I036 6901 6008 5802 8558 932",
    "intestatario": "Andrea Confortino",
    "banca": "Revolut Bank UAB",
    "bic_swift": "REVOITM2",
    "bic_corrispondente": "CHASDEFX",
    "indirizzo_banca": "Via Dante 7, 20123, Milano (MI), Italy"
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
