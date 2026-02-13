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

### Sessione Corrente (Feb 2026) - Fork 7

#### ✅ Internazionalizzazione Completa (i18n) (COMPLETATO)
- [x] **~200 chiavi di traduzione** per tutte le 6 lingue
- [x] **bible.tsx** - Pagina lettore Bibbia completamente tradotta
- [x] **community.tsx** - Pagina community tradotta
- [x] **forum.tsx** - Pagina forum tradotta
- [x] **radio.tsx** - Pagina radio tradotta (inclusi continenti)
- [x] **settings.tsx** - Pagina impostazioni tradotta
- [x] Sistema centralizzato in `/app/frontend/src/store/languageStore.ts`
- [x] Hook `useTranslation()` per accesso alle traduzioni

#### Chiavi tradotte per categoria:
- **Bible screen**: loadingBooks, chapters, editions, help, studyContextAvailable, yourNotes, note, aiExplain, highlight, share, bookmark, crossReferences, historicalContext, etc.
- **Community/Forum**: prayer, original, connectWithBrothers, communityForum, newPost, category, title, content, publish, etc.
- **Radio**: evangelicalRadios, allRadios, favorites, continents (europe, southAmerica, northAmerica, africa, asia, oceania)
- **Messaggi comuni**: noMessagesYet, noPostsYet, noGroupsFound, fillAllFields, unableToVote, etc.

### Sessioni Precedenti

#### ✅ Dizionario Biblico Espanso (Fork 6)
- [x] **69 termini** organizzati alfabeticamente (Ebraico, Greco, Aramaico)
- [x] **Traduzione AI on-demand** usando GPT-4o per tutte le 6 lingue
- [x] **Cache MongoDB** delle traduzioni per performance

#### ✅ Sistema Preferiti Dizionario (Fork 6)
- [x] API endpoints dictionary preferiti
- [x] Tabs "Tutti (69)" e "Preferiti (N)" nel frontend
- [x] Icona cuore nei dettagli termine

#### ✅ Sistema Flashcard con Ripetizione Spaziata (Fork 6)
- [x] API flashcard complete
- [x] Pagina dedicata /flashcards
- [x] Algoritmo SM-2 per ripetizione spaziata

### Testing
- **Backend**: 30/30 test passati (100%)
- **Frontend i18n**: 90%+ test passati

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
