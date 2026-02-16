import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useTranslation } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface ForumCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface ForumPost {
  post_id: string;
  user_name: string;
  title: string;
  content: string;
  category: string;
  votes: number;
  replies_count: number;
  views: number;
  created_at: string;
}

export default function ForumScreen() {
  const { t } = useTranslation();
  const [categories, setCategories] = useState<ForumCategory[]>([]);
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showNewPost, setShowNewPost] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [catData, postsData] = await Promise.all([
        api.getForumCategories(),
        api.getForumPosts(),
      ]);
      setCategories(catData);
      setPosts(postsData);
    } catch (error) {
      console.error('Error loading forum:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPosts = async (category?: string) => {
    setLoading(true);
    try {
      const data = await api.getForumPosts(category || undefined);
      setPosts(data);
    } catch (error) {
      console.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = (catId: string | null) => {
    setSelectedCategory(catId);
    loadPosts(catId || undefined);
  };

  const handleVote = async (postId: string) => {
    try {
      const result = await api.voteForumPost(postId);
      setPosts(posts.map(p => 
        p.post_id === postId ? { ...p, votes: result.votes } : p
      ));
    } catch (error) {
      Alert.alert(t('error'), t('unableToVote'));
    }
  };

  const submitNewPost = async () => {
    if (!newTitle.trim() || !newContent.trim() || !newCategory) {
      Alert.alert(t('error'), t('fillAllFields'));
      return;
    }

    setSubmitting(true);
    try {
      const post = await api.createForumPost(newTitle, newContent, newCategory);
      setPosts([post, ...posts]);
      setShowNewPost(false);
      setNewTitle('');
      setNewContent('');
      setNewCategory('');
      Alert.alert(t('published'), t('postCreated'));
    } catch (error) {
      Alert.alert(t('error'), t('unableToCreatePost'));
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryIcon = (catId: string) => {
    const cat = categories.find(c => c.id === catId);
    return cat?.icon || '💬';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
  };

  if (loading && posts.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('communityForum')}</Text>
        <TouchableOpacity onPress={() => setShowNewPost(true)}>
          <Icon name="add-circle" size={28} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {/* Categories */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoriesScroll}>
        <TouchableOpacity
          style={[styles.categoryChip, !selectedCategory && styles.categoryChipSelected]}
          onPress={() => handleCategorySelect(null)}
        >
          <Text style={[styles.categoryChipText, !selectedCategory && styles.categoryChipTextSelected]}>
            {t('all')}
          </Text>
        </TouchableOpacity>
        {categories.map(cat => (
          <TouchableOpacity
            key={cat.id}
            style={[styles.categoryChip, selectedCategory === cat.id && styles.categoryChipSelected]}
            onPress={() => handleCategorySelect(cat.id)}
          >
            <Text style={styles.categoryIcon}>{cat.icon}</Text>
            <Text style={[styles.categoryChipText, selectedCategory === cat.id && styles.categoryChipTextSelected]}>
              {cat.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Posts */}
      <FlatList
        data={posts}
        keyExtractor={(item) => item.post_id}
        contentContainerStyle={styles.postsContainer}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.postCard}
            onPress={() => router.push(`/forum/${item.post_id}`)}
          >
            <View style={styles.postHeader}>
              <Text style={styles.postCategory}>{getCategoryIcon(item.category)}</Text>
              <Text style={styles.postAuthor}>{item.user_name}</Text>
              <Text style={styles.postDate}>{formatDate(item.created_at)}</Text>
            </View>
            <Text style={styles.postTitle} numberOfLines={2}>{item.title}</Text>
            <Text style={styles.postContent} numberOfLines={2}>{item.content}</Text>
            <View style={styles.postFooter}>
              <TouchableOpacity style={styles.postAction} onPress={() => handleVote(item.post_id)}>
                <Icon name="heart" size={18} color={COLORS.error} />
                <Text style={styles.postActionText}>{item.votes}</Text>
              </TouchableOpacity>
              <View style={styles.postAction}>
                <Icon name="chatbubble" size={18} color={COLORS.textMuted} />
                <Text style={styles.postActionText}>{item.replies_count}</Text>
              </View>
              <View style={styles.postAction}>
                <Icon name="eye" size={18} color={COLORS.textMuted} />
                <Text style={styles.postActionText}>{item.views}</Text>
              </View>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="chatbubbles-outline" size={60} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>{t('noPostsYet')}</Text>
            <Text style={styles.emptySubtext}>{t('beFirstToPost')}</Text>
          </View>
        }
      />

      {/* New Post Modal */}
      {showNewPost && (
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{t('newPost')}</Text>
              <TouchableOpacity onPress={() => setShowNewPost(false)}>
                <Icon name="close" size={28} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent}>
              <Text style={styles.fieldLabel}>{t('category')}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categorySelect}>
                {categories.map(cat => (
                  <TouchableOpacity
                    key={cat.id}
                    style={[styles.categoryOption, newCategory === cat.id && styles.categoryOptionSelected]}
                    onPress={() => setNewCategory(cat.id)}
                  >
                    <Text style={styles.categoryOptionIcon}>{cat.icon}</Text>
                    <Text style={[styles.categoryOptionText, newCategory === cat.id && styles.categoryOptionTextSelected]}>
                      {cat.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>

              <Text style={styles.fieldLabel}>{t('title')}</Text>
              <TextInput
                style={styles.input}
                placeholder={t('postTitlePlaceholder')}
                placeholderTextColor={COLORS.textMuted}
                value={newTitle}
                onChangeText={setNewTitle}
              />

              <Text style={styles.fieldLabel}>{t('content')}</Text>
              <TextInput
                style={[styles.input, styles.contentInput]}
                placeholder={t('writeYourMessage')}
                placeholderTextColor={COLORS.textMuted}
                multiline
                numberOfLines={6}
                value={newContent}
                onChangeText={setNewContent}
              />

              <TouchableOpacity
                style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
                onPress={submitNewPost}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.submitButtonText}>{t('publish')}</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      )}
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
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  categoriesScroll: {
    backgroundColor: COLORS.card,
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.md,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.background,
    marginRight: SPACING.sm,
  },
  categoryChipSelected: {
    backgroundColor: COLORS.primary,
  },
  categoryIcon: {
    fontSize: 16,
    marginRight: SPACING.xs,
  },
  categoryChipText: {
    fontSize: 14,
    color: COLORS.text,
  },
  categoryChipTextSelected: {
    color: '#fff',
  },
  postsContainer: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  postCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  postCategory: {
    fontSize: 18,
    marginRight: SPACING.sm,
  },
  postAuthor: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  postDate: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  postTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  postContent: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 20,
  },
  postFooter: {
    flexDirection: 'row',
    marginTop: SPACING.md,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  postAction: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: SPACING.lg,
  },
  postActionText: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginLeft: SPACING.xs,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  modalContent: {
    padding: SPACING.md,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
    marginTop: SPACING.md,
  },
  categorySelect: {
    flexDirection: 'row',
  },
  categoryOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.background,
    marginRight: SPACING.sm,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  categoryOptionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  categoryOptionIcon: {
    fontSize: 16,
    marginRight: SPACING.xs,
  },
  categoryOptionText: {
    fontSize: 13,
    color: COLORS.text,
  },
  categoryOptionTextSelected: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
  },
  contentInput: {
    minHeight: 120,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.lg,
    marginBottom: SPACING.xl,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
});
