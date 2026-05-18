import React, { useEffect, useState } from 'react';
import { Platform, View, StyleSheet } from 'react-native';
import { canShowAds, isInitialized } from '../utils/ads';

interface AdBannerProps {
  style?: any;
  unitIndex?: 1 | 2 | 3;
}

// Production banner unit IDs (set in app.json -> AdMob plugin).
// One configured unit + Google test ID for development.
const BANNER_UNIT_ID_ANDROID = 'ca-app-pub-1876565863299921/6716733612';
const BANNER_UNIT_ID_IOS = 'ca-app-pub-1876565863299921/6716733612';
const TEST_BANNER_UNIT_ID = 'ca-app-pub-3940256099942544/6300978111';

/**
 * AdBanner is a no-op on web preview and on native until the UMP consent
 * flow (see `src/utils/ads.ts`) completes AND ad requests are allowed.
 *
 * On Android/iOS APK builds, once `canShowAds()` returns true the native
 * BannerAd component from `react-native-google-mobile-ads` is rendered.
 */
export const AdBanner: React.FC<AdBannerProps> = ({ style }) => {
  const [ready, setReady] = useState<boolean>(isInitialized() && canShowAds());

  useEffect(() => {
    if (Platform.OS === 'web' || ready) return;
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

  if (Platform.OS === 'web' || !ready) {
    return null;
  }

  // Lazy require keeps the native module out of the web bundle.
  let BannerAd: any;
  let BannerAdSize: any;
  try {
    const Ads = require('react-native-google-mobile-ads');
    BannerAd = Ads.BannerAd;
    BannerAdSize = Ads.BannerAdSize;
  } catch {
    return null;
  }

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
