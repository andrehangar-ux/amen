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
      // Prevent double processing in StrictMode
      if (hasProcessed.current) return;
      hasProcessed.current = true;
      
      try {
        // Get session_id from different sources
        let sessionId = params.session_id as string;
        
        // On web, also check the URL hash and search params
        if (Platform.OS === 'web' && !sessionId) {
          // Check query params first
          const urlParams = new URLSearchParams(window.location.search);
          sessionId = urlParams.get('session_id') || '';
          
          // Then check hash (Emergent Auth puts session_id in hash)
          if (!sessionId && window.location.hash) {
            const hashString = window.location.hash.substring(1); // Remove #
            const hashParams = new URLSearchParams(hashString);
            sessionId = hashParams.get('session_id') || '';
            
            // Also try direct extraction if URLSearchParams fails
            if (!sessionId) {
              const match = window.location.hash.match(/session_id=([^&]+)/);
              if (match) {
                sessionId = match[1];
              }
            }
          }
        }
        
        // On mobile, also check for session_id in the URL fragment
        if (!sessionId && Platform.OS !== 'web') {
          // The session_id might come through Linking
          const Linking = (await import('expo-linking')).default;
          const url = await Linking.getInitialURL();
          if (url) {
            const patterns = [
              /#session_id=([^&]+)/,
              /\?session_id=([^&]+)/,
              /session_id=([^&]+)/
            ];
            
            for (const pattern of patterns) {
              const match = url.match(pattern);
              if (match) {
                sessionId = match[1];
                break;
              }
            }
          }
        }
        
        console.log('Auth callback - Session ID:', sessionId);
        console.log('Auth callback - Platform:', Platform.OS);
        
        if (sessionId) {
          setStatus('Accesso in corso...');
          await googleLogin(sessionId);
          setStatus('Login completato!');
          router.replace('/(tabs)');
        } else {
          setStatus('Sessione non trovata');
          console.error('No session_id found in callback');
          console.log('Current URL hash:', Platform.OS === 'web' ? window.location.hash : 'N/A');
          console.log('Current URL search:', Platform.OS === 'web' ? window.location.search : 'N/A');
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
