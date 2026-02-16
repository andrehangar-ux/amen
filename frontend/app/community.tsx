import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore, useTranslation } from '../src/store/languageStore';
import { useAuthStore } from '../src/store/authStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS, MOODS } from '../src/utils/theme';
import { format } from 'date-fns';

interface CommunityMessage {
  message_id: string;
  user_id: string;
  user_name: string;
  user_country: string | null;
  content: string;
  translated_content?: string;
  original_language: string;
  message_type: string;
  likes: number;
  created_at: string;
}

export default function CommunityScreen() {
  const { user } = useAuthStore();
  const { currentLanguage, languages } = useLanguageStore();
  const { t } = useTranslation();
  const [messages, setMessages] = useState<CommunityMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<Array<{user_id: string; user_name: string}>>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [showChats, setShowChats] = useState(false);

  const loadMessages = useCallback(async () => {
    try {
      const data = await api.getCommunityMessages(currentLanguage);
      setMessages(data);
    } catch (error) {
      console.log('Error loading messages:', error);
    }
  }, [currentLanguage]);

  const loadOnlineUsers = useCallback(async () => {
    try {
      const data = await api.getOnlineUsers();
      setOnlineUsers((data.users || []).filter((u: any) => u.user_id !== user?.user_id));
    } catch (error) {
      console.log('Error loading online users:', error);
    }
  }, [user?.user_id]);

  const loadConversations = useCallback(async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (error) {
      console.log('Error loading conversations:', error);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadMessages(), loadOnlineUsers(), loadConversations()]).finally(() => setLoading(false));
    // Heartbeat + periodic refresh
    api.sendHeartbeat().catch(() => {});
    const interval = setInterval(() => {
      api.sendHeartbeat().catch(() => {});
      loadOnlineUsers();
      loadConversations();
    }, 30000);
    return () => clearInterval(interval);
  }, [loadMessages, loadOnlineUsers, loadConversations]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMessages();
    setRefreshing(false);
  };

  const handleSend = async () => {
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      await api.createCommunityMessage(newMessage, currentLanguage);
      setNewMessage('');
      await loadMessages();
    } catch (error) {
      console.log('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleLike = async (messageId: string) => {
    try {
      await api.likeCommunityMessage(messageId);
      await loadMessages();
    } catch (error) {
      console.log('Error liking message:', error);
    }
  };

  const [translating, setTranslating] = useState<string | null>(null);
  const [translations, setTranslations] = useState<Record<string, string>>({});

  const translateMessage = async (message: CommunityMessage) => {
    if (translations[message.message_id] || message.original_language === currentLanguage) return;
    
    setTranslating(message.message_id);
    try {
      const response = await api.translate(message.content, message.original_language, currentLanguage);
      setTranslations(prev => ({
        ...prev,
        [message.message_id]: response.translated_text
      }));
    } catch (error) {
      console.log('Translation error:', error);
    } finally {
      setTranslating(null);
    }
  };

  const getFlag = (lang: string) => {
    return languages[lang]?.flag || '🌐';
  };

  const renderMessage = ({ item }: { item: CommunityMessage }) => {
    const isOwn = item.user_id === user?.user_id;
    const hasTranslation = translations[item.message_id] || item.translated_content;
    const showTranslation = hasTranslation && item.original_language !== currentLanguage;
    const translatedText = translations[item.message_id] || item.translated_content;
    const isTranslating = translating === item.message_id;
    const needsTranslation = item.original_language !== currentLanguage && !hasTranslation;

    return (
      <View style={[styles.messageCard, isOwn && styles.ownMessage]}>
        <View style={styles.messageHeader}>
          <View style={styles.userInfo}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{item.user_name.charAt(0).toUpperCase()}</Text>
            </View>
            <View>
              <Text style={styles.userName}>{item.user_name}</Text>
              <View style={styles.messageMeta}>
                <Text style={styles.flag}>{getFlag(item.original_language)}</Text>
                <Text style={styles.timeText}>
                  {format(new Date(item.created_at), 'HH:mm')}
                </Text>
              </View>
            </View>
          </View>
          {item.message_type === 'prayer_request' && (
            <View style={styles.prayerBadge}>
              <Icon name="hand-left" size={12} color={COLORS.accent} />
              <Text style={styles.prayerText}>{t('prayer')}</Text>
            </View>
          )}
        </View>

        <Text style={styles.messageContent}>
          {showTranslation ? translatedText : item.content}
        </Text>

        {showTranslation && (
          <View style={styles.originalContainer}>
            <Text style={styles.originalLabel}>{t('original')} ({getFlag(item.original_language)}):</Text>
            <Text style={styles.originalText}>{item.content}</Text>
          </View>
        )}

        {/* Translation Button */}
        {needsTranslation && (
          <TouchableOpacity 
            style={styles.translateButton}
            onPress={() => translateMessage(item)}
            disabled={isTranslating}
          >
            {isTranslating ? (
              <ActivityIndicator size="small" color={COLORS.primary} />
            ) : (
              <>
                <Icon name="language" size={14} color={COLORS.primary} />
                <Text style={styles.translateText}>{t('translate')}</Text>
              </>
            )}
          </TouchableOpacity>
        )}

        <View style={styles.messageActions}>
          <TouchableOpacity
            style={styles.likeButton}
            onPress={() => handleLike(item.message_id)}
          >
            <Icon name="heart-outline" size={18} color={COLORS.textLight} />
            <Text style={styles.likeCount}>{item.likes}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>{t('community')}</Text>
          <Text style={styles.headerSubtitle}>{t('connectWithBrothers')}</Text>
        </View>
        <View style={styles.languageBadge}>
          <Text style={styles.languageFlag}>{languages[currentLanguage]?.flag}</Text>
        </View>
      </View>

      {/* Online Users + Chat Toggle */}
      <View style={styles.onlineBar}>
        <TouchableOpacity
          style={[styles.tabBtn, !showChats && styles.tabBtnActive]}
          onPress={() => setShowChats(false)}
          data-testid="community-tab-messages"
        >
          <Icon name="chatbubbles-outline" size={18} color={!showChats ? '#fff' : COLORS.textLight} />
          <Text style={[styles.tabText, !showChats && styles.tabTextActive]}>{t('community')}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabBtn, showChats && styles.tabBtnActive]}
          onPress={() => { setShowChats(true); loadConversations(); }}
          data-testid="community-tab-chats"
        >
          <Icon name="mail-outline" size={18} color={showChats ? '#fff' : COLORS.textLight} />
          <Text style={[styles.tabText, showChats && styles.tabTextActive]}>Chat</Text>
          {conversations.some(c => c.unread_count > 0) && <View style={styles.unreadDot} />}
        </TouchableOpacity>
      </View>

      {/* Online Users Strip */}
      {onlineUsers.length > 0 && (
        <View style={styles.onlineStrip}>
          <Text style={styles.onlineLabel}>Online ({onlineUsers.length})</Text>
          <FlatList
            horizontal
            data={onlineUsers}
            showsHorizontalScrollIndicator={false}
            keyExtractor={(item) => item.user_id}
            contentContainerStyle={{ paddingHorizontal: 4 }}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.onlineUser}
                onPress={() => router.push({ pathname: '/private-chat', params: { userId: item.user_id, userName: item.user_name } })}
                data-testid={`online-user-${item.user_id}`}
              >
                <View style={styles.onlineAvatar}>
                  <Text style={styles.onlineAvatarText}>{item.user_name.charAt(0).toUpperCase()}</Text>
                  <View style={styles.onlineDot} />
                </View>
                <Text style={styles.onlineUserName} numberOfLines={1}>{item.user_name.split(' ')[0]}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      )}

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Messages or Chats List */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
        ) : showChats ? (
          <FlatList
            data={conversations}
            keyExtractor={(item) => item.conversation_id}
            contentContainerStyle={styles.listContent}
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="mail-outline" size={64} color={COLORS.textMuted} />
                <Text style={styles.emptyText}>Nessuna chat</Text>
                <Text style={styles.emptySubtext}>Tocca un utente online per iniziare</Text>
              </View>
            }
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.chatItem}
                onPress={() => router.push({ pathname: '/private-chat', params: { userId: item.other_user_id, userName: item.other_user_name } })}
                data-testid={`chat-item-${item.other_user_id}`}
              >
                <View style={styles.chatAvatar}>
                  <Text style={styles.chatAvatarText}>{item.other_user_name.charAt(0).toUpperCase()}</Text>
                </View>
                <View style={styles.chatInfo}>
                  <Text style={styles.chatName}>{item.other_user_name}</Text>
                  <Text style={styles.chatLastMsg} numberOfLines={1}>
                    {item.last_sender_name}: {item.last_message}
                  </Text>
                </View>
                {item.unread_count > 0 && (
                  <View style={styles.unreadBadge}>
                    <Text style={styles.unreadText}>{item.unread_count}</Text>
                  </View>
                )}
              </TouchableOpacity>
            )}
          />
        ) : (
          <FlatList
            data={messages}
            keyExtractor={(item) => item.message_id}
            renderItem={renderMessage}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="people-outline" size={64} color={COLORS.textMuted} />
                <Text style={styles.emptyText}>{t('noMessagesYet')}</Text>
                <Text style={styles.emptySubtext}>{t('beFirstToShare')}</Text>
              </View>
            }
          />
        )}

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={t('shareThought')}
            placeholderTextColor={COLORS.textMuted}
            value={newMessage}
            onChangeText={setNewMessage}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!newMessage.trim() || sending}
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
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerContent: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerSubtitle: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  languageBadge: {
    padding: SPACING.sm,
  },
  languageFlag: {
    fontSize: 24,
  },
  keyboardView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  messageCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  ownMessage: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  messageHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.sm,
  },
  avatarText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
  },
  userName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  messageMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  flag: {
    fontSize: 14,
  },
  timeText: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  prayerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent + '20',
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.full,
    gap: SPACING.xs,
  },
  prayerText: {
    fontSize: 11,
    color: COLORS.accent,
    fontWeight: '600',
  },
  messageContent: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 22,
  },
  originalContainer: {
    marginTop: SPACING.sm,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  originalLabel: {
    fontSize: 11,
    color: COLORS.textMuted,
    marginBottom: SPACING.xs,
  },
  originalText: {
    fontSize: 13,
    color: COLORS.textLight,
    fontStyle: 'italic',
  },
  messageActions: {
    flexDirection: 'row',
    marginTop: SPACING.sm,
    justifyContent: 'space-between',
  },
  likeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  likeCount: {
    fontSize: 13,
    color: COLORS.textLight,
  },
  translateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.sm,
    backgroundColor: COLORS.primary + '15',
    borderRadius: BORDER_RADIUS.sm,
    marginTop: SPACING.sm,
    alignSelf: 'flex-start',
    gap: SPACING.xs,
  },
  translateText: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  input: {
    flex: 1,
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 15,
    color: COLORS.text,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.textMuted,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textLight,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
});
