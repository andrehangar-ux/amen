/**
 * Google AdMob initialization with UMP (User Messaging Platform) consent.
 *
 * Implements the official Google UMP flow:
 *   https://developers.google.com/admob/android/privacy/gdpr
 *
 * Flow on app launch:
 *   1. AdsConsent.gatherConsent() runs requestInfoUpdate + loadAndShowConsentFormIfRequired.
 *      - If the user is in EEA/UK/regulated-US state, the Google consent form is shown.
 *      - Outside those regions, the SDK auto-resolves without showing UI.
 *   2. Only when AdsConsent.getConsentInfo().canRequestAds is true do we call
 *      mobileAds().initialize() — Google requires this gating.
 *   3. The exported `canShowAds()` getter is used by <AdBanner /> to decide
 *      whether to render the native banner.
 *
 * Web preview / iOS Expo Go fall back gracefully: the module is loaded
 * conditionally because it is a native module.
 */
import { Platform } from 'react-native';

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
  // Only run on native platforms — the SDK has no web implementation.
  if (Platform.OS === 'web' || _initStarted) {
    return;
  }
  _initStarted = true;

  try {
    // Lazy require so the web bundler does not try to resolve the native module.
    const Ads = require('react-native-google-mobile-ads');
    const mobileAds = Ads.default;
    const { AdsConsent, AdsConsentDebugGeography } = Ads;

    // 1. Run the UMP consent flow.
    //    `gatherConsent` = requestInfoUpdate + loadAndShowConsentFormIfRequired.
    //    In DEV we force EEA geography to make the form visible during testing.
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
    // Never let an ads/consent failure crash the app launch.
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
 * later (required by Google for EEA users). Bind this to a "Privacy options"
 * button in your Settings screen.
 */
export async function showPrivacyOptionsForm(): Promise<void> {
  if (Platform.OS === 'web') return;
  try {
    const Ads = require('react-native-google-mobile-ads');
    await Ads.AdsConsent.showPrivacyOptionsForm();
  } catch (err) {
    if (__DEV__) {
      // eslint-disable-next-line no-console
      console.warn('[ads] showPrivacyOptionsForm failed:', err);
    }
  }
}
