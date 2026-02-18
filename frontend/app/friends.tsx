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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface User {
  user_id: string;
  name: string;
  email: string;
  is_online?: boolean;
  added_at?: string;
}

export default function FriendsScreen() {
  const { currentLanguage } = useLanguageStore();
  const [friends, setFriends] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddFriend, setShowAddFriend] = useState(false);

  const translations: Record<string, Record<string, string>> = {
    it: {
      title: 'I Miei Amici',
      subtitle: 'Utenti preferiti',
      noFriends: 'Nessun amico aggiunto',
      addFriendHint: 'Tocca + per aggiungere amici',
      searchPlaceholder: 'Cerca utenti...',
      online: 'Online',
      offline: 'Offline',
      remove: 'Rimuovi',
      add: 'Aggiungi',
      confirmRemove: 'Rimuovere questo amico?',
      cancel: 'Annulla',
      message: 'Messaggio',
      addFriend: 'Aggiungi Amico',
      allUsers: 'Tutti gli Utenti',
      back: 'Indietro',
    },
    en: {
      title: 'My Friends',
      subtitle: 'Favorite users',
      noFriends: 'No friends added',
      addFriendHint: 'Tap + to add friends',
      searchPlaceholder: 'Search users...',
      online: 'Online',
      offline: 'Offline',
      remove: 'Remove',
      add: 'Add',
      confirmRemove: 'Remove this friend?',
      cancel: 'Cancel',
      message: 'Message',
      addFriend: 'Add Friend',
      allUsers: 'All Users',
      back: 'Back',
    },
    es: {
      title: 'Mis Amigos',
      subtitle: 'Usuarios favoritos',
      noFriends: 'No hay amigos agregados',
      addFriendHint: 'Toca + para agregar amigos',
      searchPlaceholder: 'Buscar usuarios...',
      online: 'En línea',
      offline: 'Desconectado',
      remove: 'Eliminar',
      add: 'Agregar',
      confirmRemove: '¿Eliminar este amigo?',
      cancel: 'Cancelar',
      message: 'Mensaje',
      addFriend: 'Agregar Amigo',
      allUsers: 'Todos los Usuarios',
      back: 'Atrás',
    },
    pt: {
      title: 'Meus Amigos',
      subtitle: 'Usuários favoritos',
      noFriends: 'Nenhum amigo adicionado',
      addFriendHint: 'Toque em + para adicionar amigos',
      searchPlaceholder: 'Pesquisar usuários...',
      online: 'Online',
      offline: 'Offline',
      remove: 'Remover',
      add: 'Adicionar',
      confirmRemove: 'Remover este amigo?',
      cancel: 'Cancelar',
      message: 'Mensagem',
      addFriend: 'Adicionar Amigo',
      allUsers: 'Todos os Usuários',
      back: 'Voltar',
    },
    fr: {
      title: 'Mes Amis',
      subtitle: 'Utilisateurs favoris',
      noFriends: 'Aucun ami ajouté',
      addFriendHint: 'Appuyez sur + pour ajouter des amis',
      searchPlaceholder: 'Rechercher des utilisateurs...',
      online: 'En ligne',
      offline: 'Hors ligne',
      remove: 'Supprimer',
      add: 'Ajouter',
      confirmRemove: 'Supprimer cet ami?',
      cancel: 'Annuler',
      message: 'Message',
      addFriend: 'Ajouter un Ami',
      allUsers: 'Tous les Utilisateurs',
      back: 'Retour',
    },
    de: {
      title: 'Meine Freunde',
      subtitle: 'Lieblingsbenutzer',
      noFriends: 'Keine Freunde hinzugefügt',
      addFriendHint: 'Tippen Sie auf +, um Freunde hinzuzufügen',
      searchPlaceholder: 'Benutzer suchen...',
      online: 'Online',
      offline: 'Offline',
      remove: 'Entfernen',
      add: 'Hinzufügen',
      confirmRemove: 'Diesen Freund entfernen?',
      cancel: 'Abbrechen',
      message: 'Nachricht',
      addFriend: 'Freund hinzufügen',
      allUsers: 'Alle Benutzer',
      back: 'Zurück',
    },
  };

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  const loadData = useCallback(async () => {
    try {
      const [friendsData, usersData] = await Promise.all([
        api.getFriends(),
        api.getCommunityUsers(),
      ]);
      setFriends(friendsData || []);
      setAllUsers(usersData || []);
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

  const removeFriend = async (friendId: string) => {
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
    try {
      await api.addFriend(userId);
      const user = allUsers.find(u => u.user_id === userId);
      if (user) {
        setFriends(prev => [...prev, { ...user, added_at: new Date().toISOString() }]);
      }
    } catch (error: any) {
      Alert.alert('Errore', error.message || 'Impossibile aggiungere amico');
    }
  };

  const openChat = (userId: string) => {
    router.push({
      pathname: '/private-chat',
      params: { userId }
    });
  };

  const friendIds = friends.map(f => f.user_id);
  const filteredUsers = allUsers.filter(u => 
    !friendIds.includes(u.user_id) && 
    u.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderFriendItem = (friend: User) => (
    <View key={friend.user_id} style={styles.userCard} data-testid={`friend-${friend.user_id}`}>
      <View style={styles.userInfo}>
        <View style={styles.avatarContainer}>
          <View style={[styles.avatar, { backgroundColor: friend.is_online ? '#4CAF50' : COLORS.textSecondary }]}>
            <Text style={styles.avatarText}>{friend.name.charAt(0).toUpperCase()}</Text>
          </View>
          {friend.is_online && <View style={styles.onlineDot} />}
        </View>
        <View style={styles.userDetails}>
          <Text style={styles.userName}>{friend.name}</Text>
          <Text style={[styles.userStatus, { color: friend.is_online ? '#4CAF50' : COLORS.textSecondary }]}>
            {friend.is_online ? t('online') : t('offline')}
          </Text>
        </View>
      </View>
      <View style={styles.userActions}>
        <TouchableOpacity 
          style={[styles.actionBtn, styles.messageBtn]} 
          onPress={() => openChat(friend.user_id)}
          data-testid={`message-${friend.user_id}`}
        >
          <Icon name="chatbubble" size={18} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.actionBtn, styles.removeBtn]} 
          onPress={() => removeFriend(friend.user_id)}
          data-testid={`remove-${friend.user_id}`}
        >
          <Icon name="heart-dislike" size={18} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderUserItem = (user: User) => (
    <View key={user.user_id} style={styles.userCard} data-testid={`user-${user.user_id}`}>
      <View style={styles.userInfo}>
        <View style={styles.avatarContainer}>
          <View style={[styles.avatar, { backgroundColor: COLORS.primary }]}>
            <Text style={styles.avatarText}>{user.name.charAt(0).toUpperCase()}</Text>
          </View>
        </View>
        <View style={styles.userDetails}>
          <Text style={styles.userName}>{user.name}</Text>
        </View>
      </View>
      <TouchableOpacity 
        style={[styles.actionBtn, styles.addBtn]} 
        onPress={() => addFriend(user.user_id)}
        data-testid={`add-${user.user_id}`}
      >
        <Icon name="heart" size={18} color="#fff" />
        <Text style={styles.addBtnText}>{t('add')}</Text>
      </TouchableOpacity>
    </View>
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
        <TouchableOpacity 
          onPress={() => router.back()} 
          style={styles.backBtn}
          data-testid="friends-back-btn"
        >
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.title}>{showAddFriend ? t('addFriend') : t('title')}</Text>
          <Text style={styles.subtitle}>
            {showAddFriend ? t('allUsers') : `${friends.length} ${t('subtitle')}`}
          </Text>
        </View>
        <TouchableOpacity 
          style={styles.addFriendBtn} 
          onPress={() => setShowAddFriend(!showAddFriend)}
          data-testid="toggle-add-friend"
        >
          <Icon name={showAddFriend ? "close" : "person-add"} size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {showAddFriend && (
        <View style={styles.searchContainer}>
          <Icon name="search" size={20} color={COLORS.textSecondary} />
          <TextInput
            style={styles.searchInput}
            placeholder={t('searchPlaceholder')}
            placeholderTextColor={COLORS.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
            data-testid="search-users-input"
          />
        </View>
      )}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
        showsVerticalScrollIndicator={false}
      >
        {showAddFriend ? (
          filteredUsers.length > 0 ? (
            filteredUsers.map(renderUserItem)
          ) : (
            <View style={styles.emptyState}>
              <Icon name="people" size={64} color={COLORS.textSecondary} />
              <Text style={styles.emptyText}>{t('noFriends')}</Text>
            </View>
          )
        ) : friends.length > 0 ? (
          friends.map(renderFriendItem)
        ) : (
          <View style={styles.emptyState}>
            <Icon name="people" size={64} color={COLORS.textSecondary} />
            <Text style={styles.emptyText}>{t('noFriends')}</Text>
            <Text style={styles.emptyHint}>{t('addFriendHint')}</Text>
          </View>
        )}
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
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: {
    padding: SPACING.sm,
    marginRight: SPACING.md,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  addFriendBtn: {
    padding: SPACING.sm,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    margin: SPACING.md,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  searchInput: {
    flex: 1,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.sm,
    fontSize: 16,
    color: COLORS.text,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: SPACING.md,
    paddingBottom: SPACING.xl * 2,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  onlineDot: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#4CAF50',
    borderWidth: 2,
    borderColor: COLORS.surface,
  },
  userDetails: {
    marginLeft: SPACING.md,
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  userStatus: {
    fontSize: 13,
    marginTop: 2,
  },
  userActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  actionBtn: {
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
  },
  messageBtn: {
    backgroundColor: COLORS.primary,
  },
  removeBtn: {
    backgroundColor: '#E74C3C',
  },
  addBtn: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
  },
  addBtnText: {
    color: '#fff',
    fontWeight: '600',
    marginLeft: 4,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.lg,
  },
  emptyHint: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
});
