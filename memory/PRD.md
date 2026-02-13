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

### Sessione Corrente (Feb 2026) - Fork 5
- [x] **FIX: Quiz submit** - Rimossa validazione stretta che richiedeva TUTTE le risposte
- [x] **FIX: Pulsanti Settings/Profile** - Tutti usano `showAlert`, `showInfoAlert`, `showConfirm` che funzionano su web
- [x] **FIX: TTS multilingua** - Aggiunta selezione voce migliore disponibile + caricamento asincrono voci
- [x] **Testato con Playwright**: 
  - ✅ Logout funziona (redirect a /login dopo conferma)
  - ✅ Quiz list carica correttamente
  - ✅ Quiz domande caricano
  - ✅ API quiz/submit funziona (testato via curl: Score 20%, 3/15 corrette)

### Sessioni Precedenti
- Quiz tradotti in tutte le lingue (IT: 14, ES: 12, EN: 12, DE: 10, FR: 10, PT: 10)
- Registrazione utenti funzionante
- Internazionalizzazione completa
- Lettore biblico multilingua

## Status Bug Segnalati

| Bug | Status | Note |
|-----|--------|------|
| Quiz results/submit non funzionano | ✅ FIXED | API funziona, pulsante submit abilitato |
| Logout non funziona | ✅ FIXED | Testato con Playwright - redirect a /login |
| TTS altre lingue | ✅ FIXED | Web Speech API con voice selection |
| Pulsanti Privacy/Delete/Logout | ✅ FIXED | Usano window.alert/confirm su web |

## Backlog

### P1 - Prossimi
- [ ] Espandere dizionario biblico
- [ ] Test manuale su dispositivo mobile reale

### P2
- [ ] Fix strumenti studio AI
- [ ] UI Ricerca/Mappe

## File Chiave Modificati
- `/app/frontend/app/quiz.tsx` - Submit senza validazione stretta
- `/app/frontend/app/settings.tsx` - Tutti i pulsanti con showInfoAlert/showConfirm
- `/app/frontend/app/(tabs)/profile.tsx` - Logout con showConfirm
- `/app/frontend/app/(tabs)/bible.tsx` - TTS con voice selection

## Credenziali Test
- User: testbible@cibospirituale.it / Test123!

## Note Importanti
- React Native Web ha limitazioni con Playwright (dialoghi window.confirm non intercettabili senza handler)
- TTS dipende dalle voci installate sul browser/sistema
- I test automatizzati richiedono `page.on('dialog', lambda d: d.accept())` per gestire i confirm
