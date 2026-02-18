# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Toolbar Bibbia con accesso "I Miei Contenuti"
- [x] Pulsante bookmark nel toolbar lettura Bibbia
- [x] Apre schermata /my-content per vedere note, segnalibri, evidenziazioni
- [x] Accessibile anche da Menu Hamburger e Profilo

### Versetti Dinamici "Come ti senti oggi?"
- [x] Backend: exclude_ref parameter per evitare ripetizioni consecutive
- [x] Backend: fallback DB per controllare ultimo versetto inviato
- [x] Backend: session_id unico per ogni chiamata LLM (riflessioni sempre fresche)
- [x] Frontend: passa il ref corrente come exclude_ref ad ogni tocco
- [x] Frontend: key unica (_ts) per forzare React re-mount
- [x] Mapping chiavi EN→IT (happy→felice, hopeful→speranzoso, ecc.)
- [x] Testato: 5 chiamate consecutive = 5 versetti unici (100% diversi)

### Note, Segnalibri e Evidenziazioni
- [x] Creazione e eliminazione note
- [x] Creazione e eliminazione segnalibri
- [x] Visualizzazione durante lettura capitolo
- [x] API GET /bible/study/{book}/{chapter} restituisce user_notes e user_bookmarks

### Altre Funzionalità
- [x] Eliminazione voci dal Diario
- [x] Lista amici/utenti preferiti
- [x] Chat privata
- [x] Dizionario AI
- [x] Reset password
- [x] Progressi lettura (schermata /reading-progress, collegata dalla home)
- [x] Sezione "I Miei Contenuti" (/my-content)
- [x] Schermata Amici (/friends)
- [x] Icone standardizzate con componente <Icon>

## Recent Changes

### 2026-02-19 - Session 7 (Bug Fix P0 + Logout/Delete Fix)
- **Bug P0 RISOLTO**: Versetti "Come ti senti oggi?" ora cambiano ad ogni tocco
  - Backend: aggiunto `exclude_ref` a MoodRequest per escludere versetto precedente
  - Backend: fallback DB per controllare ultimo checkin utente/mood
  - Backend: session_id LLM unico per ogni chiamata (uuid)
  - Frontend: passa previousRef come exclude_ref
  - Frontend: key unica `_ts` per forzare re-mount componente risultato
- **Bug Fix: Logout/Elimina Account**
  - Backend logout ora legge token sia da cookie che da Authorization header
  - Frontend: redirect robusto con `window.location.href = '/'` su web
  - Frontend: handleDeleteAccount ora chiama anche logout() per pulizia completa
- **Feature: Reset Statistiche Individuali**
  - Backend: POST /api/progress/reset/{stat_type} con 4 tipi: streak, chapters, journal, history
  - Frontend: pulsanti "Azzera" sotto ogni stat card nella schermata progressi
  - Frontend: pulsante "Azzera Cronologia" nella sezione letture recenti
  - Conferma obbligatoria prima di ogni reset
  - Ogni reset è indipendente e non tocca le altre statistiche
- **Testing**: 100% backend (13/13 test reset + 10/10 mood), 100% frontend

### 2026-02-18 - Session 6
- Toolbar Bibbia con pulsante bookmark
- Traduzioni aggiunte in 6 lingue

## Testing Results
- Backend: 100% - 10/10 test mood-checkin API (5 chiamate = 5 versetti unici)
- Frontend: 100% - Emoji mood selector, loading indicator, versetti diversi ad ogni click
- Test file: /app/backend/tests/test_mood_checkin.py

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## API Endpoints Chiave
- `POST /api/ai/mood-checkin` - Versetti casuali (con exclude_ref) + riflessione AI
- `GET /api/bible/study/{book}/{chapter}` - Dati studio con user_notes e user_bookmarks
- `GET/POST/DELETE /api/bookmarks` - CRUD segnalibri
- `GET/POST/DELETE /api/bible/study/notes` - CRUD note

## Remaining Tasks (Backlog)
- [ ] P1: Notifiche push dinamiche e tradotte con versetto del giorno
- [ ] P2: Gruppi di studio privati
- [ ] P2: Personalizzazione temi e font
- [ ] P2: Refactoring server.py in moduli separati
