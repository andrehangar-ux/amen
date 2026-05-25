import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { BannerAd, BannerAdSize } from 'react-native-google-mobile-ads';
import { canShowAds, isInitialized } from '../utils/ads';

interface AdBannerProps {
  style?: any;
  /** Selects which configured Banner Unit ID to use (1, 2 or 3). Defaults to 1. */
  unitIndex?: 1 | 2 | 3;
}

// =============================================================================
// AdMob unit IDs — DO NOT mix App ID (~) with Unit IDs (/) again.
//
// App ID lives in app.json under plugins -> react-native-google-mobile-ads.
// Unit IDs (one per slot) live here.
//
// Source: AdMob Console → App "Amen!" → Unità annuncio (Feb 2026)
// =============================================================================
const BANNER_UNIT_IDS_ANDROID: Record<1 | 2 | 3, string> = {
  1: 'ca-app-pub-1876565863299921/5471187240',
  2: 'ca-app-pub-1876565863299921/7118323752',
  3: 'ca-app-pub-1876565863299921/5567117090',
};
const BANNER_UNIT_IDS_IOS: Record<1 | 2 | 3, string> = {
  // The user has no separate iOS unit IDs yet — reuse Android.
  1: 'ca-app-pub-1876565863299921/5471187240',
  2: 'ca-app-pub-1876565863299921/7118323752',
  3: 'ca-app-pub-1876565863299921/5567117090',
};
// Google's reserved test banner. Always returns a sample banner in dev builds.
const TEST_BANNER_UNIT_ID = 'ca-app-pub-3940256099942544/6300978111';

/**
 * Native-only AdBanner (iOS & Android).
 *
 * Waits for the UMP consent flow in `src/utils/ads.ts` to complete and for
 * `canRequestAds` to be true before mounting the real `<BannerAd />`.
 * The web build resolves to `AdBanner.tsx` (a no-op stub) thanks to
 * Metro's Platform-specific file extension resolution.
 */
export const AdBanner: React.FC<AdBannerProps> = ({ style, unitIndex = 1 }) => {
  const [ready, setReady] = useState<boolean>(isInitialized() && canShowAds());

  useEffect(() => {
    if (ready) return;
    // Poll briefly until UMP flow finishes (typical: <2s on cold start).
    const interval = setInterval(() => {
      if (isInitialized()) {
        setReady(canShowAds());
        clearInterval(interval);
      }
    }, 500);
    // Safety: stop polling after 15s regardless.
    const timeout = setTimeout(() => clearInterval(interval), 15000);
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [ready]);

  if (!ready) return null;

  const unitId = __DEV__
    ? TEST_BANNER_UNIT_ID
    : Platform.OS === 'android'
    ? BANNER_UNIT_IDS_ANDROID[unitIndex]
    : BANNER_UNIT_IDS_IOS[unitIndex];

  return (
    <View style={[styles.container, style]} testID="ad-banner">
      <BannerAd
        unitId={unitId}
        size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
        requestOptions={{ requestNonPersonalizedAdsOnly: false }}
        onAdLoaded={() => {
          // eslint-disable-next-line no-console
          console.log('[ads] BannerAd LOADED — unitId:', unitId);
        }}
        onAdFailedToLoad={(error: any) => {
          // Surface the precise Google error code/message in Logcat.
          // Common codes:
          //   ERROR_CODE_NO_FILL          → no inventory matched (account too new / region)
          //   ERROR_CODE_INVALID_REQUEST  → wrong unit id, App ID mismatch, package not registered
          //   ERROR_CODE_NETWORK_ERROR    → device offline / DNS issue
          //   ERROR_CODE_INTERNAL_ERROR   → SDK glitch (retry helps)
          // eslint-disable-next-line no-console
          console.warn(
            '[ads] BannerAd FAILED — unitId:',
            unitId,
            'code:',
            error?.code,
            'message:',
            error?.message,
            'domain:',
            error?.domain,
          );
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
});
