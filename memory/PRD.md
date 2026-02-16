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
- [x] Versetto del Giorno
- [x] Text-to-Speech, Strumenti di studio IA, Traduzione versetti

### Community & Chat
- [x] Messaggi community pubblici multilingua
- [x] Utenti online con pallino verde (heartbeat)
- [x] Chat privata 1:1 tra utenti
- [x] Lista conversazioni con conteggio non letti
- [x] Tab Community / Chat nella pagina community

### Dizionario Biblico
- [x] Dizionario statico termini ebraici/greci
- [x] Ricerca AI per qualsiasi termine biblico (GPT-4o)
- [x] Cache risultati AI in MongoDB
- [x] Preferiti e Flashcards

### Progressi
- [x] Tracciamento capitoli letti con data
- [x] Statistiche lettura nel profilo

### Profile & Settings
- [x] Profilo con statistiche, Quiz, Dizionario, Diario, Gruppi
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
- `GET /api/dictionary/search/{query}` | `GET /api/dictionary/ai-search/{query}`
- `GET /api/progress` | `POST /api/progress/reading/chapter`

## Recent Changes

### 2026-02-16 - Session 5 (Current)
- **Reset Password**: Backend (forgot-password + reset-password endpoints) + Frontend (forgot-password.tsx) con Resend email
- **Community Chat Privata**: Backend (private-messages CRUD) + Frontend (tab Community/Chat, utenti online strip, private-chat.tsx)
- **Dizionario AI**: Backend (ai-search con GPT-4o + cache) + Frontend (pulsante sparkles nella barra di ricerca, pannello risultati AI)
- **Login Google Mobile**: Bridge redirect endpoint per APK

### Testing Results
- iteration_19: 100% (mobile auth redirect)
- iteration_20: 100% (password reset)
- iteration_21: 92% backend, 100% frontend (3 nuove feature - 1 timeout intermittente non-bug)

## Upcoming (P1)
- [ ] Migliorare sezione progressi con vista grafica capitoli letti

## Backlog (P2)
- [ ] UI Ricerca Globale
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!
