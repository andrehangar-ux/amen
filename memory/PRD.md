# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Toolbar Bibbia con accesso "I Miei Contenuti" ✅
- [x] Pulsante bookmark nel toolbar lettura Bibbia
- [x] Apre schermata /my-content per vedere note, segnalibri, evidenziazioni
- [x] Accessibile anche da Menu Hamburger e Profilo

### Versetti Dinamici "Come ti senti oggi?" ✅ (BUG RISOLTO 2026-02-19)
- [x] Backend: random.choice() - versetti casuali ad ogni chiamata
- [x] Frontend: timestamp anti-cache + Cache-Control headers
- [x] Frontend: _timestamp nel risultato per forzare React state update
- [x] Mapping chiavi EN→IT (happy→felice, hopeful→speranzoso, ecc.)
- [x] Riflessione AI diversa ad ogni tocco
- [x] **TESTATO**: 4 click consecutivi = 4 versetti diversi (Salmi 118:24, Salmi 16:11, Isaia 55:12, Salmi 27:14)

### Sezione "Il tuo Progresso" dalla Home ✅
- [x] TouchableOpacity wrapper sulla sezione progressi
- [x] Navigazione a /reading-progress funzionante
- [x] Statistiche: giorni consecutivi, capitoli letti, voci diario
- [x] Cronologia letture con date corrette (field `last_read`)

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
- [x] Icone standardizzate con componente Icon

## Recent Changes

### 2026-02-19 - Session 7 (Current)
- **BUG FIX CRITICO**: Versetti mood selector ora cambiano ad ogni click
  - Aggiunto timestamp anti-cache nella chiamata API
  - Aggiunto Cache-Control: no-cache headers
  - Aggiunto _timestamp al risultato per forzare React update
- **Sezione Progressi**: Ora cliccabile dalla Home page
- **Fix date**: Corretto campo `read_at` → `last_read` nella cronologia letture
- **Validazione date**: Aggiunta gestione date invalide in formatDate()

### 2026-02-18 - Session 6
- **Toolbar Bibbia**: Aggiunto pulsante bookmark (Edizioni, A16, Bookmark, Aiuto)
- **Traduzioni**: Aggiunte myContent, editions, help in 6 lingue
- **Backend Mood**: Verificato funzionamento random.choice()

## Testing Results (2026-02-19)
- Backend: 100% - mood-checkin API funzionante
- Frontend: 100% - Mood selector, Progress navigation, Back button tutti verificati
- Test Report: /app/test_reports/iteration_31.json

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## API Endpoints Chiave
- `POST /api/ai/mood-checkin` - Versetti casuali + riflessione AI
- `GET /api/bible/study/{book}/{chapter}` - Dati studio con user_notes e user_bookmarks
- `GET/POST/DELETE /api/bookmarks` - CRUD segnalibri
- `GET/POST/DELETE /api/bible/study/notes` - CRUD note
- `GET /api/progress/reading/history` - Cronologia letture

## Remaining Tasks (P1)
- [ ] Notifiche push con versetto dinamico e tradotto
- [ ] Refactoring server.py in moduli

## Future Tasks (P2)
- [ ] Gruppi di studio privati
- [ ] UI Ricerca Globale completa
- [ ] Mappe Bibliche
- [ ] Personalizzazione temi e font
