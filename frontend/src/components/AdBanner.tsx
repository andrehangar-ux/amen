import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';

// Production Ad Unit IDs from AdMob Console
const AD_UNITS = {
  banner1: 'ca-app-pub-1876565863299921/5471187240',
  banner2: 'ca-app-pub-1876565863299921/7118323752',
  banner3: 'ca-app-pub-1876565863299921/5567117090',
};

const AD_UNIT_TEST = 'ca-app-pub-3940256099942544/6300978111';

interface AdBannerProps {
  style?: any;
  unitIndex?: 1 | 2 | 3;
}

// On web, export a no-op component (native ads don't work on web)
export const AdBanner: React.FC<AdBannerProps> = ({ style, unitIndex = 1 }) => {
  if (Platform.OS === 'web') return null;
  
  // This component renders nothing on web preview.
  // On native (Android APK build), the actual BannerAd is rendered
  // via the AdBannerNative component below.
  return <AdBannerNative style={style} unitIndex={unitIndex} />;
};

// Native-only implementation
const AdBannerNative: React.FC<AdBannerProps> = ({ style, unitIndex = 1 }) => {
  const unitId = __DEV__
    ? AD_UNIT_TEST
    : unitIndex === 1 ? AD_UNITS.banner1
    : unitIndex === 2 ? AD_UNITS.banner2
    : AD_UNITS.banner3;

  // Use eval to prevent Metro static analysis from bundling for web
  const moduleName = 'react-native-google-mobile-ads';
  let BannerAd: any = null;
  let BannerAdSize: any = null;
  
  try {
    // eslint-disable-next-line no-eval
    const ads = eval(`require('${moduleName}')`);
    BannerAd = ads.BannerAd;
    BannerAdSize = ads.BannerAdSize;
  } catch {
    return null;
  }

  if (!BannerAd || !BannerAdSize) return null;

  return (
    <View style={[styles.container, style]}>
      <BannerAd
        unitId={unitId}
        size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
        requestOptions={{
          requestNonPersonalizedAdsOnly: true,
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    width: '100%',
  },
});
