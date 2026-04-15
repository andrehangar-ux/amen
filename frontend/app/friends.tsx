import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
  TextInput,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface FriendUser {
  user_id: string;
  name: string;
  email?: string;
  is_online?: boolean;
  added_at?: string;
  bio?: string;
  country?: string;
}

// Stable avatar color from name
const AVATAR_PALETTE = [
  '#6B7F5B', '#D4A574', '#5B8FA8', '#A67F6B', '#7B6BA0',
  '#5BA08F', '#A0745B', '#6B8FA0', '#8F6B7F', '#5B9F6B',
  '#C4836B', '#6B7FA0', '#9F8B5B', '#7F5B8F', '#5BA07F',
];

const getAvatarColor = (name: string): string => {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_PALETTE[Math.abs(hash) % AVATAR_PALETTE.length];
};

const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.substring(0, 2).toUpperCase();
};

const translations: Record<string, Record<string, string>> = {
  it: {
    title: 'I Miei Amici',
    subtitle: 'Le tue persone fidate',
    noFriends: 'Nessun amico ancora',
    noFriendsDesc: 'Aggiungi amici per condividere il tuo cammino di fede insieme.',
    addFriendHint: 'Cerca e aggiungi nuovi amici',
    searchPlaceholder: 'Cerca per nome...',
    online: 'Online',
    offline: 'Offline',
    remove: 'Rimuovi',
    add: 'Aggiungi',
    added: 'Aggiunto',
    confirmRemove: 'Vuoi rimuovere questo amico dalla lista?',
    cancel: 'Annulla',
    message: 'Messaggio',
    addFriend: 'Aggiungi Amici',
    discoverPeople: 'Scopri Persone',
    myFriends: 'I Miei Amici',
    noResults: 'Nessun utente trovato',
    friendsCount: 'amici',
    onlineCount: 'online',
    startChatting: 'Invia messaggio',
    friendAdded: 'Amico aggiunto!',
  },
  en: {
    title: 'My Friends',
    subtitle: 'Your trusted people',
    noFriends: 'No friends yet',
    noFriendsDesc: 'Add friends to share your faith journey together.',
    addFriendHint: 'Search and add new friends',
    searchPlaceholder: 'Search by name...',
    online: 'Online',
    offline: 'Offline',
    remove: 'Remove',
    add: 'Add',
    added: 'Added',
    confirmRemove: 'Remove this friend from your list?',
    cancel: 'Cancel',
    message: 'Message',
    addFriend: 'Add Friends',
    discoverPeople: 'Discover People',
    myFriends: 'My Friends',
    noResults: 'No users found',
    friendsCount: 'friends',
    onlineCount: 'online',
    startChatting: 'Send message',
    friendAdded: 'Friend added!',
  },
  es: {
    title: 'Mis Amigos',
    subtitle: 'Tus personas de confianza',
    noFriends: 'Sin amigos aun',
    noFriendsDesc: 'Agrega amigos para compartir tu camino de fe juntos.',
    addFriendHint: 'Busca y agrega nuevos amigos',
    searchPlaceholder: 'Buscar por nombre...',
    online: 'En linea',
    offline: 'Desconectado',
    remove: 'Eliminar',
    add: 'Agregar',
    added: 'Agregado',
    confirmRemove: 'Eliminar este amigo de tu lista?',
    cancel: 'Cancelar',
    message: 'Mensaje',
    addFriend: 'Agregar Amigos',
    discoverPeople: 'Descubrir Personas',
    myFriends: 'Mis Amigos',
    noResults: 'No se encontraron usuarios',
    friendsCount: 'amigos',
    onlineCount: 'en linea',
    startChatting: 'Enviar mensaje',
    friendAdded: 'Amigo agregado!',
  },
  pt: {
    title: 'Meus Amigos',
    subtitle: 'Suas pessoas de confianca',
    noFriends: 'Nenhum amigo ainda',
    noFriendsDesc: 'Adicione amigos para compartilhar sua jornada de fe juntos.',
    addFriendHint: 'Pesquise e adicione novos amigos',
    searchPlaceholder: 'Pesquisar por nome...',
    online: 'Online',
    offline: 'Offline',
    remove: 'Remover',
    add: 'Adicionar',
    added: 'Adicionado',
    confirmRemove: 'Remover este amigo da sua lista?',
    cancel: 'Cancelar',
    message: 'Mensagem',
    addFriend: 'Adicionar Amigos',
    discoverPeople: 'Descobrir Pessoas',
    myFriends: 'Meus Amigos',
    noResults: 'Nenhum usuario encontrado',
    friendsCount: 'amigos',
    onlineCount: 'online',
    startChatting: 'Enviar mensagem',
    friendAdded: 'Amigo adicionado!',
  },
  fr: {
    title: 'Mes Amis',
    subtitle: 'Vos personnes de confiance',
    noFriends: 'Aucun ami encore',
    noFriendsDesc: 'Ajoutez des amis pour partager votre chemin de foi ensemble.',
    addFriendHint: 'Recherchez et ajoutez de nouveaux amis',
    searchPlaceholder: 'Rechercher par nom...',
    online: 'En ligne',
    offline: 'Hors ligne',
    remove: 'Supprimer',
    add: 'Ajouter',
    added: 'Ajoute',
    confirmRemove: 'Supprimer cet ami de votre liste?',
    cancel: 'Annuler',
    message: 'Message',
    addFriend: 'Ajouter des Amis',
    discoverPeople: 'Decouvrir des Personnes',
    myFriends: 'Mes Amis',
    noResults: 'Aucun utilisateur trouve',
    friendsCount: 'amis',
    onlineCount: 'en ligne',
    startChatting: 'Envoyer un message',
    friendAdded: 'Ami ajoute!',
  },
  de: {
    title: 'Meine Freunde',
    subtitle: 'Deine vertrauten Personen',
    noFriends: 'Noch keine Freunde',
    noFriendsDesc: 'Fugen Sie Freunde hinzu, um Ihren Glaubensweg gemeinsam zu teilen.',
    addFriendHint: 'Suchen und neue Freunde hinzufugen',
    searchPlaceholder: 'Nach Name suchen...',
    online: 'Online',
    offline: 'Offline',
    remove: 'Entfernen',
    add: 'Hinzufugen',
    added: 'Hinzugefugt',
    confirmRemove: 'Diesen Freund aus Ihrer Liste entfernen?',
    cancel: 'Abbrechen',
    message: 'Nachricht',
    addFriend: 'Freunde hinzufugen',
    discoverPeople: 'Personen entdecken',
    myFriends: 'Meine Freunde',
    noResults: 'Keine Benutzer gefunden',
    friendsCount: 'Freunde',
    onlineCount: 'online',
    startChatting: 'Nachricht senden',
    friendAdded: 'Freund hinzugefugt!',
  },
};

