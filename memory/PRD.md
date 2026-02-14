# Amen! - PWA Cristiana Multilingua

## Problema Originale
App cristiana PWA "Amen!" con lettore biblico multilingua, quiz, dizionario biblico, strumenti di studio AI, diario spirituale e radio.

## Architettura
- **Backend**: FastAPI + MongoDB (Motor) - `/app/backend/server.py`
- **Frontend**: React Native + Expo + Expo Router + TypeScript + Zustand
- **Database**: MongoDB `test_database`
- **AI**: OpenAI GPT-4o via Emergent LLM Key

## Lingue Supportate
it, en, es, de, fr, pt (6 lingue con TTS)

## Cosa è stato implementato

### Sessione Corrente (Feb 2026) - Fork 11

#### ✅ TRADUZIONE ON-DEMAND QUIZ 1000 DOMANDE (COMPLETATO)
- [x] Sistema traduzione on-demand per 1000 domande
- [x] Cache traduzioni in `/app/backend/quiz_translations_cache.json`
- [x] Traduzione via OpenAI GPT-4o
- [x] Tutti i 6 linguaggi supportati (it, es, en, de, fr, pt)
- [x] Titoli categorie tradotti automaticamente
- [x] Domande e opzioni tradotte on-demand (prima richiesta)
- [x] Testato con testing agent: 100% backend (13/13 test)

#### ✅ STATISTICHE E CORREZIONI QUIZ (COMPLETATO)
- [x] Endpoint `/api/quiz/submit` supporta quiz tematici e classici
- [x] Risposta include: score, correct_count, total, results[], feedback
- [x] Ogni risultato contiene: question_id, is_correct, correct_answer, user_answer, explanation, verse_ref
- [x] UI risultati in `quiz.tsx` mostra punteggio, emoji feedback, risposte corrette/errate
- [x] Sezione "Visualizza Tutte le Risposte" con spiegazioni e riferimenti biblici

#### ✅ ICONE SEZIONE QUIZ (COMPLETATO)
- [x] Tutte le icone usano componente `Icon.tsx` con fallback emoji
- [x] Icone visibili su web e mobile
- [x] Tab categories, navigation, risultati - tutti funzionanti

### Sessione Precedente (Fork 10)

#### ✅ QUIZ 1000 DOMANDE - SOTTOCATEGORIE TEMATICHE (COMPLETATO)
- [x] **1000 domande** parsate dal file utente
- [x] **33 categorie tematiche** create automaticamente
- [x] **30 domande per quiz** (limite per sessione)
- [x] **Nuova UI con 3 tab**: Quiz Tematici (default), Quiz Classici, Studio Avanzato
- [x] **API endpoints**: GET /api/quiz/categories, GET /api/quiz/category/{id}

### Sessioni Precedenti
- Login Biometrico
- Traduzioni MoodSelector e Sezioni
- Fix Icone Web (Icon.tsx)
- Dizionario Biblico (69 termini)
- Sistema Preferiti e Flashcard
- Quiz tradotti in tutte le lingue
- TTS multilingua con Web Speech API

## Database Collections
- `quiz_translations_cache` - Cache traduzioni domande quiz (NUOVO)
- `dictionary_translations` - Cache traduzioni AI dizionario
- `dictionary_favorites` - Preferiti utente
- `dictionary_flashcards` - Flashcard con dati SM-2
- `bible_cache` - Cache capitoli Bibbia
- `users` - Utenti
- `quiz_history` - Storico quiz

## Backlog

### P1 - Prossimi
- [ ] UI Ricerca Globale (`/app/frontend/app/search.tsx`)
- [ ] UI Mappe Bibliche (`/app/frontend/app/maps.tsx`)

### P2
- [ ] Menu Personalizzazione UI (temi e font)
- [ ] Logo applicazione (colomba bianca)

## File Chiave

### Backend
- `/app/backend/server.py` - API principale
- `/app/backend/quiz_1000.py` - Logica quiz 1000 domande e traduzione on-demand
- `/app/backend/quiz_categories_data.json` - 1000 domande in JSON
- `/app/backend/quiz_translations_cache.json` - Cache traduzioni

### Frontend
- `/app/frontend/app/quiz.tsx` - UI quiz con statistiche
- `/app/frontend/src/utils/api.ts` - Client API
- `/app/frontend/src/components/Icon.tsx` - Wrapper icone con fallback

## API Endpoints Quiz

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/quiz/categories?lang={code}` | GET | Lista 33 categorie tradotte |
| `/api/quiz/category/{id}?lang={code}` | GET | 30 domande con traduzione on-demand |
| `/api/quiz/submit` | POST | Invia risposte, riceve statistiche |

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Note Tecniche
- Traduzione on-demand usa `emergentintegrations.llm.chat.LlmChat` con GPT-4o
- Cache traduzioni su file JSON per evitare chiamate ripetute
- Submit quiz supporta topic classici e `cat_{category_id}` per tematici
