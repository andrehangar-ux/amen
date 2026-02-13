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

### Sessione Corrente (Feb 2026) - Fork 6

#### ✅ Dizionario Biblico Espanso (COMPLETATO)
- [x] **69 termini** organizzati alfabeticamente (Ebraico, Greco, Aramaico)
- [x] **Traduzione AI on-demand** usando GPT-4o per tutte le 6 lingue
- [x] **Cache MongoDB** delle traduzioni per performance
- [x] **Etichette origine** tradotte (Hebrew/Hebreo/Hebräisch/Hébreu/Hebraico ecc.)
- [x] **API endpoints**:
  - `GET /api/dictionary?lang={lang}` - Lista 69 termini
  - `GET /api/dictionary/{term_id}?lang={lang}` - Dettaglio termine con traduzione
  - `GET /api/dictionary/search/{query}` - Ricerca termini
- [x] **Testing completo**: 28/28 test backend passati, frontend verificato

### Sessioni Precedenti
- Quiz tradotti in tutte le lingue (IT: 14, ES: 12, EN: 12, DE: 10, FR: 10, PT: 10)
- Registrazione utenti funzionante
- Internazionalizzazione completa
- Lettore biblico multilingua
- TTS multilingua con Web Speech API
- Pulsanti Logout/Privacy/Delete funzionanti

## Status Bug Segnalati

| Bug | Status | Note |
|-----|--------|------|
| Dizionario biblico "povero" | ✅ FIXED | Ora 69 termini con traduzione AI |
| Quiz results/submit | ✅ FIXED | API funziona |
| Logout non funziona | ✅ FIXED | Testato con Playwright |
| TTS altre lingue | ✅ FIXED | Web Speech API |
| Pulsanti Privacy/Delete | ✅ FIXED | window.alert/confirm su web |

## Backlog

### P1 - Prossimi
- [ ] Completare refactoring schermata risultati Quiz (mostrare correzioni dettagliate)
- [ ] Fix strumenti studio AI in bible.tsx (Spiega con AI, Evidenzia)

### P2
- [ ] UI Ricerca Globale
- [ ] UI Mappe Bibliche
- [ ] Logo applicazione (colomba bianca)

## File Chiave

### Backend
- `/app/backend/server.py` - API principale
- `/app/backend/biblical_dictionary.py` - 69 termini del dizionario
- `/app/backend/quiz_data.py` - Dati quiz multilingue

### Frontend
- `/app/frontend/app/dictionary.tsx` - UI dizionario
- `/app/frontend/app/quiz.tsx` - Quiz con submit
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore Bibbia con TTS
- `/app/frontend/app/settings.tsx` - Impostazioni

## Database Collections
- `dictionary_translations` - Cache traduzioni AI
- `bible_cache` - Cache capitoli Bibbia
- `users` - Utenti
- `quiz_history` - Storico quiz

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Note Tecniche
- Traduzione AI usa `emergentintegrations.llm.chat.LlmChat` con modello `gpt-4o`
- Cache MongoDB evita richieste AI ripetute
- React Native Web limitato: usa window.confirm invece di Alert.alert
- TTS dipende dalle voci installate sul browser/sistema
