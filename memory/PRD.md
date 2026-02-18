# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Eliminazione Note e Segnalibri ✅ NUOVO
- [x] Eliminazione note dalla Bibbia (icona cestino su ogni nota)
- [x] Eliminazione segnalibri dalla schermata "I Miei Contenuti"
- [x] Eliminazione voci dal Diario (già esistente)
- [x] API DELETE funzionanti per bookmarks e notes

### I Miei Contenuti ✅
- [x] Schermata dedicata `/my-content` accessibile dal profilo e menu hamburger
- [x] Tab Segnalibri: lista con eliminazione
- [x] Tab Note: lista con eliminazione
- [x] Tab Evidenziati: versetti colorati
- [x] Link "Vai al versetto" per ogni elemento

### Icone "Torna Indietro" ✅ STANDARDIZZATE
- [x] Tutti i file usano il componente `Icon` invece di `Ionicons`
- [x] File corretti: maps.tsx, search.tsx, faq.tsx, feelings.tsx, flashcards.tsx, groups.tsx, events.tsx, mood-checkin.tsx, notifications.tsx
- [x] Icona `arrow-back` uniforme in tutte le schermate

### Menu Hamburger ✅
- [x] Aggiunto "I Miei Contenuti" al menu hamburger
- [x] Traduzioni in 6 lingue

### Altre Funzionalità Implementate
- [x] Versetti dinamici ad ogni tocco
- [x] Mapping chiavi mood EN→IT
- [x] Schermata progressi lettura
- [x] Lista amici/utenti preferiti
- [x] Chat privata
- [x] Dizionario AI
- [x] Reset password

## Recent Changes

### 2026-02-18 - Session 6 (Current)
- **Eliminazione contenuti**: Aggiunta funzione `handleDeleteNote` in bible.tsx con conferma
- **Menu Hamburger**: Aggiunto link "I Miei Contenuti"
- **Standardizzazione icone**: Migrati tutti i file da `Ionicons` a `Icon` component
- **Schermate corrette**: 9 file aggiornati per uniformità icone

### Testing Results
- iteration_27: Backend 100%, Frontend OK

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## Remaining Tasks

### P1
- [ ] Notifiche push dinamiche e tradotte

### Refactoring
- [ ] Suddividere server.py in moduli
