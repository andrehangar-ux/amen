# 📱 Guida per Creare APK di Amen!

## Metodo 1: EAS Build (Raccomandato)

### Prerequisiti
1. Installa EAS CLI globalmente:
```bash
npm install -g eas-cli
```

2. Accedi al tuo account Expo:
```bash
eas login
```

### Creare APK per Testing

1. Naviga nella cartella frontend:
```bash
cd /path/to/amen-app/frontend
```

2. Crea il file `eas.json` (se non esiste):
```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  }
}
```

3. Esegui il build APK:
```bash
# Per APK di test (più veloce)
eas build -p android --profile preview

# Per APK completo
eas build -p android --profile production
```

4. Scarica l'APK dal link fornito al termine del build.

---

## Metodo 2: Expo Build (Legacy)

```bash
# Nella cartella frontend
expo build:android -t apk
```

**Nota**: Questo metodo è deprecato, usa EAS Build.

---

## Metodo 3: Build Locale con Expo Dev Client

### Prerequisiti
- Android Studio installato
- JDK 11 o superiore
- Android SDK configurato

### Passaggi

1. Installa expo-dev-client:
```bash
npx expo install expo-dev-client
```

2. Genera progetto nativo:
```bash
npx expo prebuild
```

3. Apri in Android Studio:
```bash
cd android
./gradlew assembleRelease
```

4. L'APK sarà in: `android/app/build/outputs/apk/release/app-release.apk`

---

## 🔧 Configurazione app.json (già fatto)

Il file `app.json` è già configurato con:
- Nome: "Amen!"
- Package: com.amen.spiritualapp
- Icona: Colomba bianca su sfondo verde
- Permessi: Microfono, Camera

---

## 📋 Checklist Pre-Build

- [x] Nome app: Amen!
- [x] Package Android: com.amen.spiritualapp
- [x] Icona app: Colomba bianca
- [x] Splash screen configurato
- [x] Permessi dichiarati

---

## 🚀 Per testare immediatamente

Usa **Expo Go** sul tuo telefono:

1. Scarica "Expo Go" dal Play Store
2. Scansiona il QR code mostrato nel terminale
3. L'app si aprirà in Expo Go

**Limitazioni di Expo Go**:
- Non puoi installare come app standalone
- Alcune funzionalità native potrebbero non funzionare
- Per test completi, usa EAS Build

---

## 📞 Supporto

Per domande sulla build: andrehangar@live.it
