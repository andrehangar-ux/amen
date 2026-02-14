import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../src/store/authStore';
import { useConsentStore } from '../src/store/consentStore';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { COLORS } from '../src/utils/theme';
import * as SplashScreen from 'expo-splash-screen';
import { TermsModal } from '../src/components/TermsModal';

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const { checkAuth, isLoading: authLoading, isAuthenticated } = useAuthStore();
  const { hasAccepted, isChecking, checkConsent, reset } = useConsentStore();
  const [showTermsModal, setShowTermsModal] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  // Reset consent state when user logs out
  useEffect(() => {
    if (!isAuthenticated) {
      reset();
      setShowTermsModal(false);
    }
  }, [isAuthenticated]);

  // Check terms acceptance status when user is authenticated
  useEffect(() => {
    const checkTermsStatus = async () => {
      if (isAuthenticated && !authLoading && hasAccepted === null) {
        const accepted = await checkConsent();
        if (!accepted) {
          setShowTermsModal(true);
        }
      }
    };

    checkTermsStatus();
  }, [isAuthenticated, authLoading, hasAccepted]);

  // Show modal when consent is false
  useEffect(() => {
    if (isAuthenticated && hasAccepted === false) {
      setShowTermsModal(true);
    } else if (hasAccepted === true) {
      setShowTermsModal(false);
    }
  }, [isAuthenticated, hasAccepted]);

  useEffect(() => {
    if (!authLoading && !isChecking) {
      SplashScreen.hideAsync();
    }
  }, [authLoading, isChecking]);

  const handleTermsAccept = async () => {
    // The modal calls the API, so just close it
    setShowTermsModal(false);
  };

  if (authLoading || isChecking) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
      <TermsModal 
        visible={showTermsModal && isAuthenticated} 
        onAccept={handleTermsAccept} 
      />
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
        <Stack.Screen name="community" options={{ presentation: 'card' }} />
        <Stack.Screen name="donate" options={{ presentation: 'card' }} />
        <Stack.Screen name="progress" options={{ presentation: 'card' }} />
      </Stack>
    </>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
});
