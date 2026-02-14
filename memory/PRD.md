# Amen! - App Biblica PWA

## Problema Originale
Creare un'app biblica completa con lettura della Bibbia, quiz, diario spirituale, strumenti di studio basati su IA, e funzionalità social.

## Funzionalità Implementate

### Sessione Corrente (Feb 2025) - Iterazione 16
- **Pagina Progressi Completa**: Nuova pagina `/progress` accessibile cliccando sulle statistiche nel profilo. Mostra statistiche dettagliate (streak, capitoli letti, letture totali), attività recente, lista libri espandibile con capitoli letti cliccabili
- **API Statistiche Dettagliate**: Nuovi endpoint `/api/progress/stats` e `/api/progress/book/{book_name}` per ottenere progressi dettagliati

### Sessione Precedente - Iterazione 15
- TTS Migliorato per tutte le 6 lingue
- Messaggi Privati dalla Community
- Utenti Online con chat privata

### Backend API Nuovi
- `GET /api/progress/stats` - Statistiche complete di lettura
- `GET /api/progress/book/{book_name}` - Progressi per libro specifico

### Funzionalità Complete
- Pagina Progressi con statistiche dettagliate
- TTS Bibbia in 6 lingue
- Messaggi privati tra utenti
- Utenti online nella Community
- Notifiche push versetto del giorno
- Checkbox T&C nella registrazione
- Eliminazione account GDPR compliant
- Login automatico
- Quiz con 1000 domande tradotte
- Cronologia lettura nel profilo
- Internazionalizzazione completa (6 lingue)

## Architettura

```
/app
├── backend/
│   └── server.py               # FastAPI con nuovi endpoint progress
└── frontend/
    ├── app/
    │   ├── progress.tsx        # NUOVA pagina progressi dettagliati
    │   ├── (tabs)/
    │   │   ├── bible.tsx       # Lettura Bibbia con TTS
    │   │   └── profile.tsx     # Link alle statistiche espanse
    │   └── community.tsx       # Community con chat privata
    └── src/
        └── utils/api.ts        # getReadingStats, getBookProgress
```

## Database (MongoDB)
- `users`, `reading_history`, `progress`, `online_users`, `private_messages`

## Credenziali Test
- Email: testbible@cibospirituale.it
- Password: Test123!

## Backlog (P2)
1. Interfaccia Ricerca Globale (`/search.tsx`)
2. Interfaccia Mappe Bibliche (`/maps.tsx`)
3. Personalizzazione temi e font
4. Indicatori visivi capitoli letti nella selezione capitoli Bibbia

## Test Report
- Iterazione 16: 100% backend (10/10), 100% frontend
- File: /app/test_reports/iteration_16.json
