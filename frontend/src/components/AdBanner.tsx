import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';

// AdMob banner component - renders ads on native, nothing on web
// IMPORTANT: Replace production IDs with actual Banner Ad Unit IDs from AdMob Console
// Current production IDs are TEST IDs - create Ad Units at apps.admob.com

const AD_UNIT_BANNER = Platform.select({
  android: 'ca-app-pub-3940256099942544/6300978111', // Google test banner - replace with real Ad Unit ID
  ios: 'ca-app-pub-3940256099942544/2934735716', // Google test banner
  default: '',
});

interface AdBannerProps {
  style?: any;
}

export const AdBanner: React.FC<AdBannerProps> = ({ style }) => {
  // On web, don't render ads
  if (Platform.OS === 'web') return null;

  // Dynamic import to avoid web bundling issues
  try {
    const { BannerAd, BannerAdSize } = require('react-native-google-mobile-ads');
    
    return (
      <View style={[styles.container, style]}>
        <BannerAd
          unitId={AD_UNIT_BANNER}
          size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER}
          requestOptions={{
            requestNonPersonalizedAdsOnly: true,
          }}
        />
      </View>
    );
  } catch {
    // If the native module isn't available (web), render nothing
    return null;
  }
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    width: '100%',
  },
});
