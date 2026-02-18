import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  Modal,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface Group {
  group_id: string;
  name: string;
  description: string;
  topic: string;
  creator_name: string;
  members_count: number;
  language: string;
}

interface Topic {
  name: string;
  icon: string;
  color: string;
}

export default function GroupsScreen() {
  const { currentLanguage } = useLanguageStore();
  const [groups, setGroups] = useState<Group[]>([]);
  const [myGroups, setMyGroups] = useState<Group[]>([]);
  const [topics, setTopics] = useState<Record<string, Topic>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'my'>('all');
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  // Create form state
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newGroupTopic, setNewGroupTopic] = useState('study');
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [topicsData, groupsData, myGroupsData] = await Promise.all([
        api.getGroupTopics(),
        api.getGroups(selectedTopic || undefined),
        api.getMyGroups(),
      ]);
      setTopics(topicsData);
      setGroups(groupsData);
      setMyGroups(myGroupsData);
    } catch (error) {
      console.log('Error loading data:', error);
    }
  }, [selectedTopic]);

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => setLoading(false));
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim() || !newGroupDesc.trim()) return;

    setCreating(true);
    try {
      await api.createGroup({
        name: newGroupName,
        description: newGroupDesc,
        topic: newGroupTopic,
        language: currentLanguage,
      });
      setShowCreateModal(false);
      setNewGroupName('');
      setNewGroupDesc('');
      await loadData();
    } catch (error) {
      console.log('Error creating group:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleJoinGroup = async (groupId: string) => {
    try {
      await api.joinGroup(groupId);
      await loadData();
    } catch (error) {
      console.log('Error joining group:', error);
    }
  };

  const renderGroup = ({ item }: { item: Group }) => {
    const topic = topics[item.topic];
    const isMember = myGroups.some(g => g.group_id === item.group_id);

    return (
      <TouchableOpacity
        style={styles.groupCard}
        onPress={() => router.push(`/group/${item.group_id}`)}
      >
        <View style={[styles.topicIcon, { backgroundColor: topic?.color + '20' }]}>
          <Text style={styles.topicEmoji}>{topic?.icon || '\ud83d\udcda'}</Text>
        </View>
        <View style={styles.groupInfo}>
          <Text style={styles.groupName}>{item.name}</Text>
          <Text style={styles.groupDesc} numberOfLines={2}>{item.description}</Text>
          <View style={styles.groupMeta}>
            <Icon name="people-outline" size={14} color={COLORS.textMuted} />
            <Text style={styles.groupMetaText}>{item.members_count} membri</Text>
            <Text style={styles.groupMetaText}>\u2022</Text>
            <Text style={styles.groupMetaText}>{topic?.name}</Text>
          </View>
        </View>
        {!isMember && (
          <TouchableOpacity
            style={styles.joinButton}
            onPress={() => handleJoinGroup(item.group_id)}
          >
            <Icon name="add" size={20} color={COLORS.primary} />
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  };

  const displayGroups = activeTab === 'my' ? myGroups : groups;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Gruppi Biblici</Text>
          <Text style={styles.headerSubtitle}>Connettiti e cresci insieme</Text>
        </View>
        <TouchableOpacity
          style={styles.createButton}
          onPress={() => setShowCreateModal(true)}
        >
          <Icon name="add-circle" size={28} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'all' && styles.tabActive]}
          onPress={() => setActiveTab('all')}
        >
          <Text style={[styles.tabText, activeTab === 'all' && styles.tabTextActive]}>
            Tutti i Gruppi
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'my' && styles.tabActive]}
          onPress={() => setActiveTab('my')}
        >
          <Text style={[styles.tabText, activeTab === 'my' && styles.tabTextActive]}>
            I Miei Gruppi
          </Text>
        </TouchableOpacity>
      </View>

      {/* Topic Filters */}
      {activeTab === 'all' && (
        <View style={styles.topicFilters}>
          <TouchableOpacity
            style={[styles.topicFilter, !selectedTopic && styles.topicFilterActive]}
            onPress={() => setSelectedTopic(null)}
          >
            <Text style={styles.topicFilterText}>Tutti</Text>
          </TouchableOpacity>
          {Object.entries(topics).map(([key, topic]) => (
            <TouchableOpacity
              key={key}
              style={[styles.topicFilter, selectedTopic === key && styles.topicFilterActive]}
              onPress={() => setSelectedTopic(key)}
            >
              <Text style={styles.topicFilterEmoji}>{topic.icon}</Text>
              <Text style={styles.topicFilterText}>{topic.name}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Groups List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : (
        <FlatList
          data={displayGroups}
          keyExtractor={(item) => item.group_id}
          renderItem={renderGroup}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Icon name="people-outline" size={64} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>
                {activeTab === 'my' ? 'Non sei ancora in nessun gruppo' : 'Nessun gruppo trovato'}
              </Text>
            </View>
          }
        />
      )}

      {/* Create Group Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Crea Nuovo Gruppo</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <Icon name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.input}
              placeholder="Nome del gruppo"
              placeholderTextColor={COLORS.textMuted}
              value={newGroupName}
              onChangeText={setNewGroupName}
            />

            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Descrizione"
              placeholderTextColor={COLORS.textMuted}
              value={newGroupDesc}
              onChangeText={setNewGroupDesc}
              multiline
              numberOfLines={3}
            />

            <Text style={styles.inputLabel}>Tema</Text>
            <View style={styles.topicSelector}>
              {Object.entries(topics).map(([key, topic]) => (
                <TouchableOpacity
                  key={key}
                  style={[
                    styles.topicOption,
                    newGroupTopic === key && { backgroundColor: topic.color + '30', borderColor: topic.color },
                  ]}
                  onPress={() => setNewGroupTopic(key)}
                >
                  <Text style={styles.topicOptionEmoji}>{topic.icon}</Text>
                  <Text style={styles.topicOptionText}>{topic.name}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity
              style={[styles.createGroupButton, creating && styles.createGroupButtonDisabled]}
              onPress={handleCreateGroup}
              disabled={creating}
            >
              {creating ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.createGroupButtonText}>Crea Gruppo</Text>
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
  createButton: {
    padding: SPACING.sm,
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    paddingHorizontal: SPACING.md,
    gap: SPACING.md,
  },
  tab: {
    paddingVertical: SPACING.md,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: COLORS.primary,
  },
  tabText: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  tabTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  topicFilters: {
    flexDirection: 'row',
    padding: SPACING.md,
    gap: SPACING.sm,
    flexWrap: 'wrap',
  },
  topicFilter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.full,
    gap: 4,
  },
  topicFilterActive: {
    backgroundColor: COLORS.primary + '20',
  },
  topicFilterEmoji: {
    fontSize: 14,
  },
  topicFilterText: {
    fontSize: 12,
    color: COLORS.text,
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
  groupCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  topicIcon: {
    width: 50,
    height: 50,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  topicEmoji: {
    fontSize: 24,
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
    color: COLORS.textLight,
    marginTop: 4,
  },
  groupMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.sm,
    gap: 6,
  },
  groupMetaText: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  joinButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textLight,
    marginTop: SPACING.md,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    maxHeight: '90%',
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
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  topicSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  topicOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 2,
    borderColor: COLORS.border,
    gap: 6,
  },
  topicOptionEmoji: {
    fontSize: 18,
  },
  topicOptionText: {
    fontSize: 13,
    color: COLORS.text,
  },
  createGroupButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
  },
  createGroupButtonDisabled: {
    opacity: 0.7,
  },
  createGroupButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
