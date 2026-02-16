# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Authentication & Account Management
- [x] Login/Register con email/password
- [x] Google OAuth (Emergent Auth)
- [x] Login automatico (AsyncStorage)
- [x] Logout
- [x] Elimina Account (GDPR compliant - cancella tutti i dati utente)
- [x] Checkbox accettazione T&C prima della registrazione

### Bible Reading
- [x] Lettura capitoli in italiano
- [x] Versetto del Giorno (multilingua: IT, EN, ES, DE, FR, PT)
- [x] Text-to-Speech (Web Speech API / Expo AV)
- [x] Strumenti di studio IA (Spiega, Evidenzia)
- [x] Traduzione versetti

### User Experience
- [x] Multi-language support (6 lingue)
- [x] Mood check-in con versetti pertinenti
- [x] Cronologia lettura
- [x] Progressi utente (streak, capitoli letti, voci diario)

### Profile & Settings
- [x] Pagina profilo con statistiche
- [x] Cronologia lettura collapsabile
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
- `DELETE /api/auth/delete-account` - Elimina account (cascade delete)
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

## In Progress (P0)
- [x] Bug fix sezione Privacy e Legale - **COMPLETATO**
- [x] Bug fix pulsanti Logout/Elimina Account - **COMPLETATO**
- [x] Bug fix cambio lingua - **COMPLETATO**
- [x] Bug fix notifiche push - **VERIFICATO FUNZIONANTE**

## Upcoming (P1)
- [ ] Sezione Community interattiva (in attesa specifiche utente)
- [ ] Test Login Google su dispositivo mobile reale

## Backlog (P2)
- [ ] Interfaccia Ricerca Globale
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font

## Recent Changes

### 2026-02-16 (Session 4) - Bug Fix Critici
- **Bug 1 - Privacy e Legale FIXED**: I link (Informativa Privacy, Termini di Servizio, GDPR) ora navigano correttamente alla pagina `/privacy` invece di mostrare semplici alert
- **Bug 2 - Pulsanti Account FIXED**: "Elimina Account" e "Esci dall'Account" funzionano correttamente con dialog di conferma
- **Bug 3 - Cambio Lingua FIXED**: La funzione `saveSettings()` ora chiama `setGlobalLanguage()` per aggiornare immediatamente l'UI
- **Bug 4 - Notifiche VERIFIED**: Lo switch "Versetto del Giorno" è funzionante e richiede i permessi correttamente
- **Testing**: iteration_18 - 100% bug fix verified

### 2026-02-15 (Session 3) - Notifiche Push & Miglioramenti
- **Notifiche Push**: Implementato sistema notifiche giornaliere per "Versetto del Giorno"
  - Time picker per scegliere l'orario (default 07:00)
  - Toggle on/off nelle Impostazioni
  - Pulsante "Invia notifica di test"
  - Salvataggio preferenze in AsyncStorage
  - Android channel configurato
- **Menu Hamburger**: Aggiunta voce "Impostazioni" (settings)
- **Login Google Web**: Migliorato flusso OAuth per browser
- **Traduzioni**: Aggiunte chiavi per notifiche in IT/EN
- **Testing**: Tutti i test passati (iteration_15, iteration_16)

### 2026-02-15 (Session 2)
- **Menu Hamburger**: Sostituita tab bar inferiore con menu hamburger (☰) in alto a destra
- **Sezione Donazioni**: Aggiunta pagina `/donate` accessibile dal menu hamburger
  - PayPal: andrehangar@live.it
  - IBAN: IT46 I036 6901 6008 5802 8558 932
  - BIC/SWIFT: REVOITM2
  - Banca: Revolut Bank UAB
- **Quiz Traduzioni**: Corrette domande incomprensibili ("Isaia - Proto?" → "Quali capitoli formano il Proto-Isaia?")
- **Account Buttons**: Verificati funzionanti (Disconnetti, Elimina Account)

### 2026-02-15 (Session 1)
- Fixed: Versetto del giorno in tedesco (aggiunto a SAMPLE_VERSES_MULTILANG)
- Fixed: Mood verses in tedesco (aggiunto a MOOD_VERSES_MULTILANG)
- Verified: Sezione Account funzionante (Privacy, Logout, Elimina Account)

## Known Issues
- **Login Google Mobile**: Non testato su dispositivo fisico (richiede Expo Go o build nativa)
- **Notifiche Web**: Warning `[expo-notifications] Listening to push token changes is not yet fully supported on web` - comportamento normale, le notifiche web richiedono configurazione Firebase separata

## Upcoming (P1)
- [ ] Fix Login Google su mobile
- [ ] Sezione Community interattiva (in attesa specifiche utente)

## Backlog (P2)
- [ ] Interfaccia Ricerca Globale
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!
