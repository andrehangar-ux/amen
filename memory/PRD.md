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
- Versetto del giorno dinamico
- Note e segnalibri personali
- TTS (Text-to-Speech) per lettura ad alta voce

### Protezione Minori (Families Policy Compliance)
**Implementato completamente per conformità Google Play Families Policy:**

1. **Blocco Chat con Sconosciuti**
   - I minori (<18 anni) possono chattare SOLO con amici aggiunti
   - Verifica automatica su `/api/private-messages`

2. **Promemoria Sicurezza In-App**
   - Modal prominente mostrato PRIMA di accedere alle funzionalità social
   - Messaggio multilingue con consigli di sicurezza chiari
   - Richiede conferma esplicita dell'utente
   - Tracciato con `safety_reminder_shown` per non ripeterlo

3. **Controllo Genitori Completo**
   - **PIN Genitore**: PIN 4-6 cifre per proteggere le impostazioni
   - **Abilita/Disabilita Social**: Toggle per attivare/disattivare community e chat
   - **Livelli di Funzionalità**: "Solo Amici" o "Disabilitato"
   - **Condivisione Media**: Toggle per permettere/bloccare invio immagini
   - Sezione dedicata nelle Impostazioni

4. **Verifica Età**
   - Campo `birth_date` obbligatorio alla registrazione
   - Calcolo automatico età e status `is_minor`

### API Controllo Genitori
- `GET /api/parental-controls/status` - Stato attuale
- `POST /api/parental-controls/set-pin` - Imposta PIN
- `POST /api/parental-controls/verify-pin` - Verifica PIN
- `PUT /api/parental-controls/update` - Aggiorna impostazioni
- `GET /api/parental-controls/can-use-social` - Verifica permessi social

### Modalità Offline
- Caching Bibbia, Quiz e Note tramite AsyncStorage
- Rilevamento rete con NetInfo
- UI dedicata nelle impostazioni

### Community
- Post pubblici e commenti
- Chat privata (solo tra amici per minori)
- Sistema amicizie
- **BLOCCO**: Se controllo genitori disabilita social, mostra schermata di blocco

### AdMob Integration
- File app-ads.txt: `google.com, pub-1876565863299921, DIRECT, f08c47fec0942fa0`
- Endpoint `/app-ads.txt` attivo

## Sessione Corrente (Dicembre 2025)

### Completato
- [x] Miglioramento articolazione domande quiz (rimosse formule "Completa:...")
- [x] File app-ads.txt per AdMob
- [x] **Sistema Controllo Genitori Completo**:
  - UI nelle Impostazioni con PIN protection
  - Toggle social features, livelli interazione, media sharing
  - Modal sicurezza PRIMA di accesso alla community
  - Blocco schermata se social disabilitato
- [x] Endpoint API per controllo genitori
- [x] Integrazione frontend/backend completa

### In Progress
- [ ] 365 versetti giornalieri (attualmente ~110, usa modulo per ciclare)

## Task Futuri (Backlog)
1. **P1**: Completare 365 versetti giornalieri
2. **P1**: Notifiche push con versetto del giorno dinamico
3. **P1**: Gruppi di studio privati
4. **P1**: Lista amici/preferiti completa
5. **P1**: UI Ricerca Globale
6. **P2**: UI Mappe Bibliche
7. **P2**: Refactoring server.py (>5700 righe)

## Credenziali Test
- Email: `testbible@cibospirituale.it`
- Password: `Test123!`

## File Chiave Controllo Genitori
- `/app/backend/server.py` - Endpoint API (linee ~5620-5760)
- `/app/frontend/app/settings.tsx` - UI Controllo Genitori
- `/app/frontend/app/community.tsx` - Blocco e modal sicurezza
- `/app/frontend/src/utils/api.ts` - Funzioni API client
