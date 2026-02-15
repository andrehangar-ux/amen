# Amen! - Product Requirements Document

## Original Problem Statement
App cristiana per la lettura della Bibbia, diario spirituale, community e assistente AI.

## Core Features
- Lettura Bibbia multilingua (IT, EN, ES, DE, FR, PT)
- Text-to-Speech per la lettura
- Diario spirituale con mood tracking
- Community con utenti online e chat private
- Assistente AI (GPT-4o)
- Notifiche push per Versetto del Giorno
- Statistiche di lettura

## What's Been Implemented

### Session Feb 15, 2026
- **Bug Fix: Pulsanti Profilo** - DONE
  - Pulsanti "Disconnetti" e "Elimina Account" ora funzionano correttamente su web
  - Modificato showConfirm() con setTimeout per compatibilità browser
  - Aggiunto activeOpacity e data-testid ai MenuItem
  - Files: frontend/app/(tabs)/profile.tsx

- **Bug Fix: Traduzione Tedesca** - DONE
  - Aggiunto versetti biblici in tedesco (de) in SAMPLE_VERSES_MULTILANG
  - Aggiunto versetti mood in tedesco (de) in MOOD_VERSES_MULTILANG
  - Files: backend/server.py

- **Bug Fix: Icone App** - DONE
  - Aggiunto icone mancanti nel fallback emoji (school, journal, add-circle, albums, business, hand-left, library, logo-paypal, radio-button-on, repeat, save, swap-horizontal)
  - Files: frontend/src/components/Icon.tsx

### Session Dec 14, 2025
- **Termini e Condizioni (T&C)** - DONE
  - Modale bloccante che appare dopo il login se l'utente non ha accettato i T&C
  - Supporto multilingua (IT, EN, ES, DE, FR, PT)
  - Integrazione con backend API esistenti (/api/consent/status, /api/consent/accept)
  - Flow: login -> check consent -> if false, show modal -> after accept, navigate to tabs
  - Files: frontend/app/(tabs)/index.tsx, frontend/app/index.tsx, frontend/src/components/TermsModal.tsx

### Previous Sessions
- Community con utenti online e chat private - DONE
- Text-to-Speech migliorato - DONE
- Pagina statistiche di lettura (/progress) - DONE
- Build fixes e stabilizzazione - DONE

## Prioritized Backlog

### P1 - High Priority
- **Notifiche Push Versetto del Giorno**: Completare la logica di scheduling e invio della notifica giornaliera

### P2 - Medium Priority
- Interfaccia Ricerca Globale (/app/frontend/app/search.tsx)
- Mappe Bibliche (/app/frontend/app/maps.tsx)
- Personalizzazione temi e font
- Miglioramenti sezione Community (più interattiva)
- Chat privata tra utenti
- Utenti online nella sezione Community

### P3 - Low Priority
- Investigare errori 520 intermittenti
- Refactoring languageStore.ts in file JSON separati

## Key Technical Stack
- Frontend: React Native, Expo, TypeScript, Zustand
- Backend: FastAPI, MongoDB
- AI: OpenAI GPT-4o
- External APIs: bible-api.com, laparola.net

## Key API Endpoints
- POST /api/auth/login
- POST /api/auth/logout
- DELETE /api/auth/delete-account
- GET /api/consent/status
- POST /api/consent/accept?version=X
- DELETE /api/consent/withdraw
- GET /api/bible/daily-verse?lang=XX
- GET /api/reading-progress
- POST /api/heartbeat
- GET /api/online-users
- POST /api/messages
- GET /api/messages/{other_user_id}

## Test Credentials
- Email: testbible@cibospirituale.it
- Password: Test123!

## Test Reports
- /app/test_reports/iteration_18.json (Bug fixes - PASS)
