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
- [x] Versetti dinamici che cambiano ad ogni tocco (non più rotazione giornaliera)
- [x] Versetti tradotti nella lingua dell'utente (IT/EN/ES/PT/FR/DE)
- [x] Riflessione AI personalizzata nella lingua selezionata

### I Miei Contenuti (NUOVO)
- [x] Schermata dedicata per visualizzare contenuti salvati
- [x] Tab Segnalibri: versetti salvati con note
- [x] Tab Note: note di studio personali
- [x] Tab Evidenziati: versetti evidenziati con colori
- [x] Azioni: elimina, vai al versetto
- [x] Traduzioni in 6 lingue

### Progressi
- [x] Tracciamento capitoli letti con data
- [x] Statistiche lettura nel profilo

### Profile & Settings
- [x] Profilo con statistiche, Quiz, Dizionario, Diario, Gruppi, I Miei Contenuti
- [x] Privacy/Termini, Logout, Elimina Account
- [x] Cambio lingua (6 lingue), Notifiche push

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

### Bible & Dictionary
- `GET /api/bible/daily-verse` | `GET /api/bible/chapter/{book}/{chapter}`
- `GET /api/dictionary` | `GET /api/dictionary/search/{query}` | `GET /api/dictionary/ai-search/{query}`
- `POST /api/ai/mood-checkin` | `GET /api/progress` | `POST /api/progress/reading/chapter`

### Bookmarks & Notes
- `GET /api/bookmarks` | `POST /api/bookmarks` | `DELETE /api/bookmarks/{id}`
- `GET /api/bible/study/notes` | `POST /api/bible/study/notes` | `DELETE /api/bible/study/notes/{id}`

## Recent Changes

### 2026-02-18 - Session 6 (Current)
- **Versetti dinamici**: Modificato backend per cambiare versetto ad ogni tocco (rimosso random.seed giornaliero)
- **Nuova schermata "I Miei Contenuti"**: Creato `/app/frontend/app/my-content.tsx` con 3 tab (Segnalibri, Note, Evidenziati)
- **Link nel profilo**: Aggiunto menu item "I Miei Contenuti" in tutte le 6 lingue
- **Route fix**: Aggiunta route `my-content` in `_layout.tsx`

### 2026-02-16 - Session 5
- **Reset Password**: Backend + Frontend con Resend email
- **Community Chat Privata**: Backend + Frontend
- **Dizionario AI**: Backend + Frontend
- **Login Google Mobile**: Bridge redirect endpoint

### Testing Results
- iteration_24: 100% backend (12/12), 95% frontend (route working)
- iteration_23: 100% backend, 100% frontend (P0 features verified)

## Upcoming (P1)
- [ ] Rendere dinamiche e tradotte le notifiche push del versetto del giorno

## Backlog (P2)
- [ ] Gruppi di studio privati e lista amici preferiti
- [ ] UI Ricerca Globale
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font

## Refactoring Suggerito
- [ ] Suddividere `server.py` in moduli (auth.py, community.py, bible.py)

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!
