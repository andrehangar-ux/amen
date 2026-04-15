# Amen! - App di Studio Biblico

## Descrizione
Applicazione mobile/web per lo studio della Bibbia con funzionalità multilingue, quiz interattivi, community e strumenti di studio avanzati.

## Stack Tecnologico
- **Frontend**: React Native (Expo) + TypeScript
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Integrazioni**: Emergent LLM Key, Resend, Expo Notifications

## Funzionalità Implementate

### Core Features
- Lettura Bibbia multilingue (IT, ES, EN, DE, FR, PT)
- Traduzioni multiple (Nuova Diodati, Reina Valera, KJV, etc.)
- Quiz biblici con 15+ categorie
- Sistema di autenticazione (email + Google)
- Profilo utente e preferenze
- Versetto del giorno dinamico (365 versetti, uno per ogni giorno dell'anno)
- Note e segnalibri personali
- TTS (Text-to-Speech) per lettura ad alta voce

### Gruppi di Studio Privati (NUOVO)
**Implementato completamente:**
- Creazione gruppi con nome e descrizione
- Chat di gruppo in tempo reale
- Condivisione versetti con note
- Studio biblico collaborativo (passaggio corrente sincronizzato)
- Invito membri (tutti i membri possono invitare)
- Ricerca utenti per invito
- Max 30 membri per gruppo
- **Completamente bloccato per minori**

**API Gruppi di Studio:**
- `POST /api/study-groups` - Crea gruppo
- `GET /api/study-groups` - Lista gruppi utente
- `GET /api/study-groups/{id}` - Dettagli gruppo
- `POST /api/study-groups/{id}/invite` - Invita membro
- `GET /api/study-groups/invites/pending` - Inviti pendenti
- `POST /api/study-groups/invites/{id}/respond` - Accetta/rifiuta
- `POST /api/study-groups/{id}/leave` - Lascia gruppo
- `POST/GET /api/study-groups/{id}/messages` - Messaggi
- `PUT /api/study-groups/{id}/study` - Aggiorna studio corrente
- `POST /api/study-groups/{id}/share-verse` - Condividi versetto
- `GET /api/study-groups/search-users` - Cerca utenti

### Protezione Minori (Google Play Families Policy - Compliant)
- Campo data di nascita obbligatorio
- **Social features DISABILITATE per default** per minori (non piu abilitate)
- **PIN Genitore OBBLIGATORIO** prima di qualsiasi accesso social
- **Safety reminder mostrato OGNI SESSIONE** (non piu una volta sola)
- **Chat solo con amici** (friends_only mode) — lista "Tutti gli utenti" nascosta per minori
- **Utenti online nascosti** per minori (no click su sconosciuti per DM)
- Controllo genitori con PIN: abilita/disabilita social, scegli livello, media sharing
- Backend: check minori su community post, private messages, study groups
- Messaggi di blocco chiari con indicazioni su ruolo genitore
- Gruppi di studio bloccati per minori senza approvazione parentale

### Modalità Offline
- Caching Bibbia, Quiz e Note tramite AsyncStorage
- Rilevamento rete con NetInfo
- UI dedicata nelle impostazioni

### AdMob Integration
- File app-ads.txt: `google.com, pub-1876565863299921, DIRECT, f08c47fec0942fa0`
- Endpoint `/app-ads.txt` attivo

## Sessione Corrente (Febbraio 2026)

### Completato
- [x] **365 versetti del giorno** - File completo con un versetto per ogni giorno dell'anno
- [x] **Gruppi di Studio Privati** - Sistema completo con chat, inviti, condivisione versetti
- [x] Articolazione migliorata domande quiz
- [x] File app-ads.txt per AdMob
- [x] **Fix app.json** - Rimossa `targetSdkVersion` da `android` per risolvere errore validazione schema EAS Build
- [x] **Testo Bibbia copiabile** - Aggiunto `selectable={true}` ai versetti in `bible.tsx`
- [x] **Package name** - Aggiornato a `com.amen.myapp` in app.json
- [x] **Digital Asset Links** - Endpoint `/.well-known/assetlinks.json` con SHA-256 fingerprint
- [x] **Families Policy Fix (Google Play)** - Rafforzato sistema protezione minori:
  - Social disabilitate per default per minori
  - PIN genitore obbligatorio prima di qualsiasi accesso social
  - Safety reminder ad ogni sessione (non piu una volta sola)
  - Chat solo con amici (lista sconosciuti nascosta)
  - Backend check su community post per minori

## Task Futuri (Backlog)
1. **P1**: Notifiche push con versetto del giorno dinamico
2. **P1**: Lista amici/preferiti completa
3. **P1**: UI Ricerca Globale
4. **P2**: UI Mappe Bibliche
5. **P2**: Refactoring server.py (>6000 righe)

## Credenziali Test
- Email: `testbible@cibospirituale.it`
- Password: `Test123!`

## File Chiave
- `/app/backend/server.py` - API principale (include gruppi di studio)
- `/app/backend/data/daily_verses.py` - 365 versetti giornalieri
- `/app/frontend/app/study-groups.tsx` - UI Gruppi di Studio
- `/app/frontend/src/components/FloatingMenu.tsx` - Menu con link ai gruppi
