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

### Protezione Minori
- Campo data di nascita obbligatorio alla registrazione
- Blocco chat privata con sconosciuti per utenti <18 anni
- Modal di sicurezza e consenso genitoriale
- Verifica età per condivisione info personali

### Modalità Offline
- Caching Bibbia, Quiz e Note tramite AsyncStorage
- Rilevamento rete con NetInfo
- UI dedicata nelle impostazioni

### Community
- Post pubblici e commenti
- Chat privata (solo tra amici per minori)
- Sistema amicizie

### AdMob Integration
- File app-ads.txt configurato: `google.com, pub-1876565863299921, DIRECT, f08c47fec0942fa0`
- Endpoint `/app-ads.txt` attivo

## Sessione Corrente (Dicembre 2025)

### Completato
- [x] Miglioramento articolazione domande quiz (rimosse formule "Completa:..." in IT, ES, EN, PT)
- [x] File app-ads.txt per AdMob creato e servito via endpoint
- [x] Menu fluttuante globale funzionante
- [x] Compatibilità Android 15 (Edge-to-Edge)
- [x] Protezione minori completa

### In Progress
- [ ] 365 versetti giornalieri (attualmente ~110, usa modulo per ciclare)
- [ ] Funzionalità copia testo Bibbia (già presente via "Condividi")

## Task Futuri (Backlog)
1. **P1**: Notifiche push con versetto del giorno dinamico
2. **P1**: Gruppi di studio privati
3. **P1**: Lista amici/preferiti completa
4. **P1**: UI Ricerca Globale
5. **P2**: UI Mappe Bibliche
6. **P2**: Refactoring server.py (>5700 righe)

## Credenziali Test
- Email: `testbible@cibospirituale.it`
- Password: `Test123!`

## File Chiave
- `/app/backend/server.py` - API principale
- `/app/backend/quiz_data.py` - Domande quiz multilingue
- `/app/backend/data/daily_verses.py` - Versetti giornalieri
- `/app/frontend/app/(tabs)/bible.tsx` - Schermata Bibbia
- `/app/frontend/src/components/FloatingMenu.tsx` - Menu globale
