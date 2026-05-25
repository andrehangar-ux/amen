/**
 * Expo config plugin: disable Android Auto Backup so the UMP/AdMob consent
 * state cannot be restored across reinstalls.
 *
 * Sets on the <application> tag:
 *   android:allowBackup="false"
 *   android:fullBackupContent="false"
 *   tools:replace="android:allowBackup,android:fullBackupContent"
 *
 * Required because Android's Auto Backup was caching the previous (empty/
 * rejected) UMP consent state, preventing the GDPR form from re-appearing
 * after a clean install during QA.
 *
 * Toggle by setting EXPO_PUBLIC_ALLOW_BACKUP=1 in the env at build time.
 * Default behaviour = disable backup (matches the QA request).
 */
const { withAndroidManifest } = require('@expo/config-plugins');

module.exports = function withDisableAndroidBackup(config) {
  return withAndroidManifest(config, (cfg) => {
    const manifest = cfg.modResults.manifest;
    if (!manifest) return cfg;

    // 1. Ensure xmlns:tools is declared at the manifest root (needed for tools:replace).
    if (!manifest.$['xmlns:tools']) {
      manifest.$['xmlns:tools'] = 'http://schemas.android.com/tools';
    }

    // 2. Patch every <application> tag (usually only one).
    const applications = manifest.application || [];
    const disable = process.env.EXPO_PUBLIC_ALLOW_BACKUP !== '1';

    applications.forEach((app) => {
      app.$ = app.$ || {};
      app.$['android:allowBackup'] = disable ? 'false' : 'true';
      app.$['android:fullBackupContent'] = disable ? 'false' : 'true';
      // tools:replace lets us override any auto-generated value safely.
      const existing = app.$['tools:replace'] || '';
      const additions = ['android:allowBackup', 'android:fullBackupContent'];
      const merged = existing
        ? Array.from(new Set(existing.split(',').map((s) => s.trim()).concat(additions))).join(',')
        : additions.join(',');
      app.$['tools:replace'] = merged;
    });

    return cfg;
  });
};
