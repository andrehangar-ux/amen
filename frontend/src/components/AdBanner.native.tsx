import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { BannerAd, BannerAdSize } from 'react-native-google-mobile-ads';
import { canShowAds, isInitialized } from '../utils/ads';

interface AdBannerProps {
  style?: any;
  unitIndex?: 1 | 2 | 3;
}

// Production banner unit IDs (set in app.json -> AdMob plugin).
const BANNER_UNIT_ID_ANDROID = 'ca-app-pub-1876565863299921/6716733612';
const BANNER_UNIT_ID_IOS = 'ca-app-pub-1876565863299921/6716733612';
// Google reserved test ID — always returns a sample banner in dev builds.
const TEST_BANNER_UNIT_ID = 'ca-app-pub-3940256099942544/6300978111';

/**
 * Native-only AdBanner (iOS & Android).
 *
 * Waits for the UMP consent flow in `src/utils/ads.ts` to complete and for
 * `canRequestAds` to be true before mounting the real `<BannerAd />`.
 * The web build resolves to `AdBanner.tsx` (a no-op stub) thanks to
 * Metro's Platform-specific file extension resolution.
 */
export const AdBanner: React.FC<AdBannerProps> = ({ style }) => {
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
    ? BANNER_UNIT_ID_ANDROID
    : BANNER_UNIT_ID_IOS;

  return (
    <View style={[styles.container, style]} testID="ad-banner">
      <BannerAd
        unitId={unitId}
        size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
        requestOptions={{ requestNonPersonalizedAdsOnly: false }}
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
