import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

const DONATION_AMOUNTS = [5, 10, 20, 50, 100];

export default function DonateScreen() {
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState('');
  const [selectedMethod, setSelectedMethod] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const getAmount = () => {
    if (customAmount) return parseFloat(customAmount);
    return selectedAmount || 0;
  };

  const handleDonate = async () => {
    const amount = getAmount();
    if (!amount || amount <= 0) {
      Alert.alert('Errore', 'Seleziona o inserisci un importo');
      return;
    }
    if (!selectedMethod) {
      Alert.alert('Errore', 'Seleziona un metodo di pagamento');
      return;
    }

    setLoading(true);
    try {
      const donation = await api.createDonation(amount, selectedMethod, message || undefined);
      setResult(donation);
    } catch (error: any) {
      Alert.alert('Errore', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePayPalRedirect = () => {
    if (result?.paypal_link) {
      Linking.openURL(result.paypal_link);
    }
  };

  if (result) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Donazione</Text>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.resultContainer}>
          <View style={styles.resultIcon}>
            <Ionicons 
              name={result.status === 'completed' ? 'checkmark-circle' : 'time'} 
              size={64} 
              color={result.status === 'completed' ? COLORS.success : COLORS.accent} 
            />
          </View>
          <Text style={styles.resultTitle}>
            {result.status === 'completed' ? 'Grazie!' : 'Donazione in attesa'}
          </Text>
          <Text style={styles.resultAmount}>€{result.amount.toFixed(2)}</Text>
          
          {result.method === 'paypal' && (
            <TouchableOpacity style={styles.paypalButton} onPress={handlePayPalRedirect}>
              <Ionicons name="logo-paypal" size={24} color="#003087" />
              <Text style={styles.paypalButtonText}>Completa con PayPal</Text>
            </TouchableOpacity>
          )}

          {result.method === 'bonifico' && result.bank_details && (
            <View style={styles.bankDetails}>
              <Text style={styles.bankTitle}>Dettagli Bancari</Text>
              <View style={styles.bankRow}>
                <Text style={styles.bankLabel}>IBAN:</Text>
                <Text style={styles.bankValue}>{result.bank_details.iban}</Text>
              </View>
              <View style={styles.bankRow}>
                <Text style={styles.bankLabel}>Intestatario:</Text>
                <Text style={styles.bankValue}>{result.bank_details.intestatario}</Text>
              </View>
              <View style={styles.bankRow}>
                <Text style={styles.bankLabel}>Causale:</Text>
                <Text style={styles.bankValue}>{result.bank_details.causale}</Text>
              </View>
            </View>
          )}

          {result.method === 'mock' && (
            <Text style={styles.mockNote}>Questa è una donazione di prova (MOCK)</Text>
          )}

          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => router.back()}
          >
            <Text style={styles.doneButtonText}>Torna all'App</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Fai una Donazione</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Intro */}
        <View style={styles.introCard}>
          <Ionicons name="heart" size={40} color={COLORS.error} />
          <Text style={styles.introTitle}>Supporta il Ministero</Text>
          <Text style={styles.introText}>
            La tua donazione aiuta a mantenere Cibo Spirituale gratuito e accessibile a tutti.
          </Text>
        </View>

        {/* Amount Selection */}
        <Text style={styles.sectionTitle}>Seleziona Importo</Text>
        <View style={styles.amountsContainer}>
          {DONATION_AMOUNTS.map((amount) => (
            <TouchableOpacity
              key={amount}
              style={[
                styles.amountButton,
                selectedAmount === amount && styles.amountButtonSelected,
              ]}
              onPress={() => {
                setSelectedAmount(amount);
                setCustomAmount('');
              }}
            >
              <Text
                style={[
                  styles.amountText,
                  selectedAmount === amount && styles.amountTextSelected,
                ]}
              >
                €{amount}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.customAmountContainer}>
          <Text style={styles.customLabel}>O inserisci un importo personalizzato:</Text>
          <View style={styles.customInputContainer}>
            <Text style={styles.currencySymbol}>€</Text>
            <TextInput
              style={styles.customInput}
              placeholder="0.00"
              placeholderTextColor={COLORS.textMuted}
              value={customAmount}
              onChangeText={(text) => {
                setCustomAmount(text);
                setSelectedAmount(null);
              }}
              keyboardType="decimal-pad"
            />
          </View>
        </View>

        {/* Payment Method */}
        <Text style={styles.sectionTitle}>Metodo di Pagamento</Text>
        <View style={styles.methodsContainer}>
          <TouchableOpacity
            style={[
              styles.methodButton,
              selectedMethod === 'paypal' && styles.methodButtonSelected,
            ]}
            onPress={() => setSelectedMethod('paypal')}
          >
            <Ionicons name="logo-paypal" size={24} color="#003087" />
            <Text style={styles.methodText}>PayPal</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.methodButton,
              selectedMethod === 'bonifico' && styles.methodButtonSelected,
            ]}
            onPress={() => setSelectedMethod('bonifico')}
          >
            <Ionicons name="card-outline" size={24} color={COLORS.primary} />
            <Text style={styles.methodText}>Bonifico</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.methodButton,
              selectedMethod === 'mock' && styles.methodButtonSelected,
            ]}
            onPress={() => setSelectedMethod('mock')}
          >
            <Ionicons name="flash-outline" size={24} color={COLORS.accent} />
            <Text style={styles.methodText}>Test (Mock)</Text>
          </TouchableOpacity>
        </View>

        {/* Message */}
        <Text style={styles.sectionTitle}>Messaggio (opzionale)</Text>
        <TextInput
          style={styles.messageInput}
          placeholder="Aggiungi un messaggio alla tua donazione..."
          placeholderTextColor={COLORS.textMuted}
          value={message}
          onChangeText={setMessage}
          multiline
          numberOfLines={3}
        />

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.donateButton, loading && styles.donateButtonDisabled]}
          onPress={handleDonate}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="heart" size={20} color="#fff" />
              <Text style={styles.donateButtonText}>
                Dona €{getAmount() > 0 ? getAmount().toFixed(2) : '0.00'}
              </Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: SPACING.xxl,
  },
  introCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  introTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.md,
    marginBottom: SPACING.sm,
  },
  introText: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 22,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
    marginTop: SPACING.md,
  },
  amountsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  amountButton: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  amountButtonSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  amountText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  amountTextSelected: {
    color: COLORS.primary,
  },
  customAmountContainer: {
    marginTop: SPACING.md,
  },
  customLabel: {
    fontSize: 14,
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
  },
  customInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textLight,
    marginRight: SPACING.sm,
  },
  customInput: {
    flex: 1,
    fontSize: 18,
    color: COLORS.text,
    paddingVertical: SPACING.md,
  },
  methodsContainer: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  methodButton: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.card,
    borderWidth: 2,
    borderColor: COLORS.border,
    gap: SPACING.xs,
  },
  methodButtonSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  methodText: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.text,
  },
  messageInput: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 15,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.border,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  donateButton: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.xl,
    gap: SPACING.sm,
  },
  donateButtonDisabled: {
    opacity: 0.7,
  },
  donateButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  resultContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
  },
  resultIcon: {
    marginBottom: SPACING.md,
  },
  resultTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  resultAmount: {
    fontSize: 36,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.lg,
  },
  paypalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFC439',
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  paypalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#003087',
  },
  bankDetails: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    width: '100%',
    ...SHADOWS.small,
  },
  bankTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  bankRow: {
    flexDirection: 'row',
    marginBottom: SPACING.sm,
  },
  bankLabel: {
    fontSize: 14,
    color: COLORS.textLight,
    width: 100,
  },
  bankValue: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '500',
  },
  mockNote: {
    fontSize: 14,
    color: COLORS.accent,
    fontStyle: 'italic',
    marginBottom: SPACING.lg,
  },
  doneButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.lg,
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
