import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Modal,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router, useLocalSearchParams } from 'expo-router';
import { api } from '../src/utils/api';
import { useAuthStore } from '../src/store/authStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';
import { format } from 'date-fns';
import { useTranslation } from '../src/store/languageStore';

interface PrivateMessage {
  message_id: string;
  sender_id: string;
  sender_name: string;
  receiver_id: string;
  content: string;
  read: boolean;
  created_at: string;
}

interface SafetyStatus {
  is_minor: boolean;
  parental_consent: boolean;
  safety_reminder_shown: boolean;
  safety_message?: {
    title: string;
    message: string;
    confirm: string;
  };
}

export default function PrivateChatScreen() {
  const { userId, userName } = useLocalSearchParams<{ userId: string; userName: string }>();
  const { user, sessionToken } = useAuthStore();
  const { t } = useTranslation();
  const [messages, setMessages] = useState<PrivateMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showSafetyModal, setShowSafetyModal] = useState(false);
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatus | null>(null);
  const [chatBlocked, setChatBlocked] = useState(false);
  const [blockReason, setBlockReason] = useState('');
  const flatListRef = useRef<FlatList>(null);

  // Check safety status for minors
  const checkSafetyStatus = useCallback(async () => {
    try {
      const status = await api.getSafetyStatus();
      setSafetyStatus(status);
      
      // Show safety reminder for minors if not already shown
      if (status.is_minor && !status.safety_reminder_shown && status.safety_message) {
        setShowSafetyModal(true);
      }
    } catch (error) {
      console.log('Error checking safety status:', error);
    }
  }, []);

  useEffect(() => {
    checkSafetyStatus();
  }, [checkSafetyStatus]);

  const loadMessages = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await api.getPrivateMessages(userId);
      setMessages(data);
      setChatBlocked(false);
    } catch (error: any) {
      console.log('Error loading messages:', error);
      // Check if chat is blocked for minors
      if (error.message?.includes('amici') || error.message?.includes('friends')) {
        setChatBlocked(true);
        setBlockReason(error.message);
      }
    }
  }, [userId]);

  useEffect(() => {
    loadMessages().finally(() => setLoading(false));
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [loadMessages]);

  const handleAcknowledgeSafety = async () => {
    try {
      await api.acknowledgeSafetyReminder();
      setShowSafetyModal(false);
    } catch (error) {
      console.log('Error acknowledging safety:', error);
      setShowSafetyModal(false);
    }
  };

  const handleSend = async () => {
    if (!newMessage.trim() || !userId) return;
    
    // Check if minor needs parental consent for sharing info
    if (safetyStatus?.is_minor && !safetyStatus?.parental_consent) {
      // Check if message contains potential personal info
      const personalInfoPatterns = /(\d{3,}|\b(via|strada|indirizzo|scuola|telefono|cell|numero)\b)/i;
      if (personalInfoPatterns.test(newMessage)) {
        const alertMessage = Platform.OS === 'web' 
          ? window.confirm(t('parentalConsentRequired') || 'Per condividere informazioni personali è richiesto il consenso dei genitori. Vuoi continuare comunque?')
          : null;
        
        if (Platform.OS !== 'web') {
          Alert.alert(
            t('warning') || 'Attenzione',
            t('parentalConsentRequired') || 'Per condividere informazioni personali è richiesto il consenso dei genitori.',
            [{ text: 'OK' }]
          );
          return;
        } else if (!alertMessage) {
          return;
        }
      }
    }
    
    setSending(true);
    try {
      await api.sendPrivateMessage(userId, newMessage.trim());
      setNewMessage('');
      await loadMessages();
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (error) {
      console.log('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const renderMessage = ({ item }: { item: PrivateMessage }) => {
    const isOwn = item.sender_id === user?.user_id;
    return (
      <View style={[styles.messageBubble, isOwn ? styles.ownBubble : styles.otherBubble]}>
        <Text style={[styles.messageText, isOwn && styles.ownMessageText]}>{item.content}</Text>
        <Text style={[styles.messageTime, isOwn && styles.ownTimeText]}>
          {format(new Date(item.created_at), 'HH:mm')}
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Safety Reminder Modal */}
      <Modal
        visible={showSafetyModal}
        transparent
        animationType="fade"
        onRequestClose={() => {}}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.safetyModal}>
            <View style={styles.safetyIconContainer}>
              <Icon name="shield-checkmark" size={48} color={COLORS.primary} />
            </View>
            <Text style={styles.safetyTitle}>
              {safetyStatus?.safety_message?.title || t('safetyReminderTitle') || 'Promemoria Sicurezza'}
            </Text>
            <Text style={styles.safetyMessage}>
              {safetyStatus?.safety_message?.message || t('safetyReminderMessage') || 'Ricorda: non condividere mai informazioni personali con persone che non conosci.'}
            </Text>
            <View style={styles.safetyBullets}>
              <Text style={styles.safetyBullet}>• Non condividere dati personali</Text>
              <Text style={styles.safetyBullet}>• Chatta solo con amici e familiari</Text>
              <Text style={styles.safetyBullet}>• Se qualcosa ti preoccupa, parla con un adulto</Text>
            </View>
            <TouchableOpacity style={styles.safetyButton} onPress={handleAcknowledgeSafety}>
              <Text style={styles.safetyButtonText}>
                {safetyStatus?.safety_message?.confirm || t('iUnderstand') || 'Ho capito'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} data-testid="private-chat-back-btn">
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <View style={styles.headerAvatar}>
            <Text style={styles.headerAvatarText}>{(userName || 'U').charAt(0).toUpperCase()}</Text>
          </View>
          <Text style={styles.headerName} numberOfLines={1}>{userName || 'Utente'}</Text>
        </View>
        <View style={{ width: 24 }} />
      </View>

      {/* Chat Blocked for Minors */}
      {chatBlocked ? (
        <View style={styles.blockedContainer}>
          <Icon name="lock-closed" size={64} color={COLORS.warning} />
          <Text style={styles.blockedTitle}>{t('chatOnlyWithFriends') || 'Chat non disponibile'}</Text>
          <Text style={styles.blockedMessage}>
            {blockReason || t('addFriendToChat') || 'Per la tua sicurezza, puoi chattare solo con i tuoi amici. Aggiungi questo utente come amico per iniziare una conversazione.'}
          </Text>
          <TouchableOpacity style={styles.addFriendButton} onPress={() => router.back()}>
            <Icon name="person-add" size={20} color="#fff" />
            <Text style={styles.addFriendButtonText}>Torna indietro</Text>
          </TouchableOpacity>
        </View>
      ) : loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.message_id}
          contentContainerStyle={styles.messagesList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Icon name="chatbubble-ellipses-outline" size={48} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>Inizia la conversazione!</Text>
            </View>
          }
        />
      )}

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={90}
      >
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="Scrivi un messaggio..."
            placeholderTextColor={COLORS.textMuted}
            value={newMessage}
            onChangeText={setNewMessage}
            multiline
            maxLength={500}
            data-testid="private-chat-input"
          />
          <TouchableOpacity
            style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={sending || !newMessage.trim()}
            data-testid="private-chat-send-btn"
          >
            {sending ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Icon name="send" size={20} color="#fff" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm, borderBottomWidth: 1, borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  headerInfo: { flex: 1, flexDirection: 'row', alignItems: 'center', marginLeft: SPACING.sm },
  headerAvatar: {
    width: 36, height: 36, borderRadius: 18, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center',
  },
  headerAvatarText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  headerName: { fontSize: 16, fontWeight: '600', color: COLORS.text, marginLeft: SPACING.sm, flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  messagesList: { padding: SPACING.md, paddingBottom: SPACING.sm },
  messageBubble: { maxWidth: '78%', padding: SPACING.sm, borderRadius: BORDER_RADIUS.md, marginBottom: SPACING.xs },
  ownBubble: { alignSelf: 'flex-end', backgroundColor: COLORS.primary },
  otherBubble: { alignSelf: 'flex-start', backgroundColor: COLORS.card, borderWidth: 1, borderColor: COLORS.border },
  messageText: { fontSize: 15, color: COLORS.text, lineHeight: 20 },
  ownMessageText: { color: '#fff' },
  messageTime: { fontSize: 11, color: COLORS.textMuted, marginTop: 4, alignSelf: 'flex-end' },
  ownTimeText: { color: 'rgba(255,255,255,0.7)' },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 100 },
  emptyText: { color: COLORS.textMuted, marginTop: SPACING.sm, fontSize: 15 },
  inputBar: {
    flexDirection: 'row', alignItems: 'flex-end', padding: SPACING.sm,
    borderTopWidth: 1, borderTopColor: COLORS.border, backgroundColor: COLORS.card,
  },
  input: {
    flex: 1, backgroundColor: COLORS.background, borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm, fontSize: 15,
    color: COLORS.text, maxHeight: 100, borderWidth: 1, borderColor: COLORS.border,
  },
  sendButton: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: SPACING.xs,
  },
  sendButtonDisabled: { opacity: 0.5 },
  // Safety Modal Styles
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: SPACING.lg,
  },
  safetyModal: {
    backgroundColor: COLORS.card, borderRadius: BORDER_RADIUS.lg, padding: SPACING.xl,
    maxWidth: 400, width: '100%', alignItems: 'center', ...SHADOWS.large,
  },
  safetyIconContainer: {
    width: 80, height: 80, borderRadius: 40, backgroundColor: COLORS.primary + '15',
    justifyContent: 'center', alignItems: 'center', marginBottom: SPACING.md,
  },
  safetyTitle: {
    fontSize: 20, fontWeight: '700', color: COLORS.text, textAlign: 'center', marginBottom: SPACING.sm,
  },
  safetyMessage: {
    fontSize: 15, color: COLORS.textLight, textAlign: 'center', lineHeight: 22, marginBottom: SPACING.md,
  },
  safetyBullets: {
    alignSelf: 'stretch', backgroundColor: COLORS.background, borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md, marginBottom: SPACING.lg,
  },
  safetyBullet: { fontSize: 14, color: COLORS.text, marginBottom: SPACING.xs, lineHeight: 20 },
  safetyButton: {
    backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.md, paddingHorizontal: SPACING.xl, width: '100%',
  },
  safetyButtonText: { color: '#fff', fontSize: 16, fontWeight: '600', textAlign: 'center' },
  // Blocked Chat Styles
  blockedContainer: {
    flex: 1, justifyContent: 'center', alignItems: 'center', padding: SPACING.xl,
  },
  blockedTitle: {
    fontSize: 20, fontWeight: '700', color: COLORS.text, textAlign: 'center', marginTop: SPACING.lg, marginBottom: SPACING.sm,
  },
  blockedMessage: {
    fontSize: 15, color: COLORS.textLight, textAlign: 'center', lineHeight: 22, marginBottom: SPACING.lg,
  },
  addFriendButton: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.sm,
    backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.md, paddingHorizontal: SPACING.lg,
  },
  addFriendButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
