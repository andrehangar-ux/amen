# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Toolbar Bibbia con accesso "I Miei Contenuti" ✅
- [x] Pulsante bookmark nel toolbar lettura Bibbia
- [x] Apre schermata /my-content per vedere note, segnalibri, evidenziazioni
- [x] Accessibile anche da Menu Hamburger e Profilo

### Versetti Dinamici "Come ti senti oggi?" ✅
- [x] Backend: random.choice() senza seed - versetti casuali ad ogni chiamata
- [x] Mapping chiavi EN→IT (happy→felice, hopeful→speranzoso, ecc.)
- [x] Riflessione AI diversa ad ogni tocco
- [x] Testato: 5 chiamate consecutive = 4 versetti unici

### Note, Segnalibri e Evidenziazioni ✅
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
- [x] Progressi lettura

## Recent Changes

### 2026-02-18 - Session 6
- **Toolbar Bibbia**: Aggiunto pulsante bookmark (Edizioni, A16, Bookmark, Aiuto)
- **Traduzioni**: Aggiunte myContent, editions, help in 6 lingue
- **Backend Mood**: Verificato funzionamento random.choice() - versetti diversi ad ogni chiamata

## Testing Results
- Backend: 100% - mood-checkin API funzionante (5 chiamate = 4 versetti unici)
- Frontend: Emoji mood selector funziona correttamente

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## API Endpoints Chiave
- `POST /api/ai/mood-checkin` - Versetti casuali + riflessione AI
- `GET /api/bible/study/{book}/{chapter}` - Dati studio con user_notes e user_bookmarks
- `GET/POST/DELETE /api/bookmarks` - CRUD segnalibri
- `GET/POST/DELETE /api/bible/study/notes` - CRUD note

## Remaining Tasks
- [ ] Notifiche push dinamiche e tradotte
- [ ] Refactoring server.py in moduli
