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

### Sessione Corrente (Feb 2026) - Fork 12

#### ✅ FIX QUIZ LENTO (COMPLETATO)
- [x] Caricamento parallelo topics e categories con Promise.all
- [x] Tempo caricamento ridotto da ~5s a ~2s
- [x] Stato loading separato per avvio quiz
- [x] Messaggio "Caricamento quiz..." durante attesa

#### ✅ FIX TTS MULTILINGUA (COMPLETATO)
- [x] Selezione voice robusta con fallback chain
- [x] Supporto 6 lingue: it-IT, es-ES, en-GB, de-DE, fr-FR, pt-BR
- [x] Gestione asincrona voci Chrome
- [x] Timeout fallback se voci non caricano

#### ✅ CRONOLOGIA LETTURA (COMPLETATO)
- [x] Nuovo endpoint `POST /api/progress/reading/chapter`
- [x] Nuovo endpoint `GET /api/progress/reading/history`
- [x] Salvataggio automatico capitoli letti da bible.tsx
- [x] Sezione "Cronologia Lettura" nel profilo
- [x] Click per riprendere lettura capitolo
- [x] Mostra conteggio letture e data

#### ✅ FLUIDITÀ APP (COMPLETATO)
- [x] API response times: ~0.1-0.3s
- [x] Caricamento parallelo dove possibile
- [x] Ottimizzazione query MongoDB

### Sessione Precedente (Fork 11)

#### ✅ TRADUZIONE ON-DEMAND QUIZ 1000 DOMANDE
- [x] Sistema traduzione on-demand per 1000 domande
- [x] Cache traduzioni su file JSON
- [x] 6 lingue supportate

#### ✅ STATISTICHE E CORREZIONI QUIZ
- [x] Endpoint `/api/quiz/submit` con risultati dettagliati
- [x] UI risultati con punteggio, feedback, correzioni

#### ✅ ICONE SEZIONE QUIZ
- [x] Componente Icon.tsx con fallback emoji

### Sessioni Precedenti
- Quiz 1000 domande in 33 categorie
- Login Biometrico
- Dizionario Biblico (69 termini)
- Sistema Preferiti e Flashcard
- TTS multilingua con Web Speech API

## Database Collections
- `reading_history` - Cronologia capitoli letti (NUOVO)
- `quiz_translations_cache` - Cache traduzioni quiz
- `dictionary_translations` - Cache traduzioni AI
- `dictionary_favorites` - Preferiti utente
- `dictionary_flashcards` - Flashcard SM-2
- `bible_cache` - Cache capitoli Bibbia
- `users` - Utenti
- `progress` - Progressi utente
- `quiz_history` - Storico quiz

## Backlog

### P1 - Prossimi
- [ ] UI Ricerca Globale (`/app/frontend/app/search.tsx`)
- [ ] UI Mappe Bibliche (`/app/frontend/app/maps.tsx`)

### P2
- [ ] Menu Personalizzazione UI (temi e font)
- [ ] Logo applicazione

## File Chiave

### Backend
- `/app/backend/server.py` - API principale

### Frontend
- `/app/frontend/app/quiz.tsx` - UI quiz ottimizzata
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore con TTS migliorato
- `/app/frontend/app/(tabs)/profile.tsx` - Profilo con cronologia

## API Endpoints

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/progress/reading/chapter` | POST | Salva capitolo letto |
| `/api/progress/reading/history` | GET | Cronologia lettura |
| `/api/quiz/categories` | GET | Lista categorie |
| `/api/quiz/category/{id}` | GET | Quiz per categoria |
| `/api/quiz/submit` | POST | Invia risposte quiz |

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Performance
- Quiz load: ~2s
- Quiz start: ~3s  
- API response: ~0.1-0.3s
- TTS: Immediato con voci locali

## Test Reports
- `/app/test_reports/iteration_11.json` - 17/17 test passati
