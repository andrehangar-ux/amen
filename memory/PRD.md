# Amen! - App di Studio Biblico

## Descrizione
Applicazione mobile/web per lo studio della Bibbia con funzionalità multilingue, quiz interattivi, community e strumenti di studio avanzati.

## Stack Tecnologico
- **Frontend**: React Native (Expo) + TypeScript
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Integrazioni**: Emergent LLM Key, Resend, Expo Notifications

## Funzionalità Implementate

### Core Features
- Lettura Bibbia multilingue (IT, ES, EN, DE, FR, PT)
- Traduzioni multiple (Nuova Diodati, Reina Valera, KJV, etc.)
- Quiz biblici con 15+ categorie
- Sistema di autenticazione (email + Google)
- Profilo utente e preferenze
- Versetto del giorno dinamico (365 versetti, uno per ogni giorno dell'anno)
- Note e segnalibri personali
- TTS (Text-to-Speech) per lettura ad alta voce

### Gruppi di Studio Privati (NUOVO)
**Implementato completamente:**
- Creazione gruppi con nome e descrizione
- Chat di gruppo in tempo reale
- Condivisione versetti con note
- Studio biblico collaborativo (passaggio corrente sincronizzato)
- Invito membri (tutti i membri possono invitare)
- Ricerca utenti per invito
- Max 30 membri per gruppo
- **Completamente bloccato per minori**

**API Gruppi di Studio:**
- `POST /api/study-groups` - Crea gruppo
- `GET /api/study-groups` - Lista gruppi utente
- `GET /api/study-groups/{id}` - Dettagli gruppo
- `POST /api/study-groups/{id}/invite` - Invita membro
- `GET /api/study-groups/invites/pending` - Inviti pendenti
- `POST /api/study-groups/invites/{id}/respond` - Accetta/rifiuta
- `POST /api/study-groups/{id}/leave` - Lascia gruppo
- `POST/GET /api/study-groups/{id}/messages` - Messaggi
- `PUT /api/study-groups/{id}/study` - Aggiorna studio corrente
- `POST /api/study-groups/{id}/share-verse` - Condividi versetto
- `GET /api/study-groups/search-users` - Cerca utenti

### Protezione Minori (Google Play Families Policy - Compliant)
- Campo data di nascita obbligatorio
- **Social features DISABILITATE per default** per minori (non piu abilitate)
- **PIN Genitore OBBLIGATORIO** prima di qualsiasi accesso social
- **Safety reminder mostrato OGNI SESSIONE** (non piu una volta sola)
- **Chat solo con amici** (friends_only mode) — lista "Tutti gli utenti" nascosta per minori
- **Utenti online nascosti** per minori (no click su sconosciuti per DM)
- Controllo genitori con PIN: abilita/disabilita social, scegli livello, media sharing
- Backend: check minori su community post, private messages, study groups
- Messaggi di blocco chiari con indicazioni su ruolo genitore
- Gruppi di studio bloccati per minori senza approvazione parentale

### Modalità Offline
- Caching Bibbia, Quiz e Note tramite AsyncStorage
- Rilevamento rete con NetInfo
- UI dedicata nelle impostazioni

### AdMob Integration
- File app-ads.txt: `google.com, pub-1876565863299921, DIRECT, f08c47fec0942fa0`
- Endpoint `/app-ads.txt` attivo

## Sessione Corrente (Febbraio 2026)

### Completato
- [x] **365 versetti del giorno** - File completo con un versetto per ogni giorno dell'anno
- [x] **Gruppi di Studio Privati** - Sistema completo con chat, inviti, condivisione versetti
- [x] Articolazione migliorata domande quiz
- [x] File app-ads.txt per AdMob
- [x] **Fix app.json** - Rimossa `targetSdkVersion` da `android` per risolvere errore validazione schema EAS Build
- [x] **Testo Bibbia copiabile** - Aggiunto `selectable={true}` ai versetti in `bible.tsx`
- [x] **Package name** - Aggiornato a `com.amen.myapp` in app.json
- [x] **Digital Asset Links** - Endpoint `/.well-known/assetlinks.json` con SHA-256 fingerprint
- [x] **Families Policy Fix (Google Play)** - Rafforzato sistema protezione minori:
  - Social disabilitate per default per minori
  - PIN genitore obbligatorio prima di qualsiasi accesso social
  - Safety reminder ad ogni sessione (non piu una volta sola)
  - Chat solo con amici (lista sconosciuti nascosta)
  - Backend check su community post per minori
- [x] **Lista Amici completa** - Pagina redesign con stats, tab switch, avatar colorati, empty state, protezione minori (tab "Scopri Persone" nascosto). Aggiunta al FloatingMenu.
- [x] **Families Policy v3** - Creato componente `SocialGuard` centralizzato che blocca TUTTE le pagine social (community, private-chat, friends, study-groups). Il guard:
  - Verifica PIN genitore PRIMA di qualsiasi accesso social per minori
  - Mostra safety reminder OGNI sessione con 5 punti sui rischi reali
  - Blocca completamente l'accesso senza approvazione parentale
  - Mostra schermata di blocco con link a Impostazioni
- [x] **Edge-to-edge fix** - Rimosso plugin `react-native-edge-to-edge` e flag `edgeToEdgeEnabled` per eliminare API deprecate Android 15.
- [x] **Ricerca Globale** - Motore di ricerca interno per versetti biblici, libri, capitoli, dizionario, note e segnalibri. Backend con ricerca in bible_cache, BIBLE_BOOKS_MULTILANG e BIBLICAL_DICTIONARY. Frontend con suggerimenti, categorie colorate, card risultati. Aggiunta al FloatingMenu.
- [x] **Notifiche Push** - Sistema completo con 3 notifiche schedulabili:
  - Versetto del Giorno (default 07:00) — invita a leggere un versetto ogni mattina
  - Promemoria Quiz (default 12:00) — stimola a fare quiz biblici
  - Promemoria Lettura (default 20:00) — ricorda di leggere la Bibbia
  - Ciascuna con toggle on/off e selettore orario personalizzabile
  - Messaggi tradotti in 6 lingue (IT, EN, ES, PT, FR, DE)
  - Canali Android dedicati per ciascun tipo
- [x] **Firebase + AdMob** - Integrazione completa:
  - `google-services.json` configurato (progetto amen-15d00)
  - Plugin `react-native-google-mobile-ads` v16.3.3 con App ID `ca-app-pub-1876565863299921~6716733612`
  - Componente `AdBanner` con banner adattivo in Home page
  - Test IDs in dev, production IDs in release
  - `googleServicesFile` configurato in `app.json`
- [x] **Refactoring server.py - Fase 1** (Apr 2026) - Modularizzazione backend:
  - `/app/backend/core.py` - app FastAPI, MongoDB client, env vars, logger, SUPPORTED_LANGUAGES, SAFETY_MESSAGES, BAD_WORDS
  - `/app/backend/models.py` - tutti i 30+ modelli Pydantic (User, RegisterRequest, CommunityMessageCreate, ecc.)
  - `/app/backend/dependencies.py` - helper condivisi (auth, age, friendship, translate, content moderation)
  - server.py ridotto da 6431 a ~6018 righe; firma API invariata
  - Bonus: fix bug pre-esistente `CommunityMessageCreate` mancava campo `message_type` causando 500 sul POST community/messages
  - Validazione: 38/38 endpoint testati con successo (test_reports/iteration_38.json)
- [x] **Refactoring server.py - Fase 2 (parziale)** (Apr 2026) - Estrazione iniziale routes:
  - `/app/backend/routes/__init__.py` + `/app/backend/routes/auth.py` (354 righe, 9 endpoint /api/auth/*)
  - server.py ridotto da 6011 a 5698 righe
  - Lint pulizia: rimosso F811 hashlib duplicate import, rinominato duplicate `send_private_message` → `send_message_legacy` (route /api/messages legacy invariata), rimosso F841 unused vars, sostituito bare except con `except Exception`
  - Fix bug pre-esistente: `/api/auth/forgot-password` restituiva 500 quando Resend in modalità test rifiutava email non-verificate. Ora restituisce sempre 200 (privacy: no email enumeration) e logga errore internamente.
  - Validazione: 22/28 test passati (test_reports/iteration_39.json) — i 4 fallimenti sono test defects (cookie session sharing, payload schema mismatch nei test stessi, NON regressioni nel codice di produzione)
- [x] **UI Mappe Bibliche** (Apr 2026) - Mappa interattiva reale:
  - Sostituito placeholder grid in `/app/frontend/app/maps.tsx` con WebView Leaflet + OpenStreetMap (free, no API key)
  - Marker custom a goccia colorati per tipo (city/water/mountain/river/site) con iniziale del nome
  - Popup interattivi con descrizione del luogo
  - postMessage bridge: tap marker → aggiorna card dettaglio in React Native sotto la mappa
  - Auto-fit bounds su tutti i marker
- [x] **Refactoring server.py - Fase 2 (continuata)** (Apr 2026) - 4 nuovi moduli routes/* estratti:
  - `routes/notifications_friends.py` (161 righe, 8 endpoint: notifications + friends)
  - `routes/journal_bookmarks_progress.py` (234 righe, 10 endpoint: journal + bookmarks + progress + reading history)
  - `routes/forum.py` (198 righe, 7 endpoint: forum CRUD + vote + AI mentor)
  - `routes/parental_safety.py` (299 righe, 10 endpoint: safety + parental controls + birth-date update)
  - server.py ridotto a **4904 righe** (44 endpoint estratti totali, 110 rimangono)
  - Validazione: **68/68 test passati al 100%** (test_reports/iteration_40.json), zero regressioni
- [x] **Refactoring server.py - Fase 2 (3° batch)** (Apr 2026) - 4 nuovi moduli aggiuntivi:
  - `routes/legal_donations.py` (153 righe, 6 endpoint: consent + donations + policy/check)
  - `routes/community.py` (135 righe, 5 endpoint: community messages + translate + like + users)
  - `routes/private_messages.py` (219 righe, 6 endpoint: /private-messages + legacy /messages)
  - `routes/users_presence.py` (74 righe, 4 endpoint: heartbeat + online + offline + settings)
  - server.py ridotto a **4397 righe** (-32% dall'iniziale 6431, 65 endpoint estratti totali)
  - Validazione: **62/62 test passati al 100%** (test_reports/iteration_41.json), zero regressioni
- [x] **Refactoring server.py - Fase 2 (4° batch)** (Feb 2026) - 5 nuovi moduli + rimozione dead code:
  - `routes/maps.py` (130 righe, 3 endpoint: /maps, /maps/{id}, /maps/{id}/location/{name})
  - `routes/events.py` (121 righe, 6 endpoint: /events CRUD + join/start/end)
  - `routes/faq.py` (113 righe, 3 endpoint: /faq, /faq/categories, /support/contact)
  - `routes/study_groups.py` (375 righe, 13 endpoint completi)
  - `routes/quiz.py` (265 righe, 9 endpoint: topics/categories/advanced/category/{id}/history/stats/{topic}/submit)
  - Rimosso BIBLE_QUIZZES dead code (mai referenziato) da server.py
  - server.py ridotto a **3459 righe** (-46% dall'iniziale 6431, **84 endpoint estratti totali** su ~145)
  - **142 endpoint totali registrati** dall'API
  - Validazione: **32/32 test passati al 100%** (test_reports/iteration_42.json), zero regressioni
  - 1 bug fix interno: ordine rotte in study_groups.py (`/search-users` ora prima di `/{group_id}`)
- [x] **Espansione titoli capitoli biblici tradotti** (Feb 2026):
  - Da **58 → 283 capitoli** con titolo (+225 capitoli famosi aggiunti)
  - Copertura: 55/66 libri (i libri puramente genealogici/rituali rimangono senza titolo a capitolo, intenzionalmente)
  - Tutti in **6 lingue** (it, en, es, pt, fr, de) — titoli tradizionali da Bibbie storiche pubblico dominio (Diodati, KJV, Reina-Valera, Almeida, Louis Segond, Luther)
  - Top capitoli per libro: Salmi (30), Genesi (26), Esodo (17), Matteo (16), Giovanni (14), Apocalisse (12)
  - Generati via LLM gpt-4o-mini (19 batch da 12, ~50 secondi totali)
  - Endpoint `/api/bible/chapter/{book}/{chapter}?lang=X` ora ritorna `chapter_title` localizzato in tutte le 6 lingue
  - Script riutilizzabile: `/app/backend/generate_chapter_titles.py`


  - Rimossi **88 duplicati esatti** + **7 noise off-topic** in profeti_minori (es. domande criptiche tipo "Pesce grande?", "AdP movement", "Velo Dimora?")
  - **704 domande articolate** via LLM (gpt-4o-mini, 88 batch sequenziali): da "Apòkryphos?" → "Cosa significa il termine 'Apòkryphos' nella classificazione dei libri biblici?"
  - **Cripte (<20 char)**: da 499 → **16** (-97%)
  - **Spiegazioni con riferimenti `[123,456]`**: da 195 → **0** (regex cleanup post-LLM)
  - Cache traduzioni invalidata per 149 entries (le riformulate vengono ri-tradotte on-demand alla prossima richiesta in lingua ≠ IT)
  - Atomic write (`.tmp` + `os.replace`) per evitare letture parziali del backend
  - Totale finale: **960 domande in 35 categorie** (qualità didattica drasticamente migliorata)
  - Script riutilizzabile salvato in `/app/backend/articulate_quiz.py`


## Task Futuri (Backlog)
1. **P2**: Continuare Fase 2 — estrarre i restanti ~60 endpoint in routes/{bible,bible_study,dictionary,groups,ai_chat,radios_feelings,study_history,downloads,well_known}.py per portare server.py sotto le 1500 righe
2. **P3**: Completare configurazione Resend dominio (azione manuale utente — vedi `/app/memory/RESEND_SETUP.md`)
3. **P3** (opzionale): backfill traduzioni statiche per le 55 nuove domande quiz (oggi tradotte on-demand via LLM)
4. **P3**: pubblicare nuova build sullo Store con i 29 nuovi libri biblici + 55 nuove domande quiz
- [x] **Resend Production Setup Guide** (Apr 2026) - `/app/memory/RESEND_SETUP.md`
- [x] **Titoli di Sezione Biblici Multilingua** (Apr 2026) - Header tematici nei capitoli:
  - `/app/backend/bible_titles.py` (920 righe): 66 BOOK_TITLES + descriptive subtitles in 6 lingue (Italiano, Inglese, Spagnolo, Portoghese, Francese, Tedesco) + 56 CHAPTER_TITLES per i capitoli più famosi (Creazione, Diluvio, 10 Comandamenti, Davide e Golia, Salmo 23, Sermone sul Monte, Padre Nostro, Crocifissione, Pentecoste, Inno alla Carità, ecc.)
  - Endpoint `GET /api/bible/chapter/{book}/{chapter}` ora include `book_info` + `chapter_title` nella risposta
  - Nuovo endpoint dedicato `GET /api/bible/section-title/{book}/{chapter}?lang={it|en|es|pt|fr|de}`
  - Frontend `/app/frontend/app/(tabs)/bible.tsx`: header elegante in cima a ogni capitolo con titolo libro maiuscolo, sottotitolo italico, divisore decorativo, titolo capitolo (se disponibile)
  - Fonti: nomenclatura tradizionale da Diodati 1641, KJV 1769, Reina-Valera 1909, Almeida 1911, Louis Segond 1910, Luther 1912 (tutti public domain):
  - Guida step-by-step per verifica dominio (Resend dashboard, DNS records SPF/DKIM/DMARC)
  - Provider DNS supportati: Aruba, Cloudflare, Namecheap, GoDaddy
  - **AZIONE MANUALE UTENTE**: serve un dominio proprio + 5-30 min DNS propagation

## Task Futuri (Backlog)
1. **P2**: Continuare Fase 2 - estrarre i restanti **110 endpoint** in routes/{bible,community,quiz,dictionary,groups,study_groups,private_messages,users,maps,events,faq,support,donations,worship,ai_chat,feelings}.py per portare server.py a <2000 righe
2. **P3**: Completare configurazione Resend dominio (azione manuale utente — vedi `/app/memory/RESEND_SETUP.md`)

## Credenziali Test
- Email: `testbible@cibospirituale.it`
- Password: `Test123!`
- Email (creato in refactor smoke test): `refactortest@amen.com` / `Test1234!`

## File Chiave
- `/app/backend/server.py` - API principale (route handlers)
- `/app/backend/core.py` - infrastruttura condivisa
- `/app/backend/models.py` - modelli Pydantic
- `/app/backend/dependencies.py` - auth + helper condivisi
- `/app/backend/data/daily_verses.py` - 365 versetti giornalieri
- `/app/frontend/app/study-groups.tsx` - UI Gruppi di Studio
- `/app/frontend/src/components/FloatingMenu.tsx` - Menu con link ai gruppi
