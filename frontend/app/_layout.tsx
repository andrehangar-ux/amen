import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../src/store/authStore';
import { View, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { COLORS } from '../src/utils/theme';
import { FloatingMenu } from '../src/components/FloatingMenu';
import * as SplashScreen from 'expo-splash-screen';

// Initialize Google Mobile Ads SDK (native only)
if (Platform.OS !== 'web') {
  try {
    const { default: mobileAds } = require('react-native-google-mobile-ads');
    mobileAds().initialize().catch(() => {});
  } catch {}
}

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const { checkAuth, isLoading: authLoading } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!authLoading) {
      SplashScreen.hideAsync();
    }
  }, [authLoading]);

  if (authLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: COLORS.background },
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen 
          name="assistant" 
          options={{ 
            presentation: 'modal',
            animation: 'slide_from_bottom' 
          }} 
        />
        <Stack.Screen name="mood-checkin" options={{ presentation: 'modal' }} />
        <Stack.Screen name="my-content" options={{ presentation: 'card' }} />
        <Stack.Screen name="friends" options={{ presentation: 'card' }} />
        <Stack.Screen name="reading-progress" options={{ presentation: 'card' }} />
        <Stack.Screen name="community" options={{ presentation: 'card' }} />
        <Stack.Screen name="donate" options={{ presentation: 'card' }} />
      </Stack>
      <View style={styles.fabLayer} pointerEvents="box-none">
        <FloatingMenu />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  fabLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9999,
  },
});
