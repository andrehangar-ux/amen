# Amen! - App Biblica PWA

## Problema Originale
Creare un'app biblica completa con lettura della Bibbia, quiz, diario spirituale, strumenti di studio basati su IA, e funzionalità social.

## Funzionalità Implementate

### Sessione Corrente (Feb 2025)
- **Checkbox Termini e Condizioni**: Aggiunta nella pagina di registrazione con validazione obbligatoria
- **Pulsante Elimina Account**: Aggiunto nel profilo utente con cancellazione completa da tutte le collection MongoDB (GDPR compliant)
- **Login Automatico**: Verificato funzionante tramite AsyncStorage e checkAuth()

### Sessioni Precedenti
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
    │   ├── (tabs)/profile.tsx  # Profilo con Elimina Account
    │   ├── privacy.tsx         # Pagina T&C e Privacy Policy
    │   └── quiz.tsx            # Sezione quiz ottimizzata
    └── src/
        ├── store/authStore.ts  # Gestione autenticazione con login automatico
        └── store/languageStore.ts # Traduzioni multilingua (IT, EN, ES, PT, FR, DE)
```

## Database (MongoDB)
- `users`: Dati utenti
- `reading_history`: Progressi lettura
- `user_consent_log`: Log consenso privacy
- `quizzes_1000_translated`: Cache quiz tradotti

## API Key
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

## Integrazioni
- OpenAI GPT-4o (chiave LLM Emergent)
- bible-api.com, laparola.net
- Web Speech API per TTS
