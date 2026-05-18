"""
Generate translated chapter titles for famous Bible chapters that are missing
from `bible_titles.py CHAPTER_TITLES`. Uses gpt-4o-mini to produce titles in
6 languages (it/en/es/pt/fr/de) in a single batch call.

Run with: python3 generate_chapter_titles.py
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage
from bible_titles import CHAPTER_TITLES

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
OUTPUT = '/tmp/new_chapter_titles.json'
BATCH_SIZE = 12
LLM_TIMEOUT = 60

# Famous chapters to add (book_italian, chapter, hint).
# Hint helps the LLM pick the historically standard title.
FAMOUS_CHAPTERS = [
    # ----- Pentateuco -----
    ("Genesi", 4, "Cain and Abel"),
    ("Genesi", 8, "End of the Flood"),
    ("Genesi", 9, "Covenant with Noah"),
    ("Genesi", 15, "Covenant with Abraham"),
    ("Genesi", 17, "Circumcision Covenant"),
    ("Genesi", 18, "Three Visitors at Mamre"),
    ("Genesi", 19, "Sodom and Gomorrah"),
    ("Genesi", 21, "Birth of Isaac"),
    ("Genesi", 24, "Isaac and Rebekah"),
    ("Genesi", 25, "Esau and Jacob"),
    ("Genesi", 27, "Jacob's Blessing"),
    ("Genesi", 28, "Jacob's Ladder"),
    ("Genesi", 32, "Wrestling at Peniel"),
    ("Genesi", 37, "Joseph Sold by His Brothers"),
    ("Genesi", 39, "Joseph and Potiphar"),
    ("Genesi", 41, "Pharaoh's Dreams"),
    ("Genesi", 45, "Joseph Reveals Himself"),
    ("Genesi", 50, "Death of Joseph"),
    ("Esodo", 1, "Slavery in Egypt"),
    ("Esodo", 2, "Birth of Moses"),
    ("Esodo", 4, "Moses's Signs"),
    ("Esodo", 7, "First Plagues"),
    ("Esodo", 12, "Passover and Exodus"),
    ("Esodo", 13, "Consecration of the Firstborn"),
    ("Esodo", 15, "Song of Moses"),
    ("Esodo", 16, "Manna from Heaven"),
    ("Esodo", 17, "Water from the Rock"),
    ("Esodo", 19, "At Mount Sinai"),
    ("Esodo", 24, "The Covenant Confirmed"),
    ("Esodo", 32, "The Golden Calf"),
    ("Esodo", 33, "God's Glory"),
    ("Esodo", 40, "Setting up the Tabernacle"),
    ("Levitico", 16, "Day of Atonement (Yom Kippur)"),
    ("Levitico", 19, "Laws of Holiness"),
    ("Levitico", 23, "Feasts of the Lord"),
    ("Levitico", 26, "Blessings and Curses"),
    ("Numeri", 13, "The Twelve Spies"),
    ("Numeri", 14, "Israel's Rebellion"),
    ("Numeri", 20, "Waters of Meribah"),
    ("Numeri", 21, "The Bronze Serpent"),
    ("Numeri", 22, "Balaam and the Donkey"),
    ("Deuteronomio", 5, "The Ten Commandments Renewed"),
    ("Deuteronomio", 6, "The Shema"),
    ("Deuteronomio", 28, "Blessings and Curses of the Covenant"),
    ("Deuteronomio", 34, "Death of Moses"),
    # ----- Storici -----
    ("Giosuè", 1, "Joshua's Commission"),
    ("Giosuè", 3, "Crossing the Jordan"),
    ("Giosuè", 10, "The Sun Stands Still"),
    ("Giosuè", 24, "Joshua's Farewell"),
    ("Giudici", 4, "Deborah and Barak"),
    ("Giudici", 6, "Call of Gideon"),
    ("Giudici", 7, "Gideon's 300"),
    ("Giudici", 13, "Birth of Samson"),
    ("Giudici", 16, "Samson and Delilah"),
    ("Rut", 1, "Ruth's Loyalty"),
    ("Rut", 4, "Boaz Marries Ruth"),
    ("1 Samuele", 1, "Hannah's Prayer"),
    ("1 Samuele", 3, "Call of Samuel"),
    ("1 Samuele", 8, "Israel Asks for a King"),
    ("1 Samuele", 16, "David Anointed King"),
    ("1 Samuele", 18, "David and Jonathan"),
    ("2 Samuele", 6, "Ark Brought to Jerusalem"),
    ("2 Samuele", 7, "Davidic Covenant"),
    ("2 Samuele", 11, "David and Bathsheba"),
    ("2 Samuele", 12, "Nathan Rebukes David"),
    ("2 Samuele", 22, "David's Song of Praise"),
    ("1 Re", 6, "Building of the Temple"),
    ("1 Re", 8, "Dedication of the Temple"),
    ("1 Re", 17, "Elijah and the Widow"),
    ("1 Re", 18, "Elijah on Mount Carmel"),
    ("1 Re", 19, "The Still Small Voice"),
    ("2 Re", 2, "Elijah Taken Up to Heaven"),
    ("2 Re", 5, "Naaman the Leper Healed"),
    ("2 Re", 22, "Josiah's Reform"),
    # ----- Sapienziali -----
    ("Giobbe", 1, "Job's Trials Begin"),
    ("Giobbe", 38, "The Lord Answers Job"),
    ("Giobbe", 42, "Job's Restoration"),
    ("Salmi", 8, "Glory of God in Creation"),
    ("Salmi", 19, "The Heavens Declare"),
    ("Salmi", 27, "The Lord, My Light"),
    ("Salmi", 32, "Blessed Is Forgiveness"),
    ("Salmi", 34, "Taste and See the Lord"),
    ("Salmi", 37, "Trust in the Lord"),
    ("Salmi", 42, "As the Deer Pants"),
    ("Salmi", 46, "God Is Our Refuge"),
    ("Salmi", 63, "Thirsting for God"),
    ("Salmi", 73, "The Prosperity of the Wicked"),
    ("Salmi", 84, "Longing for God's House"),
    ("Salmi", 90, "Teach Us to Number Our Days"),
    ("Salmi", 95, "Come, Let Us Sing"),
    ("Salmi", 100, "A Psalm of Thanksgiving"),
    ("Salmi", 103, "Bless the Lord, O My Soul"),
    ("Salmi", 110, "The Lord's Priest-King"),
    ("Salmi", 117, "The Shortest Psalm"),
    ("Salmi", 121, "The Lord Watches Over You"),
    ("Salmi", 127, "Unless the Lord Builds"),
    ("Salmi", 130, "Out of the Depths"),
    ("Salmi", 133, "Brothers Dwelling in Unity"),
    ("Salmi", 139, "Searched and Known"),
    ("Salmi", 145, "Greatness of God"),
    ("Salmi", 150, "Final Hallelujah"),
    ("Proverbi", 1, "The Beginning of Wisdom"),
    ("Proverbi", 3, "Trust in the Lord"),
    ("Proverbi", 8, "The Call of Wisdom"),
    ("Ecclesiaste", 12, "Remember Your Creator"),
    ("Cantico dei Cantici", 1, "Song of Songs"),
    # ----- Profeti maggiori -----
    ("Isaia", 6, "Call of Isaiah"),
    ("Isaia", 7, "Sign of Emmanuel"),
    ("Isaia", 9, "Prince of Peace"),
    ("Isaia", 11, "The Branch from Jesse"),
    ("Isaia", 40, "Comfort My People"),
    ("Isaia", 55, "Invitation to Salvation"),
    ("Isaia", 61, "Year of the Lord's Favor"),
    ("Geremia", 1, "Call of Jeremiah"),
    ("Geremia", 18, "The Potter's House"),
    ("Geremia", 29, "Letter to the Exiles"),
    ("Geremia", 31, "New Covenant"),
    ("Lamentazioni", 3, "Mercies Renewed Every Morning"),
    ("Ezechiele", 1, "Vision of God's Glory"),
    ("Ezechiele", 36, "A New Heart"),
    ("Ezechiele", 37, "Valley of Dry Bones"),
    ("Daniele", 1, "Daniel in Babylon"),
    ("Daniele", 2, "Nebuchadnezzar's Statue"),
    ("Daniele", 4, "Nebuchadnezzar's Humiliation"),
    ("Daniele", 5, "Belshazzar's Feast"),
    ("Daniele", 7, "Vision of Four Beasts"),
    ("Daniele", 9, "The Seventy Weeks"),
    # ----- Profeti minori -----
    ("Osea", 1, "Hosea and Gomer"),
    ("Osea", 11, "God's Love for Israel"),
    ("Gioele", 2, "Outpouring of the Spirit"),
    ("Amos", 5, "Let Justice Roll Down"),
    ("Abdia", 1, "Fall of Edom"),
    ("Giona", 2, "Jonah's Prayer"),
    ("Giona", 3, "Nineveh Repents"),
    ("Giona", 4, "Jonah and the Plant"),
    ("Michea", 5, "The Ruler from Bethlehem"),
    ("Michea", 6, "What the Lord Requires"),
    ("Abacuc", 2, "The Just Shall Live by Faith"),
    ("Aggeo", 1, "Rebuild the Temple"),
    ("Zaccaria", 9, "The Coming King"),
    ("Malachia", 3, "The Messenger of the Covenant"),
    ("Malachia", 4, "The Sun of Righteousness"),
    # ----- Vangeli -----
    ("Matteo", 3, "Baptism of Jesus"),
    ("Matteo", 4, "Temptation in the Wilderness"),
    ("Matteo", 7, "End of the Sermon on the Mount"),
    ("Matteo", 13, "Parables of the Kingdom"),
    ("Matteo", 16, "Peter's Confession"),
    ("Matteo", 17, "The Transfiguration"),
    ("Matteo", 21, "Triumphal Entry into Jerusalem"),
    ("Matteo", 24, "The Olivet Discourse"),
    ("Matteo", 25, "Parables of the Last Days"),
    ("Marco", 1, "Beginning of the Gospel"),
    ("Marco", 4, "Parables and the Stilled Storm"),
    ("Marco", 5, "Demons and Healings"),
    ("Marco", 6, "Feeding the Five Thousand"),
    ("Marco", 14, "The Last Supper"),
    ("Marco", 15, "Crucifixion of Jesus"),
    ("Marco", 16, "The Resurrection"),
    ("Luca", 1, "The Annunciation"),
    ("Luca", 2, "The Nativity"),
    ("Luca", 4, "Jesus in Nazareth"),
    ("Luca", 10, "The Good Samaritan"),
    ("Luca", 11, "The Lord's Prayer"),
    ("Luca", 15, "The Prodigal Son"),
    ("Luca", 16, "The Rich Man and Lazarus"),
    ("Luca", 19, "Zacchaeus"),
    ("Luca", 22, "The Last Supper"),
    ("Luca", 23, "The Crucifixion"),
    ("Luca", 24, "On the Road to Emmaus"),
    ("Giovanni", 1, "The Word Became Flesh"),
    ("Giovanni", 3, "Nicodemus and the New Birth"),
    ("Giovanni", 4, "Woman at the Well"),
    ("Giovanni", 6, "The Bread of Life"),
    ("Giovanni", 8, "The Woman Caught in Adultery"),
    ("Giovanni", 10, "The Good Shepherd"),
    ("Giovanni", 11, "The Raising of Lazarus"),
    ("Giovanni", 13, "The Washing of Feet"),
    ("Giovanni", 14, "I Am the Way"),
    ("Giovanni", 15, "The True Vine"),
    ("Giovanni", 17, "Jesus' High Priestly Prayer"),
    ("Giovanni", 19, "The Crucifixion"),
    ("Giovanni", 20, "The Resurrection"),
    ("Giovanni", 21, "Jesus and Peter"),
    # ----- Atti e Lettere -----
    ("Atti", 1, "The Ascension"),
    ("Atti", 2, "Pentecost"),
    ("Atti", 7, "Stephen's Speech and Martyrdom"),
    ("Atti", 9, "Conversion of Saul"),
    ("Atti", 10, "Cornelius and Peter"),
    ("Atti", 13, "First Missionary Journey"),
    ("Atti", 15, "The Jerusalem Council"),
    ("Atti", 17, "Paul in Athens"),
    ("Atti", 27, "Paul's Shipwreck"),
    ("Romani", 1, "Gospel of Power"),
    ("Romani", 3, "Justification by Faith"),
    ("Romani", 5, "Peace with God"),
    ("Romani", 6, "Dead to Sin, Alive in Christ"),
    ("Romani", 7, "Struggle with Sin"),
    ("Romani", 8, "Life in the Spirit"),
    ("Romani", 12, "Living Sacrifices"),
    ("Romani", 13, "Submission to Authorities"),
    ("1 Corinzi", 11, "The Lord's Supper"),
    ("1 Corinzi", 12, "Spiritual Gifts"),
    ("1 Corinzi", 13, "The Hymn of Love"),
    ("1 Corinzi", 15, "The Resurrection of Christ"),
    ("2 Corinzi", 5, "New Creation in Christ"),
    ("2 Corinzi", 9, "Cheerful Giving"),
    ("Galati", 3, "Sons of God by Faith"),
    ("Galati", 5, "The Fruit of the Spirit"),
    ("Efesini", 2, "Saved by Grace"),
    ("Efesini", 5, "Christian Households"),
    ("Efesini", 6, "The Armor of God"),
    ("Filippesi", 2, "The Kenosis Hymn"),
    ("Filippesi", 4, "Rejoice in the Lord"),
    ("Colossesi", 1, "The Supremacy of Christ"),
    ("Colossesi", 3, "New Life in Christ"),
    ("1 Tessalonicesi", 4, "The Coming of the Lord"),
    ("1 Tessalonicesi", 5, "The Day of the Lord"),
    ("2 Tessalonicesi", 2, "The Man of Lawlessness"),
    ("1 Timoteo", 3, "Qualifications for Overseers"),
    ("2 Timoteo", 3, "Last Days and Scripture"),
    ("2 Timoteo", 4, "Paul's Final Charge"),
    ("Ebrei", 1, "The Supremacy of the Son"),
    ("Ebrei", 4, "The Sabbath Rest"),
    ("Ebrei", 9, "Christ Our High Priest"),
    ("Ebrei", 11, "The Heroes of Faith"),
    ("Ebrei", 12, "Discipline of the Lord"),
    ("Giacomo", 1, "Trials and Wisdom"),
    ("Giacomo", 2, "Faith and Works"),
    ("Giacomo", 3, "Taming the Tongue"),
    ("Giacomo", 5, "The Prayer of Faith"),
    ("1 Pietro", 1, "Living Hope"),
    ("1 Pietro", 2, "Living Stones"),
    ("2 Pietro", 3, "The Day of the Lord"),
    ("1 Giovanni", 1, "God Is Light"),
    ("1 Giovanni", 3, "Children of God"),
    ("1 Giovanni", 4, "God Is Love"),
    ("1 Giovanni", 5, "Faith That Overcomes"),
    ("Giuda", 1, "Contending for the Faith"),
    ("Apocalisse", 1, "Vision of the Risen Christ"),
    ("Apocalisse", 2, "Letters to the Seven Churches I"),
    ("Apocalisse", 3, "Letters to the Seven Churches II"),
    ("Apocalisse", 4, "The Throne of God"),
    ("Apocalisse", 5, "The Lamb of God"),
    ("Apocalisse", 6, "The Seven Seals"),
    ("Apocalisse", 12, "The Woman and the Dragon"),
    ("Apocalisse", 13, "The Beast"),
    ("Apocalisse", 19, "The Marriage of the Lamb"),
    ("Apocalisse", 20, "The Millennium and Final Judgment"),
    ("Apocalisse", 21, "The New Jerusalem"),
    ("Apocalisse", 22, "The Water of Life"),
]

SYSTEM = """Sei un esperto biblista. Per ogni capitolo, fornisci il titolo SEZIONE STANDARD comunemente usato nelle Bibbie storiche di pubblico dominio (Diodati/Riveduta IT, KJV/WEB EN, Reina-Valera ES, Almeida PT, Louis Segond FR, Luther DE).
INPUT: JSON array di {book, chapter, hint}.
OUTPUT: JSON array con stesso ordine e stessi campi `book` e `chapter`, e in più: `it`, `en`, `es`, `pt`, `fr`, `de` con il titolo TRADIZIONALE conciso (max 60 caratteri ognuno).
- Stile: titolo breve, sostantivato (es. "La Creazione", non "Cosa è creato"). Niente articoli iniziali rimossi se servono per scorrevolezza.
- Apostrofi: usa quelli tipografici corretti per ogni lingua (es. it: "L'Annunciazione", en: "The Lord's Prayer").
- Rispondi SOLO con il JSON array, senza commenti, senza markdown."""


async def batch_call(batch_id: int, batch: list) -> list:
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"titles_batch_{batch_id}",
        system_message=SYSTEM,
    ).with_model("openai", "gpt-4o-mini")
    payload = json.dumps([
        {"book": b, "chapter": c, "hint": h} for b, c, h in batch
    ], ensure_ascii=False)
    resp = await chat.send_message(UserMessage(text=payload))
    txt = resp.strip()
    txt = re.sub(r'^```(?:json)?\s*', '', txt)
    txt = re.sub(r'\s*```$', '', txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        print(f"[batch {batch_id}] parse fail: {e}. Raw: {txt[:200]}", flush=True)
        return []


async def main():
    # Filter out already-present chapters
    existing = set(CHAPTER_TITLES.keys())
    to_generate = [(b, c, h) for (b, c, h) in FAMOUS_CHAPTERS if (b, c) not in existing]
    print(f"Capitoli famosi totali: {len(FAMOUS_CHAPTERS)}")
    print(f"Già presenti: {len(FAMOUS_CHAPTERS) - len(to_generate)}")
    print(f"Da generare: {len(to_generate)}", flush=True)

    batches = [to_generate[i:i + BATCH_SIZE] for i in range(0, len(to_generate), BATCH_SIZE)]
    print(f"Batches: {len(batches)} da {BATCH_SIZE}", flush=True)

    all_results = []
    for i, batch in enumerate(batches):
        print(f"[batch {i+1}/{len(batches)}] {len(batch)} capitoli", flush=True)
        try:
            result = await asyncio.wait_for(batch_call(i, batch), timeout=LLM_TIMEOUT)
            all_results.extend(result)
        except asyncio.TimeoutError:
            print(f"[batch {i+1}] TIMEOUT", flush=True)
        # Incremental save
        Path(OUTPUT).write_text(json.dumps(all_results, ensure_ascii=False, indent=2))

    print(f"\n✓ Generate {len(all_results)} titoli. Salvato in {OUTPUT}", flush=True)


if __name__ == '__main__':
    asyncio.run(main())
