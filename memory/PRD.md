# Amen! - App Biblica PWA

## Problema Originale
Creare un'app biblica completa con lettura della Bibbia, quiz, diario spirituale, strumenti di studio basati su IA, e funzionalità social.

## Funzionalità Implementate

### Sessione Corrente (Feb 2025) - Iterazione 14
- **Utenti Online nella Community**: Implementato sistema di tracciamento utenti online con heartbeat ogni 2 minuti. La sezione Community mostra gli utenti attualmente connessi con avatar e indicatore verde
- **Barra Azioni Rapide Community**: Aggiunta barra con collegamenti rapidi a Bibbia, Quiz, Diario, Gruppi e Dizionario
- **Notifiche Push Versetto del Giorno**: Implementato servizio notifiche (NotificationService.ts) con toggle nel profilo utente per attivare/disattivare le notifiche giornaliere alle 08:00

### Backend API Nuovi
- `POST /api/user/heartbeat` - Aggiorna stato online dell'utente
- `GET /api/community/online-users` - Lista utenti online negli ultimi 5 minuti

### Sessioni Precedenti
- **Checkbox Termini e Condizioni**: Aggiunta nella pagina di registrazione con validazione obbligatoria
- **Pulsante Elimina Account**: Aggiunto nel profilo utente con cancellazione completa da tutte le collection MongoDB (GDPR compliant)
- **Login Automatico**: Verificato funzionante tramite AsyncStorage e checkAuth()
- Traduzione on-demand delle 1000 domande del quiz
- Ottimizzazione performance sezione quiz
- Correzione Text-to-Speech per varie lingue
- Cronologia lettura nel profilo utente
- Pagina Privacy e Copyright con T&C completi
- Internazionalizzazione della pagina profilo

## Architettura

```
/app
├── backend/
│   ├── server.py               # FastAPI, endpoint autenticazione e CRUD
│   ├── quiz_1000_questions.py  # Logica quiz con traduzione
│   └── translation_service.py  # Servizio traduzione OpenAI
└── frontend/
    ├── app/
    │   ├── (auth)/register.tsx # Registrazione con checkbox T&C
    │   ├── (tabs)/profile.tsx  # Profilo con Elimina Account e Notifiche
    │   ├── community.tsx       # Community con utenti online e azioni rapide
    │   ├── privacy.tsx         # Pagina T&C e Privacy Policy
    │   └── quiz.tsx            # Sezione quiz ottimizzata
    └── src/
        ├── services/
        │   └── NotificationService.ts # Servizio notifiche push
        ├── store/authStore.ts  # Gestione autenticazione con login automatico
        ├── store/languageStore.ts # Traduzioni multilingua (IT, EN, ES, PT, FR, DE)
        └── utils/api.ts        # API client con sendHeartbeat, getOnlineUsers
```

## Database (MongoDB)
- `users`: Dati utenti
- `reading_history`: Progressi lettura
- `user_consent_log`: Log consenso privacy
- `quizzes_1000_translated`: Cache quiz tradotti
- `online_users`: Tracciamento utenti online (nuovo)

## API Key Endpoints
- `POST /api/user/heartbeat`: Registra heartbeat utente online
- `GET /api/community/online-users`: Lista utenti online
- `DELETE /api/auth/delete-account`: Elimina account e tutti i dati utente
- `POST /api/consent/log`: Registra consenso
- `GET /api/consent/status`: Verifica stato consenso
- `POST/GET /api/reading_history`: Gestione cronologia lettura

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
- Iterazione 14: 100% backend (13/13 test), 95% frontend
- File: /app/test_reports/iteration_14.json
