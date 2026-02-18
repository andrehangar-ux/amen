# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Authentication & Account
- [x] Login/Register con email/password
- [x] Google OAuth (Web + Mobile bridge redirect)
- [x] Reset Password via email (Resend) con codice 6 cifre
- [x] Login automatico, Logout, Elimina Account (GDPR)

### Bible Reading
- [x] Lettura capitoli in italiano + multilingua
- [x] Versetto del Giorno (con rotazione giornaliera e traduzione)
- [x] Text-to-Speech, Strumenti di studio IA, Traduzione versetti
- [x] Pulsante "Condividi" con fallback web (copia negli appunti)

### Community & Chat
- [x] Messaggi community pubblici multilingua
- [x] Utenti online con pallino verde (heartbeat)
- [x] Chat privata 1:1 tra utenti
- [x] Lista conversazioni con conteggio non letti
- [x] Tab Community / Chat nella pagina community

### Dizionario Biblico
- [x] Dizionario statico 106+ termini ebraici/greci/aramaici
- [x] Ricerca AI per qualsiasi termine biblico (GPT-4o)
- [x] Cache risultati AI in MongoDB
- [x] Preferiti e Flashcards

### Funzionalità "Come ti senti oggi?"
- [x] Versetti dinamici che cambiano ad ogni tocco (random.choice)
- [x] Versetti tradotti nella lingua dell'utente (IT/EN/ES/PT/FR/DE)
- [x] Riflessione AI personalizzata nella lingua selezionata

### I Miei Contenuti
- [x] Schermata dedicata per visualizzare contenuti salvati
- [x] Tab Segnalibri: versetti salvati con note
- [x] Tab Note: note di studio personali
- [x] Tab Evidenziati: versetti evidenziati con colori
- [x] Azioni: elimina, vai al versetto
- [x] Traduzioni in 6 lingue

### I Miei Amici (NUOVO - P2 COMPLETATO)
- [x] Schermata `/friends` per gestire utenti preferiti
- [x] Aggiungere/rimuovere amici
- [x] Vedere stato online/offline degli amici
- [x] Avviare chat direttamente dalla lista amici
- [x] Ricerca utenti per aggiungere nuovi amici
- [x] Traduzioni in 6 lingue

### Gruppi di Studio
- [x] Creare/unirsi a gruppi pubblici
- [x] Post e commenti nei gruppi
- [x] Lista dei miei gruppi

### Ricerca Globale
- [x] UI esistente in `/search`
- [x] API backend `/api/search` funzionante

### Mappe Bibliche
- [x] UI esistente in `/maps`
- [x] API backend `/api/maps` funzionante

### Progressi
- [x] Tracciamento capitoli letti con data
- [x] Statistiche lettura nel profilo

### Profile & Settings
- [x] Profilo con statistiche, Quiz, Dizionario, Diario, Gruppi, I Miei Contenuti, I Miei Amici
- [x] Privacy/Termini, Logout, Elimina Account
- [x] Cambio lingua (6 lingue), Notifiche push
- [x] Impostazioni in `/settings` (lingua, bibbia, notifiche)

## Tech Stack
- **Frontend**: React Native + Expo (PWA), TypeScript, Zustand, i18next
- **Backend**: FastAPI + MongoDB
- **AI**: OpenAI GPT-4o (via Emergent LLM Key)
- **Auth**: JWT + Emergent Google OAuth
- **Email**: Resend (reset password)

## API Endpoints
### Auth
- `POST /api/auth/register` | `POST /api/auth/login` | `GET /api/auth/me`
- `POST /api/auth/forgot-password` | `POST /api/auth/reset-password`
- `GET /api/auth/mobile-redirect?scheme=amen` | `POST /api/auth/google-callback`
- `DELETE /api/auth/delete-account`

### Community & Chat
- `GET/POST /api/community/messages` | `POST /api/community/messages/{id}/like`
- `POST /api/users/heartbeat` | `GET /api/users/online`
- `POST /api/private-messages` | `GET /api/private-messages/conversations`
- `GET /api/private-messages/{user_id}`

### Friends (NUOVO)
- `GET /api/friends` - Lista amici
- `POST /api/friends` - Aggiungi amico
- `DELETE /api/friends/{friend_id}` - Rimuovi amico
- `GET /api/friends/check/{friend_id}` - Verifica amicizia

### Bible & Dictionary
- `GET /api/bible/daily-verse` | `GET /api/bible/chapter/{book}/{chapter}`
- `GET /api/dictionary` | `GET /api/dictionary/search/{query}` | `GET /api/dictionary/ai-search/{query}`
- `POST /api/ai/mood-checkin` | `GET /api/progress` | `POST /api/progress/reading/chapter`

### Bookmarks & Notes
- `GET /api/bookmarks` | `POST /api/bookmarks` | `DELETE /api/bookmarks/{id}`
- `GET /api/bible/study/notes` | `POST /api/bible/study/notes` | `DELETE /api/bible/study/notes/{id}`

### Groups
- `GET/POST /api/groups` | `GET /api/groups/my` | `POST /api/groups/{id}/join`

### Search & Maps
- `GET /api/search?q=query` - Ricerca globale
- `GET /api/maps` | `GET /api/maps/{id}` - Mappe bibliche

## Recent Changes

### 2026-02-18 - Session 6 (Current)
- **Versetti dinamici**: Modificato backend per cambiare versetto ad ogni tocco (random.choice invece di random.seed giornaliero)
- **Nuova schermata "I Miei Contenuti"**: Tab Segnalibri/Note/Evidenziati
- **Nuova schermata "I Miei Amici"**: Backend endpoints + Frontend completo per gestire utenti preferiti
- **Link nel profilo**: Aggiunti "I Miei Contenuti" e "I Miei Amici" in tutte le 6 lingue

### Testing Results
- iteration_25: 100% backend (10/10), 100% frontend (Friends feature verified)
- iteration_24: 100% backend (12/12), 95% frontend
- iteration_23: 100% backend, 100% frontend (P0 features verified)

## Completed Tasks
- [x] P0: Versetti dinamici per stato d'animo (cambiano ad ogni tocco)
- [x] P0: Traduzione versetti nella lingua utente
- [x] P0: Fix pulsante "Condividi"
- [x] P0: Ampliamento dizionario (108 termini)
- [x] P1: Sezione "I Miei Contenuti" (segnalibri, note, evidenziazioni)
- [x] P2: Lista amici/utenti preferiti

## Remaining Tasks

### P1 - Da fare
- [ ] Rendere dinamiche e tradotte le notifiche push del versetto del giorno

### P2 - Backlog
- [x] ~~Gruppi di studio privati~~ (Gruppi pubblici esistono già)
- [x] ~~Lista amici preferiti~~ (COMPLETATO)
- [x] ~~UI Ricerca Globale~~ (Esistente in /search)
- [x] ~~Mappe Bibliche~~ (Esistente in /maps)
- [ ] Personalizzazione temi e font avanzata

## Refactoring Suggerito
- [ ] Suddividere `server.py` in moduli (auth.py, community.py, bible.py)

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!
