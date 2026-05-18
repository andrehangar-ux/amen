import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../src/store/authStore';
import { View, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { COLORS } from '../src/utils/theme';
import { FloatingMenu } from '../src/components/FloatingMenu';
import * as SplashScreen from 'expo-splash-screen';
import { initializeAdsWithConsent } from '../src/utils/ads';

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const { checkAuth, isLoading: authLoading } = useAuthStore();

  useEffect(() => {
    checkAuth();
    // Google UMP consent flow MUST run before any ad request.
    // This is enforced by Google Play policy for apps shown in EEA/UK.
    // The call is safe to fire-and-forget: it gates ads internally and
    // never throws to the React tree.
    initializeAdsWithConsent();
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
