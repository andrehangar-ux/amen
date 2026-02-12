import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface DonationConfig {
  paypal_email: string;
  paypal_link: string;
  iban: string;
  intestatario: string;
  banca: string;
}

export default function DonateScreen() {
  const [config, setConfig] = useState<DonationConfig | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.getDonationConfig();
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, label: string) => {
    await Clipboard.setStringAsync(text);
    Alert.alert('Copiato!', `${label} copiato negli appunti`);
  };

  const handlePayPal = async () => {
    if (config?.paypal_link) {
      const canOpen = await Linking.canOpenURL(config.paypal_link);
      if (canOpen) {
        await Linking.openURL(config.paypal_link);
      } else {
        // Fallback: copy link
        await Clipboard.setStringAsync(config.paypal_link);
        Alert.alert('Link PayPal', `Link copiato: ${config.paypal_link}\n\nApri il browser e incolla il link.`);
      }
    } else {
      Alert.alert('Errore', 'Link PayPal non disponibile');
    }
  };

  const handleSubmitDonation = async () => {
    if (!amount || !selectedMethod) {
      Alert.alert('Errore', 'Inserisci un importo e seleziona un metodo');
      return;
    }

    setSubmitting(true);
    try {
      // First register the donation
      await api.createDonation(
        parseFloat(amount),
        selectedMethod,
        message || undefined
      );

      // Then open PayPal if selected
      if (selectedMethod === 'paypal') {
        await handlePayPal();
      }

      Alert.alert(
        'Grazie!',
        selectedMethod === 'bonifico'
          ? 'Completa il bonifico con i dati forniti. Dio ti benedica!'
          : 'La tua generosità sostiene il ministero. Dio ti benedica!'
      );

      setAmount('');
      setMessage('');
      setSelectedMethod(null);
    } catch (error) {
      console.log('Donation error:', error);
      // Even if registration fails, try to open PayPal
      if (selectedMethod === 'paypal') {
        await handlePayPal();
      }
      Alert.alert('Info', 'Procedi con la donazione. Grazie!');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Sostieni il Ministero</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.heroCard}>
          <Ionicons name="heart" size={40} color={COLORS.error} />
          <Text style={styles.heroTitle}>Offerta Libera</Text>
          <Text style={styles.heroText}>
            La tua generosità permette di mantenere Amen! gratuito e di
            sviluppare nuove funzionalità per la crescita spirituale di tutti.
          </Text>
        </View>

        <Text style={styles.sectionTitle}>Seleziona Importo</Text>
        <View style={styles.amountButtons}>
          {['5', '10', '20', '50', '100'].map((val) => (
            <TouchableOpacity
              key={val}
              style={[
                styles.amountButton,
                amount === val && styles.amountButtonSelected,
              ]}
              onPress={() => setAmount(val)}
            >
              <Text
                style={[
                  styles.amountButtonText,
                  amount === val && styles.amountButtonTextSelected,
                ]}
              >
                €{val}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TextInput
          style={styles.input}
          placeholder="Oppure inserisci un importo"
          placeholderTextColor={COLORS.textMuted}
          keyboardType="numeric"
          value={amount}
          onChangeText={setAmount}
        />

        <Text style={styles.sectionTitle}>Metodo di Pagamento</Text>

        <TouchableOpacity
          style={[
            styles.methodCard,
            selectedMethod === 'paypal' && styles.methodCardSelected,
          ]}
          onPress={() => setSelectedMethod('paypal')}
        >
          <View style={[styles.methodIcon, { backgroundColor: '#0070BA15' }]}>
            <Ionicons name="logo-paypal" size={28} color="#0070BA" />
          </View>
          <View style={styles.methodContent}>
            <Text style={styles.methodTitle}>PayPal</Text>
            <Text style={styles.methodSubtitle}>{config?.paypal_email}</Text>
          </View>
          {selectedMethod === 'paypal' && (
            <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.methodCard,
            selectedMethod === 'bonifico' && styles.methodCardSelected,
          ]}
          onPress={() => setSelectedMethod('bonifico')}
        >
          <View style={[styles.methodIcon, { backgroundColor: COLORS.primary + '15' }]}>
            <Ionicons name="business" size={28} color={COLORS.primary} />
          </View>
          <View style={styles.methodContent}>
            <Text style={styles.methodTitle}>Bonifico Bancario</Text>
            <Text style={styles.methodSubtitle}>{config?.banca}</Text>
          </View>
          {selectedMethod === 'bonifico' && (
            <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
          )}
        </TouchableOpacity>

        {selectedMethod === 'bonifico' && config && (
          <View style={styles.bankDetails}>
            <Text style={styles.bankLabel}>Dati Bancari:</Text>

            <View style={styles.bankRow}>
              <View style={styles.bankInfo}>
                <Text style={styles.bankFieldLabel}>IBAN</Text>
                <Text style={styles.bankFieldValue}>{config.iban}</Text>
              </View>
              <TouchableOpacity
                style={styles.copyButton}
                onPress={() => copyToClipboard(config.iban, 'IBAN')}
              >
                <Ionicons name="copy" size={20} color={COLORS.primary} />
              </TouchableOpacity>
            </View>

            <View style={styles.bankRow}>
              <View style={styles.bankInfo}>
                <Text style={styles.bankFieldLabel}>Intestatario</Text>
                <Text style={styles.bankFieldValue}>{config.intestatario}</Text>
              </View>
              <TouchableOpacity
                style={styles.copyButton}
                onPress={() => copyToClipboard(config.intestatario, 'Intestatario')}
              >
                <Ionicons name="copy" size={20} color={COLORS.primary} />
              </TouchableOpacity>
            </View>

            <View style={styles.bankRow}>
              <View style={styles.bankInfo}>
                <Text style={styles.bankFieldLabel}>Banca</Text>
                <Text style={styles.bankFieldValue}>{config.banca}</Text>
              </View>
            </View>

            <Text style={styles.causaleText}>
              Causale: Offerta libera Amen!
            </Text>
          </View>
        )}

        <TextInput
          style={[styles.input, styles.messageInput]}
          placeholder="Messaggio (opzionale)"
          placeholderTextColor={COLORS.textMuted}
          multiline
          numberOfLines={3}
          value={message}
          onChangeText={setMessage}
        />

        <TouchableOpacity
          style={[
            styles.submitButton,
            (!amount || !selectedMethod || submitting) && styles.submitButtonDisabled,
          ]}
          onPress={handleSubmitDonation}
          disabled={!amount || !selectedMethod || submitting}
        >
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>
              {selectedMethod === 'paypal' ? 'Vai a PayPal' : 'Registra Donazione'}
            </Text>
          )}
        </TouchableOpacity>

        <Text style={styles.bibleVerse}>
          "Ciascuno dia come ha deliberato nel suo cuore, non di malavoglia né per
          forza, perché Dio ama un donatore allegro." - 2 Corinzi 9:7
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  heroCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.md,
  },
  heroText: {
    fontSize: 15,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: SPACING.sm,
    lineHeight: 22,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  amountButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  amountButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  amountButtonSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  amountButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  amountButtonTextSelected: {
    color: '#fff',
  },
  input: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    marginBottom: SPACING.lg,
  },
  messageInput: {
    height: 80,
    textAlignVertical: 'top',
  },
  methodCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  methodCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '08',
  },
  methodIcon: {
    width: 50,
    height: 50,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  methodContent: {
    flex: 1,
  },
  methodTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  methodSubtitle: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  bankDetails: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
  },
  bankLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  bankRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  bankInfo: {
    flex: 1,
  },
  bankFieldLabel: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  bankFieldValue: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
    marginTop: 2,
  },
  copyButton: {
    padding: SPACING.sm,
  },
  causaleText: {
    fontSize: 13,
    fontStyle: 'italic',
    color: COLORS.textLight,
    marginTop: SPACING.sm,
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.md,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
  bibleVerse: {
    fontSize: 14,
    fontStyle: 'italic',
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: SPACING.xl,
    paddingHorizontal: SPACING.md,
    lineHeight: 22,
  },
});
