import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../src/store/authStore';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { COLORS } from '../src/utils/theme';
import * as SplashScreen from 'expo-splash-screen';
import { TermsModal } from '../src/components/TermsModal';
import { api } from '../src/utils/api';

// Prevent splash screen from auto-hiding
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const { checkAuth, isLoading: authLoading, isAuthenticated } = useAuthStore();
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [checkingTerms, setCheckingTerms] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  // Check terms acceptance status when user is authenticated
  useEffect(() => {
    const checkTermsStatus = async () => {
      if (isAuthenticated && !authLoading) {
        setCheckingTerms(true);
        try {
          const status = await api.getConsentStatus();
          if (!status.accepted) {
            setShowTermsModal(true);
          }
        } catch (error) {
          // If error fetching consent, show modal to be safe
          console.log('Error checking consent:', error);
          setShowTermsModal(true);
        } finally {
          setCheckingTerms(false);
        }
      }
    };

    checkTermsStatus();
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    if (!authLoading && !checkingTerms) {
      SplashScreen.hideAsync();
    }
  }, [authLoading, checkingTerms]);

  const handleTermsAccept = () => {
    setShowTermsModal(false);
  };

  if (authLoading || checkingTerms) {
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
