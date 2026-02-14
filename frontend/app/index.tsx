import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Redirect } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { COLORS } from '../src/utils/theme';
import { api } from '../src/utils/api';
import { TermsModal } from '../src/components/TermsModal';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const [checkingConsent, setCheckingConsent] = useState(false);
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [showTermsModal, setShowTermsModal] = useState(false);

  // Check consent when authenticated
  useEffect(() => {
    const checkConsent = async () => {
      if (isAuthenticated && !isLoading && hasConsent === null && !checkingConsent) {
        setCheckingConsent(true);
        try {
          const status = await api.getConsentStatus();
          setHasConsent(status.accepted);
          if (!status.accepted) {
            setShowTermsModal(true);
          }
        } catch (error) {
          console.log('Error checking consent:', error);
          setHasConsent(false);
          setShowTermsModal(true);
        } finally {
          setCheckingConsent(false);
        }
      }
    };

    checkConsent();
  }, [isAuthenticated, isLoading, hasConsent, checkingConsent]);

  const handleTermsAccept = () => {
    setShowTermsModal(false);
    setHasConsent(true);
  };

  if (isLoading || checkingConsent) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Cibo Spirituale</Text>
      </View>
    );
  }

  // Show terms modal if authenticated but no consent
  if (isAuthenticated && showTermsModal) {
    return (
      <View style={styles.container}>
        <TermsModal visible={showTermsModal} onAccept={handleTermsAccept} />
      </View>
    );
  }

  // Redirect based on auth and consent state
  if (isAuthenticated && hasConsent === true) {
    return <Redirect href="/(tabs)" />;
  }

  if (!isAuthenticated) {
    return <Redirect href="/(auth)/login" />;
  }

  // Still checking consent, show loading
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
