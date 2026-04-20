import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Icon } from './Icon';
import { router } from 'expo-router';
import { api } from '../utils/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../utils/theme';

interface SocialGuardProps {
  children: React.ReactNode;
}

export const SocialGuard: React.FC<SocialGuardProps> = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [blocked, setBlocked] = useState(false);
  const [blockReason, setBlockReason] = useState('');
  const [blockMessage, setBlockMessage] = useState('');
  const [showSafetyReminder, setShowSafetyReminder] = useState(false);
  const [safetyAcknowledged, setSafetyAcknowledged] = useState(false);
  const [isMinor, setIsMinor] = useState(false);

  const checkAccess = useCallback(async () => {
    try {
      const access = await api.canUseSocialFeatures();

      if (!access.can_use_social) {
        setBlocked(true);
        setBlockReason(access.reason);
        setBlockMessage(access.message || '');
        setIsMinor(access.is_minor || false);
        setLoading(false);
        return;
      }

      if (access.is_minor) {
        setIsMinor(true);
        setShowSafetyReminder(true);
      } else {
        setSafetyAcknowledged(true);
      }
    } catch (error) {
      setBlocked(false);
      setSafetyAcknowledged(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAccess();
  }, [checkAccess]);

  const handleAcknowledgeSafety = async () => {
    try {
      await api.acknowledgeSafetyReminder();
    } catch (e) {}
    setShowSafetyReminder(false);
    setSafetyAcknowledged(true);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (blocked) {
    return (
      <View style={styles.blockedContainer}>
        <View style={styles.blockedIcon}>
          <Icon name="shield-checkmark" size={64} color={COLORS.primary} />
        </View>
        <Text style={styles.blockedTitle}>
          {blockReason === 'no_parent_pin'
            ? 'Configurazione Genitore Richiesta'
            : 'Funzionalita Social Disabilitate'}
        </Text>
        <Text style={styles.blockedDesc}>
          {blockReason === 'no_parent_pin'
            ? 'Per la tua sicurezza, un genitore o tutore deve prima configurare un PIN di Controllo Genitori nelle Impostazioni e abilitare le funzionalita social per poter utilizzare questa sezione.'
            : (blockMessage || 'Le funzionalita social sono state disabilitate dal Controllo Genitori. Chiedi a un genitore di modificare le impostazioni.')}
        </Text>
        <View style={styles.infoBox}>
          <Icon name="information-circle" size={18} color={COLORS.primary} />
          <Text style={styles.infoText}>
            Solo un adulto puo abilitare le funzionalita social tramite il PIN di Controllo Genitori nelle Impostazioni.
          </Text>
        </View>
        <TouchableOpacity
          style={styles.settingsBtn}
          onPress={() => router.push('/settings')}
          data-testid="social-guard-settings-btn"
        >
          <Icon name="settings" size={18} color="#fff" />
          <Text style={styles.settingsBtnText}>Vai alle Impostazioni</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          data-testid="social-guard-back-btn"
        >
          <Text style={styles.backBtnText}>Torna Indietro</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <>
      {/* Safety Reminder Modal - shown EVERY session for minors */}
      <Modal visible={showSafetyReminder && !safetyAcknowledged} transparent animationType="fade" onRequestClose={() => {}}>
        <View style={styles.modalOverlay}>
          <View style={styles.safetyModal}>
            <View style={styles.warningIcon}>
              <Icon name="warning" size={48} color="#E74C3C" />
            </View>
            <Text style={styles.safetyTitle}>AVVISO DI SICUREZZA ONLINE</Text>
            <Text style={styles.safetySubtitle}>
              IMPORTANTE: Prima di continuare, leggi attentamente. Le interazioni online comportano rischi reali.
            </Text>

            <View style={styles.bulletList}>
              <View style={styles.bulletItem}>
                <Icon name="warning" size={16} color="#E74C3C" />
                <Text style={styles.bulletText}>
                  Le persone online potrebbero NON essere chi dicono di essere. Le interazioni online hanno conseguenze nel mondo reale.
                </Text>
              </View>
              <View style={styles.bulletItem}>
                <Icon name="close-circle" size={16} color="#E74C3C" />
                <Text style={styles.bulletText}>
                  NON condividere MAI: indirizzo di casa, scuola, numero di telefono, foto personali, posizione o password.
                </Text>
              </View>
              <View style={styles.bulletItem}>
                <Icon name="people" size={16} color={COLORS.primary} />
                <Text style={styles.bulletText}>
                  Chatta SOLO con persone che conosci nella vita reale e di cui ti fidi (amici, familiari).
                </Text>
              </View>
              <View style={styles.bulletItem}>
                <Icon name="hand-left" size={16} color="#F39C12" />
                <Text style={styles.bulletText}>
                  Se qualcuno ti mette a disagio o ti chiede informazioni personali, FERMATI subito e parlane con un genitore o adulto di fiducia.
                </Text>
              </View>
              <View style={styles.bulletItem}>
                <Icon name="eye-off" size={16} color="#9B59B6" />
                <Text style={styles.bulletText}>
                  NON incontrare MAI di persona qualcuno conosciuto online senza la presenza di un adulto.
                </Text>
              </View>
            </View>

            <View style={styles.parentNote}>
              <Icon name="shield-checkmark" size={16} color={COLORS.primary} />
              <Text style={styles.parentNoteText}>
                L'accesso a questa sezione e stato approvato da un genitore tramite il Controllo Genitori.
              </Text>
            </View>

            <TouchableOpacity
              style={styles.acknowledgeBtn}
              onPress={handleAcknowledgeSafety}
              data-testid="safety-guard-acknowledge-btn"
            >
              <Icon name="checkmark-circle" size={20} color="#fff" />
              <Text style={styles.acknowledgeBtnText}>Ho letto e capisco i rischi</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Only show content after safety is acknowledged (or if adult) */}
      {safetyAcknowledged ? children : (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      )}
    </>
  );
};

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  // Blocked screen
  blockedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    padding: SPACING.xl,
  },
  blockedIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: COLORS.primary + '12',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  blockedTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  blockedDesc: {
    fontSize: 15,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.lg,
    maxWidth: 320,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.primary + '12',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    maxWidth: 320,
    gap: SPACING.sm,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.primary,
    lineHeight: 19,
  },
  settingsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  settingsBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  backBtn: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
  },
  backBtnText: {
    color: COLORS.textLight,
    fontSize: 14,
  },
  // Safety Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.md,
  },
  safetyModal: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: SPACING.lg,
    width: '100%',
    maxWidth: 400,
    maxHeight: '90%',
    alignItems: 'center',
  },
  warningIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#E74C3C15',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  safetyTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#E74C3C',
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  safetySubtitle: {
    fontSize: 14,
    color: COLORS.text,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: SPACING.md,
  },
  bulletList: {
    width: '100%',
    marginBottom: SPACING.md,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
    gap: SPACING.sm,
  },
  bulletText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 19,
  },
  parentNote: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.sm,
    marginBottom: SPACING.md,
    gap: SPACING.sm,
    width: '100%',
  },
  parentNoteText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.primary,
    fontStyle: 'italic',
  },
  acknowledgeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
    width: '100%',
    justifyContent: 'center',
  },
  acknowledgeBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
