/**
 * Google AdMob initialization with UMP consent — native (Android/iOS) only.
 *
 * Implements the official Google UMP flow:
 *   https://developers.google.com/admob/android/privacy/gdpr
 *
 * Flow on app launch:
 *   1. (TEST BUILDS ONLY) AdsConsent.reset() → discards any persisted/restored
 *      consent state so the GDPR form always reappears. Driven by EXPO_PUBLIC_RESET_UMP=1
 *      to keep production users from re-prompting on every launch.
 *   2. AdsConsent.gatherConsent() runs requestInfoUpdate + loadAndShowConsentFormIfRequired.
 *   3. Only when AdsConsent.getConsentInfo().canRequestAds is true do we call
 *      mobileAds().initialize().
 *   4. <AdBanner.native> reads canShowAds() to decide whether to render.
 *
 * Verbose logs are emitted under the `[ads]` tag so the user can filter
 * Logcat with `adb logcat | grep -E "\[ads\]|Ads"` during validation.
 *
 * The web bundle gets `ads.ts` (stub) instead — Metro resolves Platform-specific
 * file extensions automatically.
 */
import mobileAds, {
  AdsConsent,
  AdsConsentDebugGeography,
  AdsConsentStatus,
} from 'react-native-google-mobile-ads';

// eslint-disable-next-line no-console
const log = (...args: any[]) => console.log('[ads]', ...args);

// Test-only switches.
// - __DEV__ already implies a dev client / Metro bundle.
// - EXPO_PUBLIC_RESET_UMP=1 lets us force the UMP reset in release/preview APKs too
//   (so the GDPR form re-appears at every launch). REMOVE / SET TO 0 before Play Store.
const SHOULD_RESET_UMP =
  __DEV__ || process.env.EXPO_PUBLIC_RESET_UMP === '1';

let _canShowAds = false;
let _initStarted = false;
let _initDone = false;

export function canShowAds(): boolean {
  return _canShowAds;
}

export function isInitialized(): boolean {
  return _initDone;
}

export async function initializeAdsWithConsent(): Promise<void> {
  if (_initStarted) return;
  _initStarted = true;

  try {
    // 1. TEST-PHASE RESET: discard any persisted UMP state (incl. anything
    //    Android's Auto Backup restored from the previous install). This makes
    //    the consent form reappear at every launch, which is exactly what we
    //    need to validate the AdMob + UMP integration end-to-end.
    if (SHOULD_RESET_UMP) {
      try {
        AdsConsent.reset();
        log('UMP state reset (test build)');
      } catch (e) {
        log('UMP reset error (non-fatal):', e);
      }
    }

    // 2. Run the UMP consent flow.
    //    `gatherConsent` = requestInfoUpdate + loadAndShowConsentFormIfRequired.
    //    DEV: force EEA geography to make the form visible regardless of device location.
    log('gatherConsent start');
    await AdsConsent.gatherConsent({
      debugGeography: __DEV__
        ? AdsConsentDebugGeography.EEA
        : AdsConsentDebugGeography.DISABLED,
      testDeviceIdentifiers: [],
    });

    // 3. Verify Google authorises ad requests (granted consent OR not required).
    const info = await AdsConsent.getConsentInfo();
    _canShowAds = Boolean(info?.canRequestAds);
    log('consent info', {
      status: info?.status,
      isConsentFormAvailable: info?.isConsentFormAvailable,
      canRequestAds: info?.canRequestAds,
      privacyOptionsRequirementStatus: info?.privacyOptionsRequirementStatus,
    });

    if (info?.status === AdsConsentStatus.OBTAINED) {
      log('consent OBTAINED — initializing Mobile Ads SDK');
    } else if (info?.status === AdsConsentStatus.NOT_REQUIRED) {
      log('consent NOT_REQUIRED (outside regulated regions) — initializing Mobile Ads SDK');
    } else if (info?.status === AdsConsentStatus.REQUIRED) {
      log('consent REQUIRED but not obtained → ads will NOT load');
    }

    // 4. Only initialize the SDK when allowed to request ads.
    if (_canShowAds) {
      const initRes = await mobileAds().initialize();
      log('mobileAds().initialize() complete', Object.keys(initRes || {}));
    } else {
      log('canRequestAds=false → SKIP mobileAds().initialize()');
    }
  } catch (err) {
    log('initializeAdsWithConsent failed:', err);
    _canShowAds = false;
  } finally {
    _initDone = true;
    log('init done — canShowAds:', _canShowAds);
  }
}

/**
 * Opens the privacy options form so the user can change their consent choice
 * later (required by Google for EEA users).
 */
export async function showPrivacyOptionsForm(): Promise<void> {
  try {
    await AdsConsent.showPrivacyOptionsForm();
  } catch (err) {
    log('showPrivacyOptionsForm failed:', err);
  }
}
