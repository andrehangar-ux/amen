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
  Modal,
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

interface SocialAccess {
  can_use_social: boolean;
  social_level: string;
  media_sharing: boolean;
  reason: string;
  message?: string;
  is_minor?: boolean;
  parent_pin_set?: boolean;
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
  const [allUsers, setAllUsers] = useState<Array<{user_id: string; name: string; is_online: boolean}>>([]);
  const [showChats, setShowChats] = useState(false);
  const [socialAccess, setSocialAccess] = useState<SocialAccess | null>(null);
  const [showSafetyReminder, setShowSafetyReminder] = useState(false);
  const [safetyAcknowledged, setSafetyAcknowledged] = useState(false);

  // Check social access permissions
  const checkSocialAccess = useCallback(async () => {
    try {
      const access = await api.canUseSocialFeatures();
      setSocialAccess(access);
      
      // MINORS: Always show safety reminder every session before allowing social
      if (access.can_use_social && access.is_minor) {
        setShowSafetyReminder(true);
      } else if (!access.is_minor) {
        // Adults: no reminder needed
        setSafetyAcknowledged(true);
      }
      // If can_use_social is false, the blocked screen handles it
    } catch (error) {
      console.log('Error checking social access:', error);
      setSocialAccess({ can_use_social: false, social_level: 'disabled', media_sharing: false, reason: 'error', message: 'Errore nel verificare l\'accesso. Riprova.' });
    }
  }, []);

  useEffect(() => {
    checkSocialAccess();
  }, [checkSocialAccess]);

  const handleAcknowledgeSafety = async () => {
    try {
      await api.acknowledgeSafetyReminder();
    } catch (error) {
      console.log('Error acknowledging:', error);
    }
    setShowSafetyReminder(false);
    setSafetyAcknowledged(true);
  };

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

