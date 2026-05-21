/**
 * Web stub. The real Google AdMob + UMP integration lives in `ads.native.ts`
 * and is selected automatically by Metro on Android/iOS bundles.
 *
 * On web every function is a no-op so the app can still be developed and
 * previewed without pulling in the native `react-native-google-mobile-ads`
 * module (which imports react-native internals not available on web).
 */
export function canShowAds(): boolean {
  return false;
}

export function isInitialized(): boolean {
  // Return true so any consumer that polls for the UMP flow does not block
  // forever on web — the AdBanner.tsx stub already returns null regardless.
  return true;
}

export async function initializeAdsWithConsent(): Promise<void> {
  // no-op on web
}

export async function showPrivacyOptionsForm(): Promise<void> {
  // no-op on web
}
