# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Note, Segnalibri e Evidenziazioni ✅ BUG FIX
- [x] **Creazione note**: POST /api/bible/study/notes funzionante
- [x] **Eliminazione note dal diario**: DELETE /api/journal/{entry_id} funzionante
- [x] **Visualizzazione durante lettura**: GET /api/bible/study/{book}/{chapter} ora restituisce user_notes E user_bookmarks
- [x] **Caricamento automatico**: bible.tsx carica bookmarks e highlights all'apertura del capitolo
- [x] **Modal strumenti studio**: Nota, AI Spiega, Dizionario, Evidenzia, Condividi, Segnalibro, Mappe, Wikipedia, LaParola

### Eliminazione Contenuti ✅
- [x] Eliminazione note dalla Bibbia (icona cestino)
- [x] Eliminazione segnalibri da "I Miei Contenuti"
- [x] Eliminazione voci dal Diario

### I Miei Contenuti ✅
- [x] Schermata /my-content accessibile da profilo e menu hamburger
- [x] Tab Segnalibri/Note/Evidenziati con eliminazione

### Versetti Dinamici ✅
- [x] Cambiano ad ogni tocco
- [x] Mapping chiavi EN→IT
- [x] Riflessione AI diversa ogni volta

### Progressi Lettura ✅
- [x] Schermata /reading-progress
- [x] Link al capitolo dalla cronologia

### Altre Funzionalità
- [x] Lista amici, Chat privata, Dizionario AI
- [x] Reset password, Google OAuth
- [x] Icone standardizzate (Icon component)

## Recent Changes

### 2026-02-18 - Session 6
- **Bug Fix**: API GET /bible/study/{book}/{chapter} ora restituisce user_bookmarks
- **Bug Fix**: bible.tsx loadStudyData popola bookmarkedVerses e highlightedVerses
- **Bug Fix**: Verificata eliminazione voci diario funzionante

## Testing Results
- iteration_28: Backend 100% (10/10), Frontend 95%

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## Remaining Tasks
- [ ] Notifiche push dinamiche e tradotte
- [ ] Refactoring server.py in moduli
