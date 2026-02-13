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
- [x] API endpoints dictionary completamente funzionanti

#### ✅ Sistema Preferiti Dizionario (COMPLETATO)
- [x] `GET /api/dictionary/favorites` - Lista preferiti utente
- [x] `POST /api/dictionary/favorites` - Aggiungere termine
- [x] `DELETE /api/dictionary/favorites/{term_id}` - Rimuovere
- [x] `GET /api/dictionary/favorites/check/{term_id}` - Verificare se preferito
- [x] Tabs "Tutti (69)" e "Preferiti (N)" nel frontend
- [x] Icona cuore nei dettagli termine

#### ✅ Sistema Flashcard con Ripetizione Spaziata (COMPLETATO)
- [x] `GET /api/dictionary/flashcards` - Lista flashcard utente
- [x] `POST /api/dictionary/flashcards` - Creare flashcard da termine
- [x] `PUT /api/dictionary/flashcards/{id}/review?quality=N` - Recensire (SM-2)
- [x] `DELETE /api/dictionary/flashcards/{id}` - Eliminare
- [x] `GET /api/dictionary/flashcards/stats` - Statistiche studio
- [x] `GET /api/dictionary/flashcards/due` - Flashcard da rivedere
- [x] **Pagina dedicata /flashcards** con modalità studio
- [x] **Algoritmo SM-2** per calcolo intervalli ripetizione
- [x] **Livelli padronanza 0-5** con colori distintivi

### Testing
- **Backend**: 30/30 test passati (100%)
- **Frontend**: UI verificata completamente
- **Bug fix**: Corretto ordine routes in server.py

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
| Logout non funziona | ✅ FIXED | Testato |
| TTS altre lingue | ✅ FIXED | Web Speech API |

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
- `/app/backend/server.py` - API principale (incluso favorites/flashcards)
- `/app/backend/biblical_dictionary.py` - 69 termini del dizionario
- `/app/backend/quiz_data.py` - Dati quiz multilingue
- `/app/backend/tests/test_favorites_flashcards.py` - Test automatici

### Frontend
- `/app/frontend/app/dictionary.tsx` - UI dizionario con preferiti
- `/app/frontend/app/flashcards.tsx` - Pagina studio flashcards
- `/app/frontend/app/quiz.tsx` - Quiz con submit
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore Bibbia con TTS

## Database Collections
- `dictionary_translations` - Cache traduzioni AI
- `dictionary_favorites` - Preferiti utente
- `dictionary_flashcards` - Flashcard con dati SM-2
- `bible_cache` - Cache capitoli Bibbia
- `users` - Utenti
- `quiz_history` - Storico quiz

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Note Tecniche
- Traduzione AI usa `emergentintegrations.llm.chat.LlmChat` con modello `gpt-4o`
- Algoritmo SM-2 per flashcard: qualità 0-2 = reset, 3-5 = incremento
- Intervalli: 1, 2, 4, 8, 16, 32 giorni basati su livello padronanza
