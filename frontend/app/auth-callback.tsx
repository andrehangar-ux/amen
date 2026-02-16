import React, { useEffect, useState, useRef } from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { COLORS } from '../src/utils/theme';

export default function AuthCallbackScreen() {
  const params = useLocalSearchParams();
  const [status, setStatus] = useState('Elaborazione login...');
  const { googleLogin } = useAuthStore();
  const hasProcessed = useRef(false);

  useEffect(() => {
    const handleCallback = async () => {
      if (hasProcessed.current) return;
      hasProcessed.current = true;
      
      try {
        let sessionId = params.session_id as string;
        
        if (Platform.OS === 'web') {
          // Extract session_id from query params or hash
          if (!sessionId) {
            const urlParams = new URLSearchParams(window.location.search);
            sessionId = urlParams.get('session_id') || '';
          }
          if (!sessionId && window.location.hash) {
            const hashString = window.location.hash.substring(1);
            const hashParams = new URLSearchParams(hashString);
            sessionId = hashParams.get('session_id') || '';
            if (!sessionId) {
              const match = window.location.hash.match(/session_id=([^&]+)/);
              if (match) sessionId = match[1];
            }
          }
          
          // If loaded in a MOBILE BROWSER (from OAuth redirect), redirect to app deep link
          if (sessionId && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
            const appScheme = 'amen';
            setStatus('Apertura app...');
            window.location.href = `${appScheme}://auth-callback?session_id=${sessionId}`;
            // Fallback: if the app doesn't open, show message after delay
            setTimeout(() => {
              setStatus('Se l\'app non si apre automaticamente, torna all\'app manualmente.');
            }, 3000);
            return;
          }
        }
        
        // On mobile native, check deep link URL
        if (!sessionId && Platform.OS !== 'web') {
          const Linking = (await import('expo-linking')).default;
          const url = await Linking.getInitialURL();
          if (url) {
            for (const pattern of [/#session_id=([^&]+)/, /\?session_id=([^&]+)/, /session_id=([^&]+)/]) {
              const match = url.match(pattern);
              if (match) { sessionId = match[1]; break; }
            }
          }
        }
        
        console.log('Auth callback - Session ID:', sessionId, 'Platform:', Platform.OS);
        
        if (sessionId) {
          setStatus('Accesso in corso...');
          await googleLogin(sessionId);
          setStatus('Login completato!');
          router.replace('/(tabs)');
        } else {
          setStatus('Sessione non trovata');
          setTimeout(() => router.replace('/(auth)/login'), 2000);
        }
      } catch (error: any) {
        console.error('Auth callback error:', error);
        setStatus(`Errore: ${error.message}`);
        setTimeout(() => router.replace('/(auth)/login'), 3000);
      }
    };

    handleCallback();
  }, []);

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
