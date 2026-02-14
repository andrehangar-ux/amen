# Amen! - PWA Cristiana Multilingua

## Problema Originale
App cristiana PWA "Amen!" con lettore biblico multilingua, quiz, dizionario biblico, strumenti di studio AI, diario spirituale e radio.

## Architettura
- **Backend**: FastAPI + MongoDB (Motor) - `/app/backend/server.py`
- **Frontend**: React Native + Expo + Expo Router + TypeScript + Zustand
- **Database**: MongoDB `test_database`
- **AI**: OpenAI GPT-4o via Emergent LLM Key

## Lingue Supportate
it, en, es, de, fr, pt (6 lingue con TTS)

## Cosa è stato implementato

### Sessione Corrente (Feb 2026) - Fork 12

#### ✅ CRONOLOGIA LETTURA MULTILINGUA (COMPLETATO)
- [x] Sezione "Cronologia Lettura" nel profilo
- [x] Traduzioni complete in 6 lingue
- [x] Click su capitolo → apre lettura biblica
- [x] Mostra libro, capitolo, conteggio letture, data
- [x] Endpoint `/api/progress/reading/chapter` e `/api/progress/reading/history`

#### ✅ PRIVACY E TERMINI - GDPR COMPLIANCE (COMPLETATO)
- [x] Pagina `/privacy` con documentazione legale completa
- [x] **Termini e Condizioni (T&C)**:
  - Licenza d'uso SaaS non esclusiva
  - Divieto Reverse Engineering, Model Scraping, Prompt Injection
  - Clausola risoluzione automatica
  - Safe Harbor Clause per manleva
  - Limitazione responsabilità
- [x] **Privacy Policy GDPR 2026**:
  - Titolare: Andrea Hangar (andrehangar@live.it)
  - Modalità Ephemeris (cancellazione post-sessione)
  - Standard C2PA per metadati crittografici
  - Threshold originalità 15%
- [x] **Tabella Dati Trattati**:
  - Email, Nome, Preferenze, Hash password, Log consenso, Prompt AI
  - Base giuridica per ogni dato (Art. 6.1.a/b/c/f)
- [x] **Trasparenza AI** (Art. 22 GDPR / EU AI Act):
  - Dichiarazione uso GPT-4o
  - Limitazioni note
- [x] **Diritti Utente** (Artt. 15-22 GDPR):
  - Accesso, Rettifica, Cancellazione, Limitazione, Portabilità, Opposizione
  - Procedura richiesta (30 giorni)
- [x] **Protocollo Consenso Click-wrap**:
  - Log timestamp, hash documento (SHA-256), IP mascherato
  - No pre-tick (GDPR compliance)
  - Badge "Accettato" verde dopo accettazione
- [x] Endpoint API: `/api/consent/status`, `/api/consent/accept`, `/api/consent/withdraw`

### Sessione Precedente (Fork 11)

#### ✅ FIX QUIZ, TTS, CRONOLOGIA, FLUIDITÀ
- [x] Quiz caricamento parallelo (~2s)
- [x] TTS migliorato con selezione voice robusta
- [x] Cronologia lettura con click per riprendere
- [x] API response times ~0.1-0.3s

### Sessioni Precedenti
- Traduzione 1000 domande quiz on-demand
- Statistiche fine quiz con correzioni
- Quiz 1000 domande in 33 categorie
- Login Biometrico
- Dizionario Biblico (69 termini)
- Sistema Preferiti e Flashcard

## Database Collections
- `consent_logs` - Log consensi GDPR (NUOVO)
- `reading_history` - Cronologia capitoli letti
- `quiz_translations_cache` - Cache traduzioni quiz
- `dictionary_translations` - Cache traduzioni AI
- `dictionary_favorites` - Preferiti utente
- `dictionary_flashcards` - Flashcard SM-2
- `bible_cache` - Cache capitoli Bibbia
- `users` - Utenti
- `progress` - Progressi utente
- `quiz_history` - Storico quiz

## Backlog

### P1 - Prossimi
- [ ] UI Ricerca Globale (`/app/frontend/app/search.tsx`)
- [ ] UI Mappe Bibliche (`/app/frontend/app/maps.tsx`)

### P2
- [ ] Menu Personalizzazione UI (temi e font)
- [ ] Logo applicazione

## File Chiave

### Backend
- `/app/backend/server.py` - API principale

### Frontend
- `/app/frontend/app/(tabs)/profile.tsx` - Profilo con traduzioni e cronologia
- `/app/frontend/app/privacy.tsx` - Pagina Privacy e Termini GDPR
- `/app/frontend/app/quiz.tsx` - UI quiz ottimizzata
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore con TTS migliorato

## API Endpoints

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/consent/status` | GET | Status consenso utente |
| `/api/consent/accept` | POST | Accetta T&C con audit trail |
| `/api/consent/withdraw` | DELETE | Revoca consenso (GDPR Art. 17) |
| `/api/progress/reading/chapter` | POST | Salva capitolo letto |
| `/api/progress/reading/history` | GET | Cronologia lettura |
| `/api/quiz/categories` | GET | Lista categorie |
| `/api/quiz/category/{id}` | GET | Quiz per categoria |
| `/api/quiz/submit` | POST | Invia risposte quiz |

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Titolare Trattamento Dati
- Nome: Andrea Hangar
- Email: andrehangar@live.it

## Test Reports
- `/app/test_reports/iteration_12.json` - 17/17 test passati
