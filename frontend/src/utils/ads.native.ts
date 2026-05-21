/**
 * Google AdMob initialization with UMP consent — native (Android/iOS) only.
 *
 * Implements the official Google UMP flow:
 *   https://developers.google.com/admob/android/privacy/gdpr
 *
 * Flow on app launch:
 *   1. AdsConsent.gatherConsent() runs requestInfoUpdate + loadAndShowConsentFormIfRequired.
 *   2. Only when AdsConsent.getConsentInfo().canRequestAds is true do we call
 *      mobileAds().initialize().
 *   3. <AdBanner.native> reads canShowAds() to decide whether to render.
 *
 * The web bundle gets `ads.ts` (stub) instead — Metro resolves Platform-specific
 * file extensions automatically.
 */
import mobileAds, {
  AdsConsent,
  AdsConsentDebugGeography,
} from 'react-native-google-mobile-ads';

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
    // 1. Run the UMP consent flow.
    //    `gatherConsent` = requestInfoUpdate + loadAndShowConsentFormIfRequired.
    //    DEV: force EEA geography to make the form visible during testing.
    await AdsConsent.gatherConsent({
      debugGeography: __DEV__
        ? AdsConsentDebugGeography.EEA
        : AdsConsentDebugGeography.DISABLED,
      testDeviceIdentifiers: [],
    });

    // 2. Verify Google authorises ad requests (granted consent OR not required).
    const info = await AdsConsent.getConsentInfo();
    _canShowAds = Boolean(info?.canRequestAds);

    // 3. Only initialize the SDK when allowed to request ads.
    if (_canShowAds) {
      await mobileAds().initialize();
    }
  } catch (err) {
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.warn('[ads] initializeAdsWithConsent failed:', err);
    }
    _canShowAds = false;
  } finally {
    _initDone = true;
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
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.warn('[ads] showPrivacyOptionsForm failed:', err);
    }
  }
}
