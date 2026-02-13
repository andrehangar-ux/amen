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

### Sessione Corrente (Feb 2026) - Fork 9

#### ✅ Traduzioni MoodSelector e Sezioni (COMPLETATO)
- [x] **MoodSelector tradotto** in tutte le 6 lingue
  - Felice, Triste, Ansioso, Arrabbiato, Grato, Confuso, Speranzoso, Stanco
- [x] **Sezioni home tradotte**: "Come ti senti oggi?", "Azioni Rapide", "Il Tuo Progresso", "Esplora"
- [x] **Login/Registrazione tradotti** con tutti i messaggi di errore

#### ✅ Login Biometrico (COMPLETATO)
- [x] **BiometricService** creato (`/app/frontend/src/services/BiometricService.ts`)
- [x] Supporto per **impronta digitale** e **riconoscimento facciale**
- [x] **Salvataggio credenziali sicuro** con `expo-secure-store`
- [x] **Login automatico** con biometria se abilitato
- [x] **Traduzioni biometria** in 6 lingue

#### ✅ Registrazione Migliorata (COMPLETATO)
- [x] **Opzione biometria** nella registrazione (visibile solo su mobile)
- [x] **Switch** per abilitare/disabilitare accesso con impronta
- [x] **Tutti gli utenti salvati** nel database MongoDB (21 utenti attualmente)

#### ⚠️ Problema Icone (NOTO)
- Icone Ionicons mostrano quadrati vuoti su Expo Web
- Problema noto con caricamento font CDN
- Funziona correttamente su dispositivi mobili nativi

### Sessioni Precedenti

#### ✅ Logo App Personalizzato (Fork 7/8)
- [x] **Logo colomba bianca** su sfondo verde oliva con scritta "Amen!"
- [x] Integrato nelle pagine login/registrazione

#### ✅ Schermata Risultati Quiz Migliorata (Fork 7/8)
- [x] Emoji dinamica basata sul punteggio
- [x] Statistiche visive corrette/errate
- [x] Sezione risposte errate con spiegazioni

#### ✅ Internazionalizzazione Completa (Fork 7/8)
- [x] ~200+ chiavi di traduzione per 6 lingue

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
