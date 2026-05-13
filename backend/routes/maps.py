"""
Biblical maps endpoints.

Provides static biblical map data (Palestine, Exodus, Paul's journeys, Jesus'
ministry) plus an AI-augmented per-location description endpoint.
"""
from fastapi import HTTPException
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import api_router, EMERGENT_LLM_KEY


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
        ],
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
        ],
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
        ],
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
        ],
    },
}


@api_router.get("/maps")
async def get_available_maps():
    """Get list of available biblical maps"""
    return [
        {
            "id": map_data["id"],
            "name": map_data["name"],
            "description": map_data["description"],
            "locations_count": len(map_data["locations"]),
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
            system_message="Sei una guida biblica esperta. Fornisci informazioni storiche e bibliche sui luoghi.",
        ).with_model("openai", "gpt-4o")

        response = await chat.send_message(UserMessage(
            text=f"Parlami del luogo biblico '{location['name']}' in modo breve ma informativo. Includi eventi biblici importanti e versetti chiave."
        ))

        return {**location, "detailed_description": response}
    except Exception:
        return {**location, "detailed_description": location["description"]}