export default function FriendsScreen() {
  const { currentLanguage } = useLanguageStore();
  const [friends, setFriends] = useState<FriendUser[]>([]);
  const [allUsers, setAllUsers] = useState<FriendUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'friends' | 'discover'>('friends');
  const [addingUserId, setAddingUserId] = useState<string | null>(null);
  const [isMinor, setIsMinor] = useState(false);

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  const loadData = useCallback(async () => {
    try {
      const [friendsData, usersData, socialAccess] = await Promise.all([
        api.getFriends(),
        api.getCommunityUsers(),
        api.canUseSocialFeatures().catch(() => null),
      ]);
      setFriends(friendsData || []);
      setAllUsers(usersData || []);
      if (socialAccess?.is_minor) setIsMinor(true);
    } catch (error) {
      console.error('Error loading friends:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const removeFriend = (friendId: string, friendName: string) => {
    Alert.alert(
      t('remove'),
      t('confirmRemove'),
      [
        { text: t('cancel'), style: 'cancel' },
        {
          text: t('remove'),
          style: 'destructive',
          onPress: async () => {
            try {
              await api.removeFriend(friendId);
              setFriends(prev => prev.filter(f => f.user_id !== friendId));
            } catch (error) {
              console.error('Error removing friend:', error);
            }
          },
        },
      ]
    );
  };

  const addFriend = async (userId: string) => {
    setAddingUserId(userId);
    try {
      await api.addFriend(userId);
      const user = allUsers.find(u => u.user_id === userId);
      if (user) {
        setFriends(prev => [...prev, { ...user, added_at: new Date().toISOString() }]);
      }
    } catch (error: any) {
      Alert.alert('Errore', error.message || 'Impossibile aggiungere amico');
    } finally {
      setAddingUserId(null);
    }
  };

  const openChat = (userId: string, userName: string) => {
    router.push({ pathname: '/private-chat', params: { userId, userName } });
  };

  const friendIds = new Set(friends.map(f => f.user_id));
  const onlineCount = friends.filter(f => f.is_online).length;

  const filteredUsers = allUsers.filter(u =>
    !friendIds.has(u.user_id) &&
    u.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} data-testid="friends-screen">
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} data-testid="friends-back-btn">
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.title}>{t('title')}</Text>
          <Text style={styles.subtitle}>{t('subtitle')}</Text>
        </View>
      </View>

      {/* Stats Bar */}
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{friends.length}</Text>
          <Text style={styles.statLabel}>{t('friendsCount')}</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <View style={styles.onlineIndicator}>
            <View style={styles.onlinePulse} />
            <Text style={styles.statNumber}>{onlineCount}</Text>
          </View>
          <Text style={styles.statLabel}>{t('onlineCount')}</Text>
        </View>
      </View>

      {/* Tab Switch */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'friends' && styles.tabActive]}
          onPress={() => setActiveTab('friends')}
          data-testid="tab-friends"
        >
          <Icon name="people" size={18} color={activeTab === 'friends' ? '#fff' : COLORS.textLight} />
          <Text style={[styles.tabText, activeTab === 'friends' && styles.tabTextActive]}>
            {t('myFriends')}
          </Text>
        </TouchableOpacity>
        {/* Hide discover tab for minors */}
        {!isMinor && (
          <TouchableOpacity
            style={[styles.tab, activeTab === 'discover' && styles.tabActive]}
            onPress={() => setActiveTab('discover')}
            data-testid="tab-discover"
          >
            <Icon name="search" size={18} color={activeTab === 'discover' ? '#fff' : COLORS.textLight} />
            <Text style={[styles.tabText, activeTab === 'discover' && styles.tabTextActive]}>
              {t('discoverPeople')}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Search - only in discover tab */}
      {activeTab === 'discover' && !isMinor && (
        <View style={styles.searchContainer}>
          <Icon name="search" size={20} color={COLORS.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder={t('searchPlaceholder')}
            placeholderTextColor={COLORS.textMuted}
            value={searchQuery}
            onChangeText={setSearchQuery}
            data-testid="search-users-input"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Icon name="close-circle" size={20} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Content */}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />}
        showsVerticalScrollIndicator={false}
      >
        {activeTab === 'friends' ? (
          friends.length > 0 ? (
            <>
              {/* Online friends first */}
              {friends.filter(f => f.is_online).length > 0 && (
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionDot} />
                  <Text style={styles.sectionTitle}>{t('online')}</Text>
                </View>
              )}
              {friends
                .filter(f => f.is_online)
                .map(friend => (
                  <FriendCard
                    key={friend.user_id}
                    friend={friend}
                    onMessage={() => openChat(friend.user_id, friend.name)}
                    onRemove={() => removeFriend(friend.user_id, friend.name)}
                    t={t}
                  />
                ))}

              {/* Offline friends */}
              {friends.filter(f => !f.is_online).length > 0 && (
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>{t('offline')}</Text>
                </View>
              )}
              {friends
                .filter(f => !f.is_online)
                .map(friend => (
                  <FriendCard
                    key={friend.user_id}
                    friend={friend}
                    onMessage={() => openChat(friend.user_id, friend.name)}
                    onRemove={() => removeFriend(friend.user_id, friend.name)}
                    t={t}
                  />
                ))}
            </>
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconWrap}>
                <Icon name="people" size={48} color={COLORS.primary} />
              </View>
              <Text style={styles.emptyTitle}>{t('noFriends')}</Text>
              <Text style={styles.emptyDesc}>{t('noFriendsDesc')}</Text>
              {!isMinor && (
                <TouchableOpacity
                  style={styles.emptyActionBtn}
                  onPress={() => setActiveTab('discover')}
                  data-testid="empty-discover-btn"
                >
                  <Icon name="search" size={20} color="#fff" />
                  <Text style={styles.emptyActionText}>{t('discoverPeople')}</Text>
                </TouchableOpacity>
              )}
            </View>
          )
        ) : (
          // Discover tab
          filteredUsers.length > 0 ? (
            filteredUsers.map(user => (
              <DiscoverCard
                key={user.user_id}
                user={user}
                isFriend={friendIds.has(user.user_id)}
                isAdding={addingUserId === user.user_id}
                onAdd={() => addFriend(user.user_id)}
                t={t}
              />
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="search" size={48} color={COLORS.textMuted} />
              <Text style={styles.emptyTitle}>{t('noResults')}</Text>
            </View>
          )
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

// Friend Card Component
const FriendCard = ({ friend, onMessage, onRemove, t }: {
  friend: FriendUser;
  onMessage: () => void;
  onRemove: () => void;
  t: (key: string) => string;
}) => {
  const color = getAvatarColor(friend.name);

  return (
    <View style={styles.friendCard} data-testid={`friend-${friend.user_id}`}>
      <View style={styles.friendLeft}>
        <View style={[styles.avatar, { backgroundColor: color }]}>
          <Text style={styles.avatarText}>{getInitials(friend.name)}</Text>
          {friend.is_online && (
            <View style={styles.onlineBadge} />
          )}
        </View>
        <View style={styles.friendInfo}>
          <Text style={styles.friendName}>{friend.name}</Text>
          <Text style={[styles.friendStatus, friend.is_online && styles.friendStatusOnline]}>
            {friend.is_online ? t('online') : t('offline')}
          </Text>
        </View>
      </View>
      <View style={styles.friendActions}>
        <TouchableOpacity
          style={styles.chatBtn}
          onPress={onMessage}
          data-testid={`message-${friend.user_id}`}
        >
          <Icon name="chatbubble" size={18} color={COLORS.primary} />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.removeBtn}
          onPress={onRemove}
          data-testid={`remove-${friend.user_id}`}
        >
          <Icon name="close" size={16} color={COLORS.textMuted} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Discover Card Component
const DiscoverCard = ({ user, isFriend, isAdding, onAdd, t }: {
  user: FriendUser;
  isFriend: boolean;
  isAdding: boolean;
  onAdd: () => void;
  t: (key: string) => string;
}) => {
  const color = getAvatarColor(user.name);

  return (
    <View style={styles.discoverCard} data-testid={`user-${user.user_id}`}>
      <View style={styles.friendLeft}>
        <View style={[styles.avatar, { backgroundColor: color }]}>
          <Text style={styles.avatarText}>{getInitials(user.name)}</Text>
        </View>
        <View style={styles.friendInfo}>
          <Text style={styles.friendName}>{user.name}</Text>
        </View>
      </View>
      {isFriend ? (
        <View style={styles.addedBadge}>
          <Icon name="checkmark" size={16} color={COLORS.primary} />
          <Text style={styles.addedText}>{t('added')}</Text>
        </View>
      ) : (
        <TouchableOpacity
          style={styles.addBtn}
          onPress={onAdd}
          disabled={isAdding}
          data-testid={`add-${user.user_id}`}
        >
          {isAdding ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Icon name="person-add" size={16} color="#fff" />
              <Text style={styles.addBtnText}>{t('add')}</Text>
            </>
          )}
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  backBtn: {
    padding: SPACING.sm,
    marginRight: SPACING.sm,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  // Stats Bar
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.card,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: SPACING.xl,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: COLORS.border,
  },
  onlineIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  onlinePulse: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#4CAF50',
  },
  // Tab Switch
  tabContainer: {
    flexDirection: 'row',
    margin: SPACING.md,
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.lg,
    padding: 4,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.sm + 2,
    borderRadius: BORDER_RADIUS.md,
    gap: 6,
  },
  tabActive: {
    backgroundColor: COLORS.primary,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textLight,
  },
  tabTextActive: {
    color: '#fff',
  },
  // Search
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    marginHorizontal: SPACING.md,
    marginBottom: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    height: 46,
  },
  searchInput: {
    flex: 1,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.sm,
    fontSize: 15,
    color: COLORS.text,
  },
  // Content
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: SPACING.md,
    paddingBottom: 120,
  },
  // Section headers
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    marginTop: SPACING.sm,
    gap: 6,
  },
  sectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#4CAF50',
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.textLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  // Friend Card
  friendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  friendLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  avatarText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.5,
  },
  onlineBadge: {
    position: 'absolute',
    bottom: 1,
    right: 1,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#4CAF50',
    borderWidth: 2.5,
    borderColor: COLORS.card,
  },
  friendInfo: {
    marginLeft: SPACING.md,
    flex: 1,
  },
  friendName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  friendStatus: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  friendStatusOnline: {
    color: '#4CAF50',
    fontWeight: '500',
  },
  friendActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  chatBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Discover Card
  discoverCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
    gap: 6,
    minWidth: 100,
    justifyContent: 'center',
  },
  addBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  addedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
    gap: 4,
  },
  addedText: {
    color: COLORS.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  // Empty State
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl * 2,
    paddingHorizontal: SPACING.xl,
  },
  emptyIconWrap: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: COLORS.primary + '12',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  emptyDesc: {
    fontSize: 15,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.lg,
    maxWidth: 280,
  },
  emptyActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    borderRadius: BORDER_RADIUS.full,
    gap: SPACING.sm,
  },
  emptyActionText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
