# Amen! - PWA Cristiana Multilingua

## Problema Originale
App cristiana PWA "Amen!" con lettore biblico multilingua, quiz, dizionario biblico, strumenti di studio AI, diario spirituale e radio.

## Architettura
- **Backend**: FastAPI + MongoDB (Motor) - `/app/backend/server.py`
- **Frontend**: React Native + Expo + Expo Router + TypeScript + Zustand
- **Database**: MongoDB `test_database` (bible_cache, users, quiz_history, study_notes, progress)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Bible APIs**: laparola.net (IT), GitHub Bible JSON (EN/ES/DE/FR/PT), bible-api.com (fallback)

## Lingue Supportate
it, en, es, de, fr, pt (6 lingue con TTS: it-IT, en-US, es-ES, de-DE, fr-FR, pt-BR)

## Cosa è stato implementato

### Sessione Corrente (Feb 2026) - Fork 4
- [x] **FIX: Text-to-Speech multilingua** - Aggiunto supporto cross-platform:
  - Web: usa Web Speech API nativa (`window.speechSynthesis`)
  - Native: usa expo-speech
  - Modificati: `bible.tsx`, `index.tsx`, `feelings.tsx`
  - Tutte le lingue supportate con codici TTS corretti
- [x] **FIX: Registrazione utenti** - Sostituito `Alert.alert` con `showAlert` helper che usa `window.alert` su web
- [x] Test: 9/9 test auth passati (register, login, logout, delete-account)

### Sessione Precedente - Fork 3
- [x] FIX: Pulsanti Esci/Elimina Account con `window.confirm` su web
- [x] FIX: Quiz tradotti in tutte le lingue (IT: 14, ES: 12, EN: 12, DE: 10, FR: 10, PT: 10)
- [x] FIX: Errore ObjectId `/api/progress`

### Sessione Fork 2
- [x] Internazionalizzazione Quiz e Home
- [x] 30+ chiavi traduzione in languageStore

### Sessione Fork 1
- [x] Fix critico cambio lingua Bibbia
- [x] Backend dizionario multilingua

### Sessioni Precedenti
- [x] Auth JWT (login/register)
- [x] Lettore biblico multilingua con 37 libri
- [x] AI spiegazione versetti (GPT-4o)
- [x] Diario spirituale
- [x] Radio cristiane

## Backlog Prioritizzato

### P1 - Prossimi
- [ ] Espandere dizionario biblico con più termini
- [ ] Tradurre completamente pagina Settings

### P2
- [ ] Fix strumenti di studio (AI, Evidenziazione, Segnalibri) - da verificare
- [ ] Ricerca dizionario multilingua

### P3 - Futuro
- [ ] Implementare UI Ricerca Globale
- [ ] Implementare UI Mappe Bibliche
- [ ] Creare logo app ("Amen!" con colomba bianca)

## File Chiave
- `/app/backend/server.py` - API principale
- `/app/backend/quiz_data.py` - Quiz multilingua (750+ domande in 6 lingue)
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore biblico con TTS cross-platform
- `/app/frontend/app/(auth)/register.tsx` - Form registrazione con showAlert cross-platform
- `/app/frontend/src/store/languageStore.ts` - Store lingua con tts_code per ogni lingua

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Test Reports
- /app/test_reports/iteration_4.json - Backend 9/9 auth tests passed, TTS verified
