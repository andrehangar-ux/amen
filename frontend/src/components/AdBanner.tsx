import React from 'react';
import { Platform } from 'react-native';

interface AdBannerProps {
  style?: any;
  unitIndex?: 1 | 2 | 3;
}

// AdBanner is a no-op on web preview.
// On native Android builds, ads are rendered via the native AdMob SDK
// which is configured in app.json plugin and google-services.json.
// The actual ad rendering happens only in the native APK build.
export const AdBanner: React.FC<AdBannerProps> = () => {
  // Native ads cannot render in web preview
  return null;
};
