"""
FAQ and support contact endpoints.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import Depends, Request

from core import api_router, db
from dependencies import require_auth
from models import User


FAQ_DATA = [
    {
        "id": "faq1",
        "category": "generale",
        "question": "Cos'è Amen!?",
        "answer": "Amen! è un'app cristiana evangelica per la crescita spirituale. Include lettura della Bibbia (Nuova Diodati e Reina Valera), assistente AI spirituale, diario personale, quiz biblici, dizionario dei termini antichi, e una comunità di credenti.",
    },
    {
        "id": "faq2",
        "category": "bibbia",
        "question": "Quali traduzioni bibliche sono disponibili?",
        "answer": "L'app include la Nuova Diodati (italiano) e Reina Valera 1960 (spagnolo). Altre traduzioni saranno aggiunte in futuro.",
    },
    {
        "id": "faq3",
        "category": "account",
        "question": "Come posso cancellare il mio account?",
        "answer": "Puoi richiedere la cancellazione del tuo account contattandoci a andrehangar@live.it. I tuoi dati saranno rimossi entro 30 giorni.",
    },
    {
        "id": "faq4",
        "category": "donazioni",
        "question": "Come posso sostenere l'app?",
        "answer": "Puoi fare una donazione tramite PayPal (andrehangar@live.it) o bonifico bancario. Le donazioni aiutano a mantenere l'app gratuita e ad aggiungere nuove funzionalità.",
    },
    {
        "id": "faq5",
        "category": "community",
        "question": "Come funziona il forum?",
        "answer": "Il forum permette di discutere, condividere testimonianze, fare domande bibliche e richiedere preghiere. Un mentore AI modera le discussioni per mantenere un ambiente rispettoso.",
    },
    {
        "id": "faq6",
        "category": "studio",
        "question": "Cosa sono i quiz biblici?",
        "answer": "I quiz biblici sono test interattivi per verificare e approfondire la tua conoscenza della Bibbia. Ogni risposta include spiegazioni e riferimenti ai versetti.",
    },
    {
        "id": "faq7",
        "category": "studio",
        "question": "Come funziona il dizionario biblico?",
        "answer": "Il dizionario spiega i termini originali ebraici e greci con le loro radici semantiche, pronuncia, significato e versetti di riferimento.",
    },
    {
        "id": "faq8",
        "category": "eventi",
        "question": "Cosa sono gli eventi live?",
        "answer": "Gli eventi live permettono di partecipare a letture bibliche sincronizzate, momenti di lode e preghiera comunitaria con altri utenti dell'app.",
    },
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
        "eventi": "Eventi",
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
        "created_at": datetime.now(timezone.utc),
    }

    await db.support_tickets.insert_one(support_ticket)

    return {
        "success": True,
        "message": "Messaggio inviato! Ti risponderemo presto.",
        "ticket_id": support_ticket["ticket_id"],
    }
