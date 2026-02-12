import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { COLORS } from '../src/utils/theme';

export default function AuthCallbackScreen() {
  const params = useLocalSearchParams();
  const [status, setStatus] = useState('Elaborazione login...');
  const { googleLogin } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get session_id from URL params
        const sessionId = params.session_id as string;
        
        console.log('Auth callback params:', params);
        console.log('Session ID:', sessionId);
        
        if (sessionId) {
          setStatus('Accesso in corso...');
          await googleLogin(sessionId);
          setStatus('Login completato!');
          router.replace('/(tabs)');
        } else {
          setStatus('Sessione non trovata');
          setTimeout(() => {
            router.replace('/(auth)/login');
          }, 2000);
        }
      } catch (error: any) {
        console.error('Auth callback error:', error);
        setStatus(`Errore: ${error.message}`);
        setTimeout(() => {
          router.replace('/(auth)/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [params.session_id]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={COLORS.primary} />
      <Text style={styles.text}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  text: {
    marginTop: 20,
    fontSize: 16,
    color: COLORS.text,
  },
});
