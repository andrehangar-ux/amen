# Amen! - App Biblica PWA

## Problem Statement
App mobile PWA per lettura della Bibbia con funzionalità di studio, diario spirituale, community e assistente IA.

## Core Features Implemented

### Funzionalità "Come ti senti oggi?" ✅ AGGIORNATO
- [x] Versetti dinamici che cambiano ad OGNI TOCCO (random.choice)
- [x] Mapping chiavi inglesi (happy/hopeful) → italiane (felice/speranzoso)
- [x] Riflessione AI che cambia ad ogni chiamata
- [x] Versetti tradotti nella lingua dell'utente (IT/EN/ES/PT/FR/DE)
- [x] Loading indicator durante il caricamento

### Progressi di Lettura ✅ AGGIORNATO
- [x] Nuova schermata dedicata `/reading-progress`
- [x] Statistiche: giorni consecutivi, capitoli letti, voci diario
- [x] Cronologia delle letture recenti
- [x] Link diretto al capitolo nella Bibbia (tocca per leggere)
- [x] Pulsante "Continua a Leggere"
- [x] Profilo: stats cliccabili con Link/Pressable per navigazione web
- [x] Traduzioni in 6 lingue

### Authentication & Account
- [x] Login/Register con email/password
- [x] Google OAuth (Web + Mobile bridge redirect)
- [x] Reset Password via email (Resend)
- [x] Login automatico, Logout, Elimina Account (GDPR)

### Bible Reading
- [x] Lettura capitoli in italiano + multilingua
- [x] Versetto del Giorno (con rotazione giornaliera e traduzione)
- [x] Text-to-Speech, Strumenti di studio IA
- [x] Pulsante "Condividi" con fallback web

### Community & Chat
- [x] Messaggi community pubblici multilingua
- [x] Utenti online con pallino verde
- [x] Chat privata 1:1 tra utenti
- [x] Lista conversazioni

### Dizionario Biblico
- [x] 106+ termini ebraici/greci/aramaici
- [x] Ricerca AI con GPT-4o
- [x] Preferiti e Flashcards

### I Miei Contenuti
- [x] Tab Segnalibri/Note/Evidenziati
- [x] Azioni: elimina, vai al versetto

### I Miei Amici
- [x] Gestione utenti preferiti
- [x] Stato online/offline
- [x] Chat diretta

## API Endpoints

### Mood Checkin
- `POST /api/ai/mood-checkin` - Restituisce versetto E riflessione diversi ad ogni chiamata
  - Input: `{mood: "happy"|"hopeful"|..., language: "it"|"en"|...}`
  - Output: `{mood, verse: {ref, text}, reflection, language}`
  - Mapping automatico chiavi EN→lingua selezionata

### Progress
- `GET /api/progress` - Statistiche generali
- `GET /api/progress/reading/history?limit=N` - Cronologia letture

## Recent Changes

### 2026-02-18 - Session 6
- **Mood Checkin Fix**: Aggiunto mapping chiavi inglesi (happy, hopeful, sad...) → chiavi per lingua (felice, speranzoso, triste...)
- **Versetti dinamici**: Ogni tocco = versetto diverso + riflessione AI diversa
- **Loading state**: Aggiunto indicatore durante il caricamento
- **Schermata Progressi**: Nuova `/reading-progress` con stats e cronologia
- **Profilo**: Stats cliccabili con Link/Pressable per web compatibility
- **Link Bibbia**: Ogni voce cronologia porta al capitolo

### Testing Results
- iteration_26: 100% backend (12/12), 70% frontend (navigation fix applied)

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## Remaining Tasks

### P1
- [ ] Notifiche push dinamiche e tradotte

### Refactoring
- [ ] Suddividere server.py in moduli
