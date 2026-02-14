# Amen! - App Biblica PWA

## Problema Originale
Creare un'app biblica completa con lettura della Bibbia, quiz, diario spirituale, strumenti di studio basati su IA, e funzionalità social.

## Funzionalità Implementate

### Sessione Corrente (Feb 2025) - Iterazione 15
- **TTS Migliorato**: Corretto il Text-to-Speech per la lettura della Bibbia in tutte le 6 lingue (IT, EN, ES, PT, FR, DE). Implementato con Web Speech API + expo-speech fallback, fix per bug Chrome, e selezione automatica della voce corretta
- **Messaggi Privati dalla Community**: Cliccando sull'avatar di un utente online si apre un modal per la chat privata. Include invio/ricezione messaggi in tempo reale
- **Utenti Online nella Community**: Sistema di heartbeat ogni 2 min, sezione utenti online con avatar, indicatore verde e icona chat per aprire conversazione privata

### Sessione Precedente - Iterazione 14
- Utenti Online nella Community
- Barra Azioni Rapide Community
- Notifiche Push Versetto del Giorno

### Backend API
- `POST /api/user/heartbeat` - Aggiorna stato online
- `GET /api/community/online-users` - Lista utenti online (ultimi 5 min)
- `POST /api/messages` - Invia messaggio privato
- `GET /api/messages/{user_id}` - Ottieni conversazione con utente
- `GET /api/messages` - Lista tutte le conversazioni

### Funzionalità Precedenti (Completate)
- Checkbox Termini e Condizioni nella registrazione
- Pulsante Elimina Account nel profilo (GDPR compliant)
- Login Automatico tramite AsyncStorage
- Traduzione on-demand delle 1000 domande del quiz
- Ottimizzazione performance sezione quiz
- Cronologia lettura nel profilo utente
- Pagina Privacy e Copyright con T&C completi
- Internazionalizzazione completa (6 lingue)

## Architettura

```
/app
├── backend/
│   ├── server.py               # FastAPI, endpoints autenticazione e CRUD
│   ├── quiz_1000_questions.py  # Logica quiz con traduzione
│   └── translation_service.py  # Servizio traduzione OpenAI
└── frontend/
    ├── app/
    │   ├── (auth)/register.tsx # Registrazione con checkbox T&C
    │   ├── (tabs)/
    │   │   ├── bible.tsx       # Lettura Bibbia con TTS migliorato
    │   │   └── profile.tsx     # Profilo con Elimina Account e Notifiche
    │   ├── community.tsx       # Community con utenti online e messaggi privati
    │   ├── privacy.tsx         # Pagina T&C e Privacy Policy
    │   └── quiz.tsx            # Sezione quiz ottimizzata
    └── src/
        ├── services/
        │   └── NotificationService.ts # Servizio notifiche push
        ├── store/
        │   ├── authStore.ts    # Gestione autenticazione
        │   └── languageStore.ts # Traduzioni multilingua
        └── utils/api.ts        # API client completo
```

## Database (MongoDB)
- `users`: Dati utenti
- `reading_history`: Progressi lettura
- `user_consent_log`: Log consenso privacy
- `quizzes_1000_translated`: Cache quiz tradotti
- `online_users`: Tracciamento utenti online
- `private_messages`: Messaggi privati tra utenti

## Credenziali Test
- Email: testbible@cibospirituale.it
- Password: Test123!

## Backlog (P2)
1. Interfaccia Ricerca Globale (`/search.tsx`)
2. Interfaccia Mappe Bibliche (`/maps.tsx`)
3. Personalizzazione temi e font
4. Selezione orario personalizzato per notifica versetto

## Integrazioni
- OpenAI GPT-4o (chiave LLM Emergent)
- bible-api.com, laparola.net
- Web Speech API per TTS
- expo-notifications per notifiche push

## Test Report
- Iterazione 15: 100% backend (10/10 test), 85% frontend
- File: /app/test_reports/iteration_15.json

## Note Tecniche TTS
Il TTS utilizza Web Speech API sul web con:
- Selezione automatica della voce per lingua (it-IT, en-US, es-ES, pt-BR, fr-FR, de-DE)
- Fix per bug Chrome (resume periodico, voices loading)
- Fallback su expo-speech per app native
- Logging dettagliato per debug (prefisso 'TTS:')