  const loadAllUsers = useCallback(async () => {
    try {
      const data = await api.getCommunityUsers();
      setAllUsers(data);
    } catch (error) {
      console.log('Error loading all users:', error);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadMessages(), loadOnlineUsers(), loadConversations(), loadAllUsers()]).finally(() => setLoading(false));
    // Heartbeat + periodic refresh
    api.sendHeartbeat().catch(() => {});
    const interval = setInterval(() => {
      api.sendHeartbeat().catch(() => {});
      loadOnlineUsers();
      loadConversations();
    }, 30000);
    return () => clearInterval(interval);
  }, [loadMessages, loadOnlineUsers, loadConversations, loadAllUsers]);

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
          <TouchableOpacity
            style={styles.userInfo}
            onPress={() => !isOwn && router.push({ pathname: '/private-chat', params: { userId: item.user_id, userName: item.user_name } })}
            disabled={isOwn}
          >
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
          </TouchableOpacity>
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
      {/* Safety Reminder Modal - Shown BEFORE allowing any social interaction */}
      <Modal
        visible={showSafetyReminder}
        transparent
        animationType="fade"
        onRequestClose={() => {}}
      >
        <View style={styles.safetyModalOverlay}>
          <View style={styles.safetyModal}>
            <View style={styles.safetyIconContainer}>
              <Icon name="shield-checkmark" size={56} color="#E74C3C" />
            </View>
            <Text style={styles.safetyTitle}>
              {t('safetyReminderTitle') || 'Avviso di Sicurezza Online'}
            </Text>
            <Text style={styles.safetyMessage}>
              {t('safetyReminderMessage') || 'IMPORTANTE: Interagire online comporta rischi reali. Prima di continuare, leggi attentamente:'}
            </Text>
            <View style={styles.safetyBullets}>
              <View style={styles.safetyBulletItem}>
                <Icon name="warning" size={20} color="#E74C3C" />
                <Text style={styles.safetyBulletText}>
                  {t('realWorldRisks') || 'Le interazioni online possono avere conseguenze reali. Non tutti sono chi dicono di essere.'}
                </Text>
              </View>
              <View style={styles.safetyBulletItem}>
                <Icon name="close-circle" size={20} color="#E74C3C" />
                <Text style={styles.safetyBulletText}>
                  {t('neverSharePersonalInfo') || 'NON condividere MAI: indirizzo, scuola, telefono, foto personali o posizione.'}
                </Text>
              </View>
              <View style={styles.safetyBulletItem}>
                <Icon name="people" size={20} color={COLORS.primary} />
                <Text style={styles.safetyBulletText}>
                  {t('chatOnlyWithKnown') || 'Chatta SOLO con persone che conosci nella vita reale e di cui ti fidi.'}
                </Text>
              </View>
              <View style={styles.safetyBulletItem}>
                <Icon name="hand-left" size={20} color="#F39C12" />
                <Text style={styles.safetyBulletText}>
                  {t('tellAdultIfUncomfortable') || 'Se qualcuno ti fa sentire a disagio o ti chiede informazioni personali, FERMATI e parlane subito con un genitore o un adulto di fiducia.'}
                </Text>
              </View>
              <View style={styles.safetyBulletItem}>
                <Icon name="eye-off" size={20} color="#9B59B6" />
                <Text style={styles.safetyBulletText}>
                  {t('beCarefulWithStrangers') || 'Non incontrare MAI di persona qualcuno conosciuto online senza un adulto.'}
                </Text>
              </View>
            </View>
            <Text style={styles.safetyParentNote}>
              {t('parentApprovedAccess') || 'L\'accesso a questa sezione e stato approvato da un genitore tramite il Controllo Genitori nelle Impostazioni.'}
            </Text>
            <TouchableOpacity 
              style={styles.safetyAcknowledgeBtn} 
              onPress={handleAcknowledgeSafety}
              data-testid="safety-acknowledge-btn"
            >
              <Icon name="checkmark-circle" size={24} color="#fff" />
              <Text style={styles.safetyAcknowledgeBtnText}>
                {t('iUnderstandAndAccept') || 'Ho letto e capisco i rischi'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Social Features Blocked Screen */}
      {socialAccess && !socialAccess.can_use_social ? (
        <View style={styles.blockedContainer}>
          <Icon name="shield-checkmark" size={80} color={COLORS.primary} />
          <Text style={styles.blockedTitle}>
            {socialAccess.reason === 'no_parent_pin'
              ? (t('parentSetupRequired') || 'Configurazione Genitore Richiesta')
              : (t('socialFeaturesDisabled') || 'Funzionalita Social Disabilitate')}
          </Text>
          <Text style={styles.blockedMessage}>
            {socialAccess.reason === 'no_parent_pin'
              ? (t('parentMustSetupPin') || 'Per la tua sicurezza, un genitore o tutore deve prima configurare un PIN di Controllo Genitori nelle Impostazioni e abilitare le funzionalita social.')
              : (socialAccess.message || t('parentalControlsBlockedSocial') || 'Il controllo genitori ha disabilitato le funzionalita social per questo account. Chiedi a un genitore di modificare le impostazioni.')}
          </Text>
          <View style={styles.blockedInfoBox}>
            <Icon name="information-circle" size={20} color={COLORS.primary} />
            <Text style={styles.blockedInfoText}>
              {t('adultRequiredInfo') || 'Solo un adulto puo abilitare o disabilitare le funzionalita social tramite il PIN di Controllo Genitori.'}
            </Text>
          </View>
          <TouchableOpacity 
            style={styles.goToSettingsBtn}
            onPress={() => router.push('/settings')}
            data-testid="go-to-settings-btn"
          >
            <Icon name="settings" size={20} color="#fff" />
            <Text style={styles.goToSettingsBtnText}>
              {t('goToSettings') || 'Vai alle Impostazioni'}
            </Text>
          </TouchableOpacity>
        </View>
      ) : !safetyAcknowledged ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>{t('checkingAccess') || 'Verifica accesso...'}</Text>
        </View>
      ) : (
        <>
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

      {/* Online Users Strip - hidden for minors in friends_only mode */}
      {(!socialAccess?.is_minor || socialAccess?.social_level !== 'friends_only') && (
      <View style={styles.onlineStrip}>
        <Text style={styles.onlineLabel}>
          Online ({onlineUsers.length})
        </Text>
        {onlineUsers.length > 0 ? (
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
        ) : (
          <Text style={styles.onlineEmpty}>Nessun utente online al momento</Text>
        )}
      </View>
      )}

      {/* Minors: friends_only info banner */}
      {socialAccess?.is_minor && socialAccess?.social_level === 'friends_only' && (
        <View style={styles.friendsOnlyBanner}>
          <Icon name="shield-checkmark" size={16} color={COLORS.primary} />
          <Text style={styles.friendsOnlyBannerText}>
            {t('friendsOnlyMode') || 'Modalita protetta: puoi chattare solo con i tuoi amici.'}
          </Text>
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
            data={[
              ...conversations.map(c => ({ type: 'conversation' as const, ...c })),
              ...(socialAccess?.is_minor && socialAccess?.social_level === 'friends_only' ? [] : allUsers
                .filter(u => !conversations.some(c => c.other_user_id === u.user_id))
                .map(u => ({ type: 'user' as const, ...u })))
            ]}
            keyExtractor={(item) => item.type === 'conversation' ? item.conversation_id : item.user_id}
            contentContainerStyle={styles.listContent}
            ListHeaderComponent={
              conversations.length > 0 ? (
                <Text style={styles.sectionTitle}>Conversazioni</Text>
              ) : null
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="people-outline" size={64} color={COLORS.textMuted} />
                <Text style={styles.emptyText}>Nessun utente registrato</Text>
              </View>
            }
            renderItem={({ item, index }) => {
              if (item.type === 'conversation') {
                const c = item as any;
                return (
                  <TouchableOpacity
                    style={styles.chatItem}
                    onPress={() => router.push({ pathname: '/private-chat', params: { userId: c.other_user_id, userName: c.other_user_name } })}
                    data-testid={`chat-item-${c.other_user_id}`}
                  >
                    <View style={styles.chatAvatar}>
                      <Text style={styles.chatAvatarText}>{c.other_user_name.charAt(0).toUpperCase()}</Text>
                    </View>
                    <View style={styles.chatInfo}>
                      <Text style={styles.chatName}>{c.other_user_name}</Text>
                      <Text style={styles.chatLastMsg} numberOfLines={1}>
                        {c.last_sender_name}: {c.last_message}
                      </Text>
                    </View>
                    {c.unread_count > 0 && (
                      <View style={styles.unreadBadge}>
                        <Text style={styles.unreadText}>{c.unread_count}</Text>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              } else {
                const u = item as any;
                const isFirstUser = index === conversations.length;
                return (
                  <>
                    {isFirstUser && (
                      <Text style={[styles.sectionTitle, { marginTop: conversations.length > 0 ? 16 : 0 }]}>Tutti gli utenti</Text>
                    )}
                    <TouchableOpacity
                      style={styles.chatItem}
                      onPress={() => router.push({ pathname: '/private-chat', params: { userId: u.user_id, userName: u.name } })}
                      data-testid={`user-item-${u.user_id}`}
                    >
                      <View style={[styles.chatAvatar, !u.is_online && { backgroundColor: COLORS.textMuted }]}>
                        <Text style={styles.chatAvatarText}>{u.name.charAt(0).toUpperCase()}</Text>
                        {u.is_online && <View style={styles.userOnlineDot} />}
                      </View>
                      <View style={styles.chatInfo}>
                        <Text style={styles.chatName}>{u.name}</Text>
                        <Text style={styles.chatLastMsg}>{u.is_online ? 'Online' : 'Offline'}</Text>
                      </View>
                      <Icon name="chatbubble-outline" size={20} color={COLORS.primary} />
                    </TouchableOpacity>
                  </>
                );
              }
            }}
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

        {/* Input Area - only show for community messages tab */}
        {!showChats && (
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
        )}
      </KeyboardAvoidingView>
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm, borderBottomWidth: 1, borderBottomColor: COLORS.border, backgroundColor: COLORS.card,
  },
  // Online bar & tabs
  onlineBar: {
    flexDirection: 'row', backgroundColor: COLORS.card, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  tabBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingVertical: SPACING.sm, gap: 6,
  },
  tabBtnActive: { backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.sm, margin: 4 },
  tabText: { fontSize: 13, fontWeight: '600', color: COLORS.textLight },
  tabTextActive: { color: '#fff' },
  unreadDot: {
    width: 8, height: 8, borderRadius: 4, backgroundColor: '#EF4444', position: 'absolute', top: 6, right: '30%',
  },
  // Online strip
  onlineStrip: {
    backgroundColor: COLORS.card, paddingVertical: SPACING.xs, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  onlineLabel: { fontSize: 11, fontWeight: '600', color: COLORS.primary, paddingHorizontal: SPACING.md, marginBottom: 4 },
  onlineUser: { alignItems: 'center', width: 60, paddingVertical: 4 },
  onlineAvatar: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: COLORS.primary + '20',
    justifyContent: 'center', alignItems: 'center',
  },
  onlineAvatarText: { fontSize: 16, fontWeight: '600', color: COLORS.primary },
  onlineDot: {
    width: 10, height: 10, borderRadius: 5, backgroundColor: '#22C55E',
    position: 'absolute', bottom: 0, right: 0, borderWidth: 2, borderColor: COLORS.card,
  },
  onlineUserName: { fontSize: 10, color: COLORS.textLight, marginTop: 2, textAlign: 'center' },
  onlineEmpty: { fontSize: 12, color: COLORS.textMuted, paddingHorizontal: SPACING.md, paddingBottom: 8 },
  // Section title
  sectionTitle: { fontSize: 13, fontWeight: '700', color: COLORS.primary, paddingHorizontal: SPACING.md, paddingVertical: 8, textTransform: 'uppercase' },
  // Chat list items
  chatItem: {
    flexDirection: 'row', alignItems: 'center', padding: SPACING.md,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  chatAvatar: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center',
  },
  chatAvatarText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  chatInfo: { flex: 1, marginLeft: SPACING.sm },
  chatName: { fontSize: 15, fontWeight: '600', color: COLORS.text },
  chatLastMsg: { fontSize: 13, color: COLORS.textLight, marginTop: 2 },
  unreadBadge: {
    minWidth: 22, height: 22, borderRadius: 11, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center', paddingHorizontal: 6,
  },
  unreadText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  userOnlineDot: {
    width: 12, height: 12, borderRadius: 6, backgroundColor: '#22C55E',
    position: 'absolute', bottom: -1, right: -1, borderWidth: 2, borderColor: COLORS.card,
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
  // Safety and Parental Controls Styles
  safetyModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.lg,
  },
  safetyModal: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.xl,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  safetyIconContainer: {
    marginBottom: SPACING.md,
  },
  safetyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  safetyMessage: {
    fontSize: 15,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginBottom: SPACING.lg,
    lineHeight: 22,
  },
  safetyBullets: {
    width: '100%',
    gap: SPACING.md,
    marginBottom: SPACING.xl,
  },
  safetyBulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
  },
  safetyBulletText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  safetyAcknowledgeBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
    width: '100%',
  },
  safetyAcknowledgeBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  blockedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
    backgroundColor: COLORS.background,
  },
  blockedTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
  },
  blockedMessage: {
    fontSize: 15,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginBottom: SPACING.xl,
    lineHeight: 22,
    maxWidth: 300,
  },
  goToSettingsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
  },
  goToSettingsBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  blockedInfoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.primary + '12',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.xl,
    maxWidth: 320,
    gap: SPACING.sm,
  },
  blockedInfoText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.primary,
    lineHeight: 19,
  },
  safetyParentNote: {
    fontSize: 12,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginBottom: SPACING.md,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  friendsOnlyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    gap: SPACING.sm,
  },
  friendsOnlyBannerText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '600',
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: 14,
    color: COLORS.textMuted,
  },
});
