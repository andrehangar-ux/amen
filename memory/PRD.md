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

### Sessione Corrente (Feb 2026) - Fork 7/8

#### ✅ Logo App Personalizzato (COMPLETATO)
- [x] **Logo colomba bianca** su sfondo verde oliva con scritta "Amen!"
- [x] Integrato nella pagina di **login** (120x120px, angoli arrotondati)
- [x] Integrato nella pagina di **registrazione** (100x100px, angoli arrotondati)
- [x] File salvato in `/app/frontend/assets/images/logo.jpg`

#### ✅ Schermata Risultati Quiz Migliorata (COMPLETATO)
- [x] **Emoji dinamica** basata sul punteggio:
  - 🏆 ≥80% (Ottimo lavoro!)
  - ⭐ ≥60% (Buon risultato!)
  - 📚 ≥40% (Continua a studiare!)
  - 💪 <40% (Continua a studiare!)
- [x] **Statistiche visive** corrette/errate con icone
- [x] **Pulsante "Visualizza Tutte le Risposte"** per vedere il dettaglio completo
- [x] **Sezione Risposte Errate** con:
  - Domanda
  - Tua risposta (con icona ❌)
  - Risposta corretta (con icona ✅)
  - Spiegazione dettagliata
  - Riferimento al versetto biblico
- [x] **Sezione Risposte Corrette** con spiegazioni per approfondimento
- [x] Traduzioni complete in 6 lingue

#### ✅ Internazionalizzazione Completa (i18n) (COMPLETATO)
- [x] **~200+ chiavi di traduzione** per tutte le 6 lingue
- [x] File aggiornati: bible.tsx, community.tsx, forum.tsx, radio.tsx, settings.tsx, quiz.tsx
- [x] Sistema centralizzato in `/app/frontend/src/store/languageStore.ts`

### Testing
- **Backend**: 100% test passati
- **Frontend**: 90%+ test passati (logo e quiz verificati)

### Sessioni Precedenti
- Dizionario Biblico (69 termini con traduzione AI on-demand)
- Sistema Preferiti e Flashcard
- Quiz tradotti in tutte le lingue
- TTS multilingua con Web Speech API

## Backlog

### P1 - Prossimi
- [ ] Fix strumenti studio AI in bible.tsx (Spiega con AI, Evidenzia) - **Bug ricorrente**

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
