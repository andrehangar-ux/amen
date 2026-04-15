import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router, useLocalSearchParams } from 'expo-router';
import { api } from '../src/utils/api';
import { useAuthStore } from '../src/store/authStore';
import { useTranslation } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';
import { format } from 'date-fns';

interface StudyGroup {
  group_id: string;
  name: string;
  description?: string;
  members: Array<{ user_id: string; user_name: string; role: string }>;
  current_study?: { book: string; chapter: number; verse_start: number; verse_end?: number };
  created_at: string;
}

interface GroupMessage {
  message_id: string;
  user_id: string;
  user_name: string;
  content: string;
  message_type: string;
  shared_content?: any;
  created_at: string;
}

interface Invite {
  invite_id: string;
  group_id: string;
  group_name: string;
  invited_by_name: string;
}

export default function StudyGroupsScreen() {
  const { user } = useAuthStore();
  const { t } = useTranslation();
  const params = useLocalSearchParams();
  const [groups, setGroups] = useState<StudyGroup[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<StudyGroup | null>(null);
  const [messages, setMessages] = useState<GroupMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ user_id: string; name: string }>>([]);
  const [searching, setSearching] = useState(false);
  const [blockedMinor, setBlockedMinor] = useState(false);

  const loadGroups = useCallback(async () => {
    try {
      const [groupsRes, invitesRes] = await Promise.all([
        api.getMyStudyGroups(),
        api.getPendingInvites()
      ]);
      setGroups(groupsRes.groups || []);
      setInvites(invitesRes.invites || []);
      setBlockedMinor(false);
    } catch (error: any) {
      if (error.message?.includes('minori')) {
        setBlockedMinor(true);
      }
      console.log('Error loading groups:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  useEffect(() => {
    if (params.groupId && groups.length > 0) {
      const group = groups.find(g => g.group_id === params.groupId);
      if (group) {
        setSelectedGroup(group);
        loadMessages(group.group_id);
      }
    }
  }, [params.groupId, groups]);

  const loadMessages = async (groupId: string) => {
    try {
      const res = await api.getGroupMessages(groupId);
      setMessages(res.messages || []);
    } catch (error) {
      console.log('Error loading messages:', error);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return;
    setCreating(true);
    try {
      const res = await api.createStudyGroup(newGroupName.trim(), newGroupDesc.trim() || undefined);
      if (res.success) {
        setShowCreateModal(false);
        setNewGroupName('');
        setNewGroupDesc('');
        loadGroups();
      }
    } catch (error: any) {
      alert(error.message || 'Errore nella creazione del gruppo');
    } finally {
      setCreating(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedGroup) return;
    setSending(true);
    try {
      await api.sendGroupMessage(selectedGroup.group_id, newMessage.trim());
      setNewMessage('');
      loadMessages(selectedGroup.group_id);
    } catch (error) {
      console.log('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleRespondInvite = async (inviteId: string, accept: boolean) => {
    try {
      await api.respondToInvite(inviteId, accept);
      loadGroups();
    } catch (error: any) {
      alert(error.message || 'Errore');
    }
  };

  const handleSearchUsers = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await api.searchUsersForInvite(query);
      setSearchResults(res.users || []);
    } catch (error) {
      console.log('Error searching users:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleInviteUser = async (userId: string) => {
    if (!selectedGroup) return;
    try {
      await api.inviteToStudyGroup(selectedGroup.group_id, userId);
      alert('Invito inviato!');
      setShowInviteModal(false);
      setSearchQuery('');
      setSearchResults([]);
    } catch (error: any) {
      alert(error.message || 'Errore nell\'invio dell\'invito');
    }
  };

  const handleLeaveGroup = async () => {
    if (!selectedGroup) return;
    try {
      await api.leaveStudyGroup(selectedGroup.group_id);
      setSelectedGroup(null);
      loadGroups();
    } catch (error: any) {
      alert(error.message || 'Errore');
    }
  };

  // Blocked for minors
  if (blockedMinor) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Icon name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('studyGroups') || 'Gruppi di Studio'}</Text>
        </View>
        <View style={styles.blockedContainer}>
          <Icon name="shield-checkmark" size={80} color={COLORS.primary} />
          <Text style={styles.blockedTitle}>
            {t('studyGroupsBlocked') || 'Gruppi di Studio Non Disponibili'}
          </Text>
          <Text style={styles.blockedMessage}>
            {t('minorsCantAccessGroups') || 'Per la tua sicurezza, i gruppi di studio richiedono che un genitore abiliti le funzionalita social tramite il Controllo Genitori nelle Impostazioni.'}
          </Text>
          <TouchableOpacity
            style={styles.goToSettingsBtn}
            onPress={() => router.push('/settings')}
            data-testid="study-groups-go-settings"
          >
            <Icon name="settings" size={20} color="#fff" />
            <Text style={styles.goToSettingsBtnText}>{t('goToSettings') || 'Vai alle Impostazioni'}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Group Chat View
  if (selectedGroup) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.groupHeader}>
          <TouchableOpacity style={styles.backButton} onPress={() => setSelectedGroup(null)}>
            <Icon name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <View style={styles.groupHeaderInfo}>
            <Text style={styles.groupHeaderTitle}>{selectedGroup.name}</Text>
            <Text style={styles.groupHeaderMembers}>
              {selectedGroup.members?.length || 0} {t('members') || 'membri'}
            </Text>
          </View>
          <TouchableOpacity style={styles.inviteButton} onPress={() => setShowInviteModal(true)}>
            <Icon name="person-add" size={22} color={COLORS.primary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.menuButton} onPress={handleLeaveGroup}>
            <Icon name="exit-outline" size={22} color={COLORS.error} />
          </TouchableOpacity>
        </View>

        {/* Current Study */}
        {selectedGroup.current_study && (
          <View style={styles.currentStudyBanner}>
            <Icon name="book" size={18} color={COLORS.primary} />
            <Text style={styles.currentStudyText}>
              {t('currentStudy') || 'Studio corrente'}: {selectedGroup.current_study.book} {selectedGroup.current_study.chapter}
              {selectedGroup.current_study.verse_start && `:${selectedGroup.current_study.verse_start}`}
              {selectedGroup.current_study.verse_end && `-${selectedGroup.current_study.verse_end}`}
            </Text>
          </View>
        )}

        {/* Messages */}
        <FlatList
          data={messages}
          keyExtractor={(item) => item.message_id}
          style={styles.messagesList}
          contentContainerStyle={styles.messagesContent}
          renderItem={({ item }) => (
            <View style={[
              styles.messageItem,
              item.user_id === user?.user_id && styles.myMessage
            ]}>
              {item.user_id !== user?.user_id && (
                <Text style={styles.messageSender}>{item.user_name}</Text>
              )}
              {item.message_type === 'verse_share' && item.shared_content && (
                <View style={styles.sharedVerse}>
                  <Icon name="bookmark" size={16} color={COLORS.primary} />
                  <Text style={styles.sharedVerseRef}>
                    {item.shared_content.book} {item.shared_content.chapter}:{item.shared_content.verse}
                  </Text>
                  <Text style={styles.sharedVerseText}>{item.shared_content.text}</Text>
                  {item.shared_content.note && (
                    <Text style={styles.sharedVerseNote}>{item.shared_content.note}</Text>
                  )}
                </View>
              )}
              {item.message_type === 'study_update' && (
                <View style={styles.studyUpdateMessage}>
                  <Icon name="book-outline" size={16} color={COLORS.primary} />
                  <Text style={styles.studyUpdateText}>{item.content}</Text>
                </View>
              )}
              {item.message_type === 'chat' && (
                <Text style={styles.messageText}>{item.content}</Text>
              )}
              <Text style={styles.messageTime}>
                {format(new Date(item.created_at), 'HH:mm')}
              </Text>
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyMessages}>
              <Icon name="chatbubbles-outline" size={48} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>{t('noMessages') || 'Nessun messaggio'}</Text>
            </View>
          }
        />

        {/* Input */}
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.messageInput}
              value={newMessage}
              onChangeText={setNewMessage}
              placeholder={t('typeMessage') || 'Scrivi un messaggio...'}
              placeholderTextColor={COLORS.textMuted}
              multiline
            />
            <TouchableOpacity
              style={[styles.sendButton, !newMessage.trim() && styles.sendButtonDisabled]}
              onPress={handleSendMessage}
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

        {/* Invite Modal */}
        <Modal visible={showInviteModal} transparent animationType="fade">
          <View style={styles.modalOverlay}>
            <View style={styles.modal}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>{t('inviteMember') || 'Invita Membro'}</Text>
                <TouchableOpacity onPress={() => setShowInviteModal(false)}>
                  <Icon name="close" size={24} color={COLORS.text} />
                </TouchableOpacity>
              </View>
              <TextInput
                style={styles.searchInput}
                value={searchQuery}
                onChangeText={handleSearchUsers}
                placeholder={t('searchUsers') || 'Cerca utenti...'}
                placeholderTextColor={COLORS.textMuted}
              />
              {searching ? (
                <ActivityIndicator style={styles.searchingIndicator} />
              ) : (
                <FlatList
                  data={searchResults}
                  keyExtractor={(item) => item.user_id}
                  style={styles.searchResultsList}
                  renderItem={({ item }) => (
                    <TouchableOpacity
                      style={styles.searchResultItem}
                      onPress={() => handleInviteUser(item.user_id)}
                    >
                      <Icon name="person" size={20} color={COLORS.primary} />
                      <Text style={styles.searchResultName}>{item.name}</Text>
                      <Icon name="add-circle" size={24} color={COLORS.primary} />
                    </TouchableOpacity>
                  )}
                  ListEmptyComponent={
                    searchQuery.length >= 2 ? (
                      <Text style={styles.noResultsText}>{t('noUsersFound') || 'Nessun utente trovato'}</Text>
                    ) : null
                  }
                />
              )}
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    );
  }

  // Groups List View
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('studyGroups') || 'Gruppi di Studio'}</Text>
        <TouchableOpacity style={styles.createButton} onPress={() => setShowCreateModal(true)}>
          <Icon name="add" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <ScrollView
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadGroups(); }} />
          }
          contentContainerStyle={styles.scrollContent}
        >
          {/* Pending Invites */}
          {invites.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>{t('pendingInvites') || 'Inviti Pendenti'}</Text>
              {invites.map((invite) => (
                <View key={invite.invite_id} style={styles.inviteCard}>
                  <View style={styles.inviteInfo}>
                    <Text style={styles.inviteGroupName}>{invite.group_name}</Text>
                    <Text style={styles.inviteBy}>
                      {t('invitedBy') || 'Invitato da'} {invite.invited_by_name}
                    </Text>
                  </View>
                  <View style={styles.inviteActions}>
                    <TouchableOpacity
                      style={styles.acceptButton}
                      onPress={() => handleRespondInvite(invite.invite_id, true)}
                    >
                      <Icon name="checkmark" size={20} color="#fff" />
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.declineButton}
                      onPress={() => handleRespondInvite(invite.invite_id, false)}
                    >
                      <Icon name="close" size={20} color="#fff" />
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* My Groups */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('myGroups') || 'I Miei Gruppi'}</Text>
            {groups.length === 0 ? (
              <View style={styles.emptyGroups}>
                <Icon name="people-outline" size={64} color={COLORS.textMuted} />
                <Text style={styles.emptyTitle}>{t('noGroups') || 'Nessun gruppo'}</Text>
                <Text style={styles.emptySubtext}>
                  {t('createFirstGroup') || 'Crea il tuo primo gruppo di studio biblico'}
                </Text>
                <TouchableOpacity style={styles.createFirstButton} onPress={() => setShowCreateModal(true)}>
                  <Icon name="add" size={20} color="#fff" />
                  <Text style={styles.createFirstButtonText}>{t('createGroup') || 'Crea Gruppo'}</Text>
                </TouchableOpacity>
              </View>
            ) : (
              groups.map((group) => (
                <TouchableOpacity
                  key={group.group_id}
                  style={styles.groupCard}
                  onPress={() => { setSelectedGroup(group); loadMessages(group.group_id); }}
                >
                  <View style={styles.groupIcon}>
                    <Icon name="people" size={28} color={COLORS.primary} />
                  </View>
                  <View style={styles.groupInfo}>
                    <Text style={styles.groupName}>{group.name}</Text>
                    {group.description && (
                      <Text style={styles.groupDesc} numberOfLines={1}>{group.description}</Text>
                    )}
                    <Text style={styles.groupMembers}>
                      {group.members?.length || 0} {t('members') || 'membri'}
                    </Text>
                  </View>
                  <Icon name="chevron-forward" size={24} color={COLORS.textMuted} />
                </TouchableOpacity>
              ))
            )}
          </View>
        </ScrollView>
      )}

      {/* Create Group Modal */}
      <Modal visible={showCreateModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{t('createGroup') || 'Crea Gruppo'}</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Icon name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            <TextInput
              style={styles.input}
              value={newGroupName}
              onChangeText={setNewGroupName}
              placeholder={t('groupName') || 'Nome del gruppo'}
              placeholderTextColor={COLORS.textMuted}
            />
            <TextInput
              style={[styles.input, styles.textArea]}
              value={newGroupDesc}
              onChangeText={setNewGroupDesc}
              placeholder={t('groupDescription') || 'Descrizione (opzionale)'}
              placeholderTextColor={COLORS.textMuted}
              multiline
              numberOfLines={3}
            />
            <TouchableOpacity
              style={[styles.createGroupButton, !newGroupName.trim() && styles.createGroupButtonDisabled]}
              onPress={handleCreateGroup}
              disabled={!newGroupName.trim() || creating}
            >
              {creating ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Icon name="add-circle" size={20} color="#fff" />
                  <Text style={styles.createGroupButtonText}>{t('create') || 'Crea'}</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  createButton: {
    padding: SPACING.sm,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    padding: SPACING.md,
  },
  section: {
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  inviteCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  inviteInfo: {
    flex: 1,
  },
  inviteGroupName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  inviteBy: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  inviteActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  acceptButton: {
    backgroundColor: COLORS.success,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
  },
  declineButton: {
    backgroundColor: COLORS.error,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
  },
  groupCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  groupIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  groupInfo: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  groupName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  groupDesc: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  groupMembers: {
    fontSize: 12,
    color: COLORS.primary,
    marginTop: 4,
  },
  emptyGroups: {
    alignItems: 'center',
    paddingVertical: SPACING.xxl,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  createFirstButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.lg,
    gap: SPACING.sm,
  },
  createFirstButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.lg,
  },
  modal: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  input: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  createGroupButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
  },
  createGroupButtonDisabled: {
    opacity: 0.5,
  },
  createGroupButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Group Chat Styles
  groupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  groupHeaderInfo: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  groupHeaderTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  groupHeaderMembers: {
    fontSize: 13,
    color: COLORS.textMuted,
  },
  inviteButton: {
    padding: SPACING.sm,
  },
  menuButton: {
    padding: SPACING.sm,
  },
  currentStudyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    padding: SPACING.sm,
    gap: SPACING.sm,
  },
  currentStudyText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '500',
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: SPACING.md,
  },
  messageItem: {
    backgroundColor: COLORS.card,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    maxWidth: '80%',
    alignSelf: 'flex-start',
  },
  myMessage: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.primary + '20',
  },
  messageSender: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  messageText: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 20,
  },
  messageTime: {
    fontSize: 11,
    color: COLORS.textMuted,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  sharedVerse: {
    backgroundColor: COLORS.background,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  sharedVerseRef: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
    marginLeft: SPACING.sm,
  },
  sharedVerseText: {
    fontSize: 14,
    color: COLORS.text,
    marginTop: 4,
    fontStyle: 'italic',
  },
  sharedVerseNote: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 4,
  },
  studyUpdateMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  studyUpdateText: {
    fontSize: 14,
    color: COLORS.primary,
    fontStyle: 'italic',
  },
  emptyMessages: {
    alignItems: 'center',
    paddingVertical: SPACING.xxl,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: SPACING.md,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  messageInput: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 15,
    color: COLORS.text,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: COLORS.primary,
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  searchInput: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  searchingIndicator: {
    marginVertical: SPACING.lg,
  },
  searchResultsList: {
    maxHeight: 300,
  },
  searchResultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: SPACING.md,
  },
  searchResultName: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  noResultsText: {
    textAlign: 'center',
    color: COLORS.textMuted,
    padding: SPACING.lg,
  },
  // Blocked
  blockedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  blockedTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    marginTop: SPACING.lg,
  },
  blockedMessage: {
    fontSize: 15,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: SPACING.md,
    maxWidth: 300,
    marginBottom: SPACING.xl,
    lineHeight: 22,
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
});
