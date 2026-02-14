# 📱 AMEN! - Guida Completa per Creare APK e Distribuire ai Tester

## 🚀 PASSO 1: Salva il Progetto su GitHub

1. Clicca **"Save to GitHub"** nell'interfaccia di Emergent (in alto)
2. Seleziona il branch (main)
3. Clicca **"PUSH TO GITHUB"**
4. Il progetto sarà disponibile nel tuo repository GitHub

---

## 📦 PASSO 2: Crea l'APK per Android

### Sul tuo computer:

```bash
# 1. Clona il repository
git clone https://github.com/TUO-USERNAME/TUO-REPO.git
cd TUO-REPO/frontend

# 2. Installa le dipendenze
npm install

# 3. Installa EAS CLI globalmente
npm install -g eas-cli

# 4. Login con account Expo (gratuito su expo.dev)
eas login

# 5. Configura il progetto (prima volta)
eas build:configure

# 6. CREA L'APK! 🎉
eas build -p android --profile preview
```

### Risultato:
- Riceverai un **link per scaricare l'APK**
- Condividi questo link con i tuoi tester
- I tester scaricano e installano direttamente!

---

## 🍎 PASSO 3: Per Tester iOS

### Opzione A: TestFlight (Raccomandato)
Richiede Apple Developer Account ($99/anno)

```bash
# Crea build iOS per TestFlight
eas build -p ios --profile preview
eas submit -p ios
```
- I tester ricevono invito via email
- Installano tramite app TestFlight

### Opzione B: Expo Go (Gratuito, Immediato)
1. I tester scaricano **"Expo Go"** dall'App Store
2. Condividi il link dell'app: `https://quiz-stats-amen.preview.emergentagent.com`
3. Aprono il link in Expo Go

---

## 🔗 PASSO 4: Condividi con i Tester

### Per Android:
Dopo il build, ricevi un link tipo:
```
https://expo.dev/artifacts/eas/XXXXX.apk
```
Condividi questo link! I tester:
1. Cliccano il link
2. Scaricano l'APK
3. Abilitano "Installa da fonti sconosciute"
4. Installano l'app

### Per iOS (senza TestFlight):
I tester usano **Expo Go**:
1. Scaricano Expo Go dall'App Store
2. Scansionano il QR code o aprono il link

---

## ⚙️ Configurazione Già Pronta

Il progetto è già configurato con:
- ✅ Nome: **Amen!**
- ✅ Package Android: `com.amen.spiritualapp`
- ✅ Bundle iOS: `com.amen.spiritualapp`
- ✅ Icona: Colomba bianca
- ✅ Splash screen verde
- ✅ Permessi dichiarati

---

## 📋 Checklist Pre-Distribuzione

- [ ] Salva progetto su GitHub
- [ ] Crea account Expo gratuito su expo.dev
- [ ] Installa Node.js sul tuo PC
- [ ] Esegui il build APK
- [ ] Testa l'APK sul tuo telefono
- [ ] Condividi il link con i tester

---

## 🆘 Problemi Comuni

### "EAS command not found"
```bash
npm install -g eas-cli
```

### "Not logged in"
```bash
eas login
```

### Build fallito
```bash
# Pulisci e riprova
rm -rf node_modules
npm install
eas build -p android --profile preview --clear-cache
```

---

## 📞 Supporto

Email: andrehangar@live.it

---

## 🎯 Riepilogo Veloce

```bash
# Android APK in 5 minuti:
git clone [tuo-repo]
cd frontend
npm install
npm install -g eas-cli
eas login
eas build -p android --profile preview
# → Ricevi link APK da condividere!
```
