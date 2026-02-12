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
it, en, es, de, fr, pt (6 lingue)

## Cosa è stato implementato

### Sessione Corrente (Feb 2026) - Fork 3
- [x] **FIX: Pulsanti Esci e Elimina Account** - Sostituito `Alert.alert` con `window.confirm` per supporto cross-platform (web + mobile)
- [x] **FIX: Quiz tradotti in tutte le lingue** - Aggiunte 8-10 categorie quiz per ogni lingua:
  - IT: 14 quiz (completo)
  - ES: 12 quiz (+8 nuovi: Éxodo, Hechos, Profetas, Apocalipsis, Personajes, Milagros, Beatitudes, Mandamientos)
  - EN: 12 quiz (+9 nuovi: Exodus, Acts, Prophets, Revelation, Characters, Miracles, Beatitudes, Commandments, Parables)
  - DE: 10 quiz (+8 nuovi: Psalmen, Exodus, Apostelgeschichte, Propheten, Offenbarung, Personen, Wunder, Seligpreisungen)
  - FR: 10 quiz (+8 nuovi: Psaumes, Exode, Actes, Prophètes, Apocalypse, Personnages, Miracles, Béatitudes)
  - PT: 10 quiz (+8 nuovi: Salmos, Êxodo, Atos, Profetas, Apocalipse, Personagens, Milagres, Bem-aventuranças)
- [x] **FIX: Errore ObjectId /api/progress** - Corretto bug serializzazione MongoDB

### Sessione Precedente (Feb 2026) - Fork 2
- [x] P0 - Completata internazionalizzazione (i18n) per Quiz e Home
- [x] Aggiunte 30+ chiavi traduzione in `languageStore.ts`
- [x] Tradotta sezione "Esplora" nella Home

### Sessione Fork 1
- [x] P0 - Fix critico cambio lingua Bibbia
- [x] Backend dizionario multilingua
- [x] Test: 49/49 test passati

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
- [ ] Menu personalizzazione UI (temi, font)

## File Chiave
- `/app/backend/server.py` - API principale
- `/app/backend/quiz_data.py` - Quiz multilingua (750+ domande in 6 lingue)
- `/app/frontend/app/(tabs)/profile.tsx` - Pulsante Esci con showConfirm
- `/app/frontend/app/settings.tsx` - Pulsanti Privacy/Delete con showConfirm
- `/app/frontend/src/store/languageStore.ts` - Store lingua con 50+ chiavi

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Test Reports
- /app/test_reports/iteration_3.json - Backend 18/18 passed, Quiz 10-14 per lingua
