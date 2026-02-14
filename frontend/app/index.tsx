import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { router, Redirect } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { COLORS } from '../src/utils/theme';
import { api } from '../src/utils/api';
import { TermsModal } from '../src/components/TermsModal';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const [checkingConsent, setCheckingConsent] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);

  // Check consent and navigate when authenticated
  useEffect(() => {
    const checkAndNavigate = async () => {
      if (isAuthenticated && !isLoading && !checkingConsent) {
        setCheckingConsent(true);
        try {
          const status = await api.getConsentStatus();
          if (!status.accepted) {
            setShowTermsModal(true);
          } else {
            router.replace('/(tabs)');
          }
        } catch (error) {
          console.log('Error checking consent:', error);
          setShowTermsModal(true);
        }
        setCheckingConsent(false);
      }
    };

    checkAndNavigate();
  }, [isAuthenticated, isLoading]);

  const handleTermsAccept = () => {
    setShowTermsModal(false);
    router.replace('/(tabs)');
  };

  // Show loading while checking auth
  if (isLoading || checkingConsent) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cibo Spirituale</Text>
      </View>
    );
  }

  // Not authenticated - go to login
  if (!isAuthenticated) {
    return <Redirect href="/(auth)/login" />;
  }

  // Authenticated but showing terms modal
  if (showTermsModal) {
    return (
      <View style={styles.container}>
        <TermsModal visible={showTermsModal} onAccept={handleTermsAccept} />
      </View>
    );
  }

  // Default loading state while redirect happens
  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={COLORS.primary} />
      <Text style={styles.loadingText}>Cibo Spirituale</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.primary,
  },
});
