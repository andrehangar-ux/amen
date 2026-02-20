# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Quiz Studio Biblico Avanzato - 6 Sotto-Quiz Tematici ✅ (2026-02-20)
- [x] 6 sottocategorie da 8 domande ciascuna sotto il tab "Studio Avanzato"
- [x] Backend: quiz_advanced_subcategories.json + endpoint dedicati
- [x] Frontend: Tab avanzato mostra sottocategorie invece del singolo quiz da 100 domande
- [x] Pulsante X (indietro) funzionante nelle schermate quiz
- [x] Invio quiz e risultati funzionanti per le sottocategorie avanzate

### Navigazione Capitoli Bibbia ✅ (AGGIUNTO 2026-02-19)
- [x] Pulsanti "Precedente" / "Successivo" per navigare tra capitoli
- [x] Pulsante centrale per tornare alla selezione capitoli
- [x] Navigazione automatica tra libri (fine libro → inizio libro successivo)
- [x] Pulsanti disabilitati ai limiti (inizio/fine Bibbia)
- [x] Traduzioni multilingua (IT, ES, EN)

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

### 2026-02-20 - Session 10 (Current)
- **Quiz Studio Avanzato Suddiviso**: Le 100 domande avanzate sono state suddivise in 6 sotto-quiz tematici da 8 domande:
  1. Critica Testuale - Manoscritti, codici e varianti testuali
  2. Esegesi e Metodi - Tecniche interpretative e figure retoriche
  3. Lingue Bibliche - Ebraico, aramaico e greco del NT
  4. Teologia del NT - Cristologia, soteriologia e escatologia
  5. Teologia dell'AT - Pentateuco, profeti e sapienza
  6. Storia e Padri - Eresie, concili e Padri della Chiesa
- **Nuovi endpoint**: `/api/quiz/advanced-subcategories` e `/api/quiz/advanced-subcategory/{id}`
- **Tab Studio Avanzato**: Ora mostra le 6 sottocategorie con banner "6 quiz - 48 domande"
- **Fix quiz-stats.tsx**: Corretto errore FONT_SIZES non definito
- **Fix Pulsante X/Indietro (Web + iOS Nativo)**: Risolto bug click/touch:
  - `<View pointerEvents="none">` intorno a Icon per prevenire intercettazione events
  - `hitSlop={20}` per area touch più grande
  - `accessibilityRole="button"` per migliore gestione touch su nativo
  - `minWidth/minHeight: 44px` per touch target Apple-compliant
  - `router.push('/')` per navigazione affidabile
- **Traduzioni Quiz Avanzati**: 48 domande tradotte in 5 lingue (en, es, de, fr, pt) con traduzioni pre-generate salvate in `quiz_advanced_translations.json`
- **Test Report**: /app/test_reports/iteration_32.json, iteration_33.json

### 2026-02-20 - Session 9
- **Quiz Studio Biblico Avanzato**: Aggiunte 100 domande di critica testuale, esegesi e teologia biblica
- **Statistiche Quiz**: Nuova schermata `/quiz-stats` con:
  - Punteggio medio e migliore
  - Streak giorni consecutivi
  - Statistiche per categoria
  - Attività recente
- **API /quiz/stats**: Nuovo endpoint per statistiche aggregate

### 2026-02-19 - Session 8 (Current)
- **Navigazione Capitoli**: Aggiunti pulsanti "Precedente" / "Successivo" nella lettura Bibbia
- **Fix Android Permissions**: Rimosso permesso CAMERA non utilizzato da app.json

### 2026-02-19 - Session 7
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

## Testing Results (2026-02-20)
- Backend: 100% - 10/10 pytest tests passed (iteration_32)
- Frontend: 100% - 9/9 features verified (quiz subcategories, X button, submission)
- Test Report: /app/test_reports/iteration_32.json

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
