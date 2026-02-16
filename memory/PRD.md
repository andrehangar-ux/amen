# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Authentication & Account Management
- [x] Login/Register con email/password
- [x] Google OAuth (Emergent Auth) - Web funzionante
- [x] Google OAuth Mobile - Bridge redirect per APK (nuovo)
- [x] Login automatico (AsyncStorage)
- [x] Logout
- [x] Elimina Account (GDPR compliant)
- [x] Checkbox accettazione T&C

### Bible Reading
- [x] Lettura capitoli in italiano
- [x] Versetto del Giorno (multilingua: IT, EN, ES, DE, FR, PT)
- [x] Text-to-Speech
- [x] Strumenti di studio IA
- [x] Traduzione versetti

### User Experience
- [x] Multi-language support (6 lingue)
- [x] Mood check-in con versetti pertinenti
- [x] Cronologia lettura
- [x] Progressi utente

### Profile & Settings
- [x] Pagina profilo con statistiche
- [x] Link a Quiz, Dizionario, Diario, Gruppi
- [x] Sezione Account (Privacy/Termini, Logout, Elimina Account)

## Tech Stack
- **Frontend**: React Native + Expo (PWA)
- **Backend**: FastAPI + MongoDB
- **AI**: OpenAI GPT-4o (via Emergent LLM Key)
- **Auth**: JWT + Emergent Google OAuth

## API Endpoints
- `POST /api/auth/register` - Registrazione
- `POST /api/auth/login` - Login
- `GET /api/auth/mobile-redirect?scheme=amen` - Bridge HTML per OAuth mobile (NUOVO)
- `POST /api/auth/google-callback` - Callback Google OAuth
- `DELETE /api/auth/delete-account` - Elimina account
- `GET /api/bible/daily-verse?lang=xx` - Versetto del giorno
- `GET /api/bible/chapter/{book}/{chapter}?lang=xx` - Lettura capitoli
- `POST /api/ai/chat` - Chat con assistente IA
- `POST /api/ai/mood-checkin` - Check-in umore

## Database Collections
- `users` - Dati utente
- `reading_history` - Cronologia lettura
- `user_consent_log` - Consensi GDPR
- `quiz_results` - Risultati quiz
- `bookmarks` - Segnalibri

## Completed (P0)
- [x] Bug fix sezione Privacy e Legale
- [x] Bug fix pulsanti Logout/Elimina Account
- [x] Bug fix cambio lingua
- [x] Bug fix notifiche push
- [x] Fix Login Google Mobile - Bridge redirect endpoint + auth-callback migliorato

## Upcoming (P1)
- [ ] Sezione Community interattiva (in attesa specifiche utente)

## Backlog (P2)
- [ ] Interfaccia Ricerca Globale
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font

## Recent Changes

### 2026-02-16 (Session 5) - Fix Login Google Mobile
- **Backend**: Aggiunto endpoint `GET /api/auth/mobile-redirect?scheme=amen` che serve pagina HTML bridge
  - Legge session_id dall'hash fragment URL (lato client)
  - Reindirizza al deep link dell'app `{scheme}://auth-callback?session_id=xxx`
  - Mostra messaggio fallback dopo 3 secondi se l'app non si apre
- **Frontend login.tsx**: Riscritto flusso mobile Google auth
  - Usa il nuovo endpoint bridge come redirect URL
  - Estrae dinamicamente lo scheme dall'app (`Linking.createURL`)
  - Gestisce correttamente `openAuthSessionAsync` result
- **Frontend auth-callback.tsx**: Aggiunto rilevamento mobile browser
  - Se caricata in browser mobile (userAgent Android/iOS), reindirizza al deep link
  - Compatibilità retroattiva per APK esistenti
- **Testing**: iteration_19 - 100% test passati (11/11 backend + frontend)

### 2026-02-16 (Session 4) - Bug Fix Critici
- Bug 1-4 (Privacy, Account, Lingua, Notifiche) RISOLTI E VERIFICATI

## Known Issues
- **APK Rebuild Required**: L'utente deve compilare un nuovo APK per applicare il fix del login Google mobile
- **Scheme Mismatch**: L'utente ha menzionato "faithapp9" - potrebbe essere uno scheme diverso nell'APK precedente

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!
