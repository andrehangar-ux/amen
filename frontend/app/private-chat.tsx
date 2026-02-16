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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router, useLocalSearchParams } from 'expo-router';
import { api } from '../src/utils/api';
import { useAuthStore } from '../src/store/authStore';
import { COLORS, SPACING, BORDER_RADIUS } from '../src/utils/theme';
import { format } from 'date-fns';

interface PrivateMessage {
  message_id: string;
  sender_id: string;
  sender_name: string;
  receiver_id: string;
  content: string;
  read: boolean;
  created_at: string;
}

export default function PrivateChatScreen() {
  const { userId, userName } = useLocalSearchParams<{ userId: string; userName: string }>();
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<PrivateMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const loadMessages = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await api.getPrivateMessages(userId);
      setMessages(data);
    } catch (error) {
      console.log('Error loading messages:', error);
    }
  }, [userId]);

  useEffect(() => {
    loadMessages().finally(() => setLoading(false));
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [loadMessages]);

  const handleSend = async () => {
    if (!newMessage.trim() || !userId) return;
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

      {loading ? (
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
});
