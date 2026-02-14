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

### Sessione Corrente (Feb 2026) - Fork 10

#### ✅ QUIZ 1000 DOMANDE - SOTTOCATEGORIE TEMATICHE (COMPLETATO)
- [x] **1000 domande** parsate dal file `qiuz bibbia.txt` fornito dall'utente
- [x] **33 categorie tematiche** create automaticamente:
  - Abramo, Apocalisse, Conquista e Giudici, Donne della Bibbia
  - Elia ed Eliseo, Esilio e Ritorno, Ezechiele e Daniele
  - Feste e Culto, Formazione del Canone, Geremia
  - Giacobbe e Giuseppe, I Vangeli, Isaia, L'Alleanza
  - L'Apostolo Paolo, L'Esodo, La Chiesa Nascente
  - La Creazione, La Torah, La Vita di Gesù
  - Lingue e Termini, Lo Scisma, Manoscritti e Traduzioni
  - Miracoli e Parabole, Noè e il Diluvio
  - Passione e Risurrezione, Profeti Minori
  - Salmi e Sapienza, Salomone, Sansone e Samuele
  - Saul e Davide, Storia e Luoghi, Teologia Biblica
- [x] **30 domande per quiz** (limite per sessione)
- [x] **Traduzioni titoli categorie** in tutte e 6 le lingue
- [x] **Nuova UI con 3 tab**: Quiz Tematici (default), Quiz Classici, Studio Avanzato
- [x] **Info banner** che mostra "1000 domande in 33 categorie"
- [x] **API endpoints**:
  - `GET /api/quiz/categories?lang={lang}` - lista categorie
  - `GET /api/quiz/category/{id}?lang={lang}` - domande per categoria
- [x] **File creati**:
  - `/app/backend/quiz_1000.py` - modulo per gestione categorie
  - `/app/backend/quiz_categories_data.json` - dati JSON delle 1000 domande

#### Testing Quiz 1000:
- **Backend**: 15/15 test passati (100%)
- **Frontend**: 100% funzionante

### Sessione Precedente (Fork 9)

#### ✅ Traduzioni MoodSelector e Sezioni (COMPLETATO)
- [x] **MoodSelector tradotto** in tutte le 6 lingue
- [x] **Sezioni home tradotte**
- [x] **Login/Registrazione tradotti**

#### ✅ Login Biometrico (COMPLETATO)
- [x] **BiometricService** creato
- [x] Supporto impronta digitale e riconoscimento facciale
- [x] Salvataggio credenziali sicuro

#### ✅ Fix Icone Web (COMPLETATO)
- [x] Componente `Icon.tsx` con fallback a emoji per Expo Web

### Testing
- **Backend**: 100% test passati
- **Frontend**: 100% test passati
- **Strumenti Studio IA**: ✅ Verificati funzionanti

## Problemi Risolti in Questa Sessione

### ✅ Icone Web (RISOLTO)
- Creato componente `Icon.tsx` con fallback emoji per Expo Web
- Le icone ora mostrano emoji chiari invece di quadrati vuoti

### ✅ Strumenti Studio IA (VERIFICATO FUNZIONANTE)
- Testato l'intero flusso: selezione versetto → apertura tools → AI Spiega
- L'API `/api/bible/study/ai-explain` risponde correttamente
- Modal AI funziona e genera spiegazioni in tutte le lingue

### ✅ Bandiere Lingua (VERIFICATO PRESENTI)
- Bandiere presenti nel selettore lingua in settings.tsx
- 🇮🇹 IT, 🇪🇸 ES, 🇬🇧 EN, 🇧🇷 PT, 🇫🇷 FR, 🇩🇪 DE

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
