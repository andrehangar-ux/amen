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
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore, useTranslation } from '../src/store/languageStore';
import { useAuthStore } from '../src/store/authStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';
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

interface OnlineUser {
  user_id: string;
  user_name: string;
  last_seen: string;
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
  const [onlineUsers, setOnlineUsers] = useState<OnlineUser[]>([]);
  const [onlineCount, setOnlineCount] = useState(0);

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
      setOnlineUsers(data.users || []);
      setOnlineCount(data.online_count || 0);
    } catch (error) {
      console.log('Error loading online users:', error);
    }
  }, []);

  const sendHeartbeat = useCallback(async () => {
    try {
      await api.sendHeartbeat();
    } catch (error) {
      console.log('Heartbeat error:', error);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadMessages(), loadOnlineUsers()]).finally(() => setLoading(false));
    
    // Send heartbeat every 2 minutes to track online status
    sendHeartbeat();
    const heartbeatInterval = setInterval(sendHeartbeat, 120000);
    const onlineInterval = setInterval(loadOnlineUsers, 60000);
    
    return () => {
      clearInterval(heartbeatInterval);
      clearInterval(onlineInterval);
    };
  }, [loadMessages, loadOnlineUsers, sendHeartbeat]);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([loadMessages(), loadOnlineUsers()]);
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
        <View style={styles.onlineBadge}>
          <View style={styles.onlineDot} />
          <Text style={styles.onlineText}>{onlineCount}</Text>
        </View>
      </View>

      {/* Online Users Section */}
      {onlineUsers.length > 0 && (
        <View style={styles.onlineUsersContainer}>
          <View style={styles.onlineUsersHeader}>
            <Icon name="radio-button-on" size={12} color="#4CAF50" />
            <Text style={styles.onlineUsersTitle}>{t('onlineNow')}</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.onlineUsersScroll}>
            {onlineUsers.map((onlineUser) => (
              <View key={onlineUser.user_id} style={styles.onlineUserItem}>
                <View style={styles.onlineUserAvatar}>
                  <Text style={styles.onlineUserAvatarText}>{onlineUser.user_name.charAt(0).toUpperCase()}</Text>
                  <View style={styles.onlineIndicator} />
                </View>
                <Text style={styles.onlineUserName} numberOfLines={1}>
                  {onlineUser.user_name.split(' ')[0]}
                </Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Quick Actions Bar */}
      <View style={styles.quickActionsContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.quickActionsScroll}>
          <TouchableOpacity style={styles.quickAction} onPress={() => router.push('/bible')}>
            <View style={[styles.quickActionIcon, { backgroundColor: COLORS.primary + '20' }]}>
              <Icon name="book" size={20} color={COLORS.primary} />
            </View>
            <Text style={styles.quickActionText}>{t('readBible')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickAction} onPress={() => router.push('/quiz')}>
            <View style={[styles.quickActionIcon, { backgroundColor: '#4CAF50' + '20' }]}>
              <Icon name="help-circle" size={20} color="#4CAF50" />
            </View>
            <Text style={styles.quickActionText}>{t('quiz')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickAction} onPress={() => router.push('/journal')}>
            <View style={[styles.quickActionIcon, { backgroundColor: '#FF9800' + '20' }]}>
              <Icon name="create" size={20} color="#FF9800" />
            </View>
            <Text style={styles.quickActionText}>{t('journal')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickAction} onPress={() => router.push('/groups')}>
            <View style={[styles.quickActionIcon, { backgroundColor: '#9C27B0' + '20' }]}>
              <Icon name="people" size={20} color="#9C27B0" />
            </View>
            <Text style={styles.quickActionText}>{t('groups')}</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickAction} onPress={() => router.push('/dictionary')}>
            <View style={[styles.quickActionIcon, { backgroundColor: '#2196F3' + '20' }]}>
              <Icon name="library" size={20} color="#2196F3" />
            </View>
            <Text style={styles.quickActionText}>{t('dictionary')}</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Messages List */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
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
  quickActionsContainer: {
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingVertical: SPACING.sm,
  },
  quickActionsScroll: {
    paddingHorizontal: SPACING.md,
    gap: SPACING.md,
  },
  quickAction: {
    alignItems: 'center',
    width: 70,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  quickActionText: {
    fontSize: 11,
    color: COLORS.textLight,
    textAlign: 'center',
  },
});
