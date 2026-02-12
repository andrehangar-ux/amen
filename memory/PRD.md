# Amen! - PWA Cristiana Multilingua

## Problema Originale
App cristiana PWA "Amen!" con lettore biblico multilingua, quiz, dizionario biblico, strumenti di studio AI, diario spirituale e radio.

## Architettura
- **Backend**: FastAPI + MongoDB (Motor) - `/app/backend/server.py`
- **Frontend**: React Native + Expo + Expo Router + TypeScript + Zustand
- **Database**: MongoDB `test_database` (bible_cache, users, quiz_history, study_notes)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Bible APIs**: laparola.net (IT), GitHub Bible JSON (EN/ES/DE/FR/PT), bible-api.com (fallback)

## Lingue Supportate
it, en, es, de, fr, pt (6 lingue)

## Cosa è stato implementato

### Sessione Corrente (Feb 2026) - Fork 2
- [x] P0 - Completata internazionalizzazione (i18n) per Quiz e Home
  - Aggiunte 30+ nuove chiavi di traduzione in `languageStore.ts`
  - Tradotta sezione "Esplora" nella Home (Quiz Biblici, Dizionario, Forum, Mappe, Eventi Live)
  - Tradotti messaggi di errore, stati vuoti e etichette nel Quiz
  - Tradotti tutti i contenuti Quiz (titoli topic, descrizioni, domande, spiegazioni)
- [x] Tab bar completamente tradotta in tutte le 6 lingue
- [x] Sottotitolo "Mondiale" tradotto nella sezione Community
- [x] Fallback "Fratello/Brother/etc." tradotto nell'header

### Sessione Precedente (Feb 2026) - Fork 1
- [x] P0 - Fix critico cambio lingua Bibbia (da abbreviazione a indice posizionale)
- [x] Backend: Aggiunta lista libri tedeschi (de) in BIBLE_BOOKS_MULTILANG
- [x] Backend: Nuova funzione get_italian_book_name() per convertire nomi libri
- [x] Backend: Dizionario multilingua (DICT_TRANSLATIONS, DICT_TERM_TRANSLATIONS)
- [x] Frontend: Quiz usa lang param corrente nelle chiamate API
- [x] Frontend: Dizionario completamente tradotto
- [x] Test: 49/49 test passati (18 Bible + 31 Quiz/Dictionary)

### Sessioni Precedenti
- [x] Auth JWT (login/register)
- [x] Lettore biblico multilingua con 37 libri
- [x] Sistema quiz con domande multilingua
- [x] Dizionario biblico (8 termini ebraici/greci)
- [x] AI spiegazione versetti (GPT-4o)
- [x] Evidenziazione e segnalibri versetti
- [x] Diario spirituale
- [x] Radio cristiane
- [x] Navigazione link esterni con expo-web-browser

## Backlog Prioritizzato

### P1 - Prossimi
- [ ] Completare refactoring quiz (risultati dettagliati con correzioni/spiegazioni visibili)
- [ ] Espandere dizionario biblico (più di 8 termini, fonti Wikipedia)
- [ ] Tradurre pagina Settings in tutte le lingue

### P2
- [ ] Fix strumenti di studio (AI, Evidenziazione, Segnalibri) - verificare funzionamento
- [ ] Fix pulsanti Impostazioni (Logout, Elimina account) - verificare funzionamento
- [ ] Ricerca dizionario multilingua (attualmente solo italiano)

### P3 - Futuro
- [ ] Implementare UI Ricerca Globale
- [ ] Implementare UI Mappe Bibliche
- [ ] Creare logo app ("Amen!" con colomba bianca)
- [ ] Menu personalizzazione UI (temi, font)

## File Chiave
- `/app/backend/server.py` - API principale
- `/app/frontend/app/(tabs)/bible.tsx` - Lettore biblico
- `/app/frontend/app/quiz.tsx` - Schermata quiz con i18n completo
- `/app/frontend/app/dictionary.tsx` - Dizionario biblico
- `/app/frontend/app/(tabs)/_layout.tsx` - Layout tab con traduzioni
- `/app/frontend/app/(tabs)/index.tsx` - Home page con sezione Esplora tradotta
- `/app/frontend/src/utils/api.ts` - Client API
- `/app/frontend/src/store/languageStore.ts` - Store lingua con 30+ chiavi traduzione

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Test Reports
- /app/test_reports/iteration_1.json - 18/18 Bible tests passed
- /app/test_reports/iteration_2.json - 31/31 Quiz/Dictionary tests passed
