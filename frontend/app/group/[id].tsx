import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { api } from '../../src/utils/api';
import { useAuthStore } from '../../src/store/authStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

interface Post {
  post_id: string;
  user_id: string;
  user_name: string;
  content: string;
  post_type: string;
  bible_reference?: string;
  likes: number;
  liked_by: string[];
  comments: any[];
  comments_count: number;
  created_at: string;
}

interface Group {
  group_id: string;
  name: string;
  description: string;
  topic: string;
  members_count: number;
}

export default function GroupDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuthStore();
  const [group, setGroup] = useState<Group | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);
  const [commentingOn, setCommentingOn] = useState<string | null>(null);
  const [commentText, setCommentText] = useState('');

  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      const [groupData, postsData] = await Promise.all([
        api.getGroup(id),
        api.getGroupPosts(id),
      ]);
      setGroup(groupData);
      setPosts(postsData);
    } catch (error) {
      console.log('Error loading data:', error);
    }
  }, [id]);

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => setLoading(false));
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handlePost = async () => {
    if (!newPost.trim() || !id) return;

    setPosting(true);
    try {
      await api.createGroupPost(id, newPost);
      setNewPost('');
      await loadData();
    } catch (error) {
      console.log('Error posting:', error);
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (postId: string) => {
    if (!id) return;
    try {
      await api.likePost(id, postId);
      await loadData();
    } catch (error) {
      console.log('Error liking:', error);
    }
  };

  const handleComment = async (postId: string) => {
    if (!commentText.trim() || !id) return;

    try {
      await api.addComment(id, postId, commentText);
      setCommentText('');
      setCommentingOn(null);
      await loadData();
    } catch (error) {
      console.log('Error commenting:', error);
    }
  };

  const renderPost = ({ item }: { item: Post }) => {
    const isLiked = item.liked_by?.includes(user?.user_id || '');

    return (
      <View style={styles.postCard}>
        <View style={styles.postHeader}>
          <View style={styles.postAvatar}>
            <Text style={styles.postAvatarText}>{item.user_name.charAt(0)}</Text>
          </View>
          <View style={styles.postMeta}>
            <Text style={styles.postAuthor}>{item.user_name}</Text>
            <Text style={styles.postTime}>
              {format(new Date(item.created_at), 'd MMM, HH:mm', { locale: it })}
            </Text>
          </View>
          {item.post_type === 'prayer' && (
            <View style={styles.prayerBadge}>
              <Text style={styles.prayerBadgeText}>\ud83d\ude4f Preghiera</Text>
            </View>
          )}
        </View>

        <Text style={styles.postContent}>{item.content}</Text>

        {item.bible_reference && (
          <View style={styles.bibleRef}>
            <Ionicons name="book-outline" size={14} color={COLORS.primary} />
            <Text style={styles.bibleRefText}>{item.bible_reference}</Text>
          </View>
        )}

        <View style={styles.postActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleLike(item.post_id)}
          >
            <Ionicons
              name={isLiked ? 'heart' : 'heart-outline'}
              size={20}
              color={isLiked ? COLORS.error : COLORS.textLight}
            />
            <Text style={styles.actionText}>{item.likes}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setCommentingOn(commentingOn === item.post_id ? null : item.post_id)}
          >
            <Ionicons name="chatbubble-outline" size={18} color={COLORS.textLight} />
            <Text style={styles.actionText}>{item.comments_count}</Text>
          </TouchableOpacity>
        </View>

        {/* Comments */}
        {item.comments && item.comments.length > 0 && (
          <View style={styles.comments}>
            {item.comments.slice(-3).map((comment: any, idx: number) => (
              <View key={idx} style={styles.comment}>
                <Text style={styles.commentAuthor}>{comment.user_name}:</Text>
                <Text style={styles.commentText}>{comment.content}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Comment Input */}
        {commentingOn === item.post_id && (
          <View style={styles.commentInput}>
            <TextInput
              style={styles.commentTextInput}
              placeholder="Scrivi un commento..."
              placeholderTextColor={COLORS.textMuted}
              value={commentText}
              onChangeText={setCommentText}
            />
            <TouchableOpacity
              style={styles.commentSendButton}
              onPress={() => handleComment(item.post_id)}
            >
              <Ionicons name="send" size={18} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle} numberOfLines={1}>{group?.name}</Text>
          <Text style={styles.headerSubtitle}>{group?.members_count} membri</Text>
        </View>
        <TouchableOpacity style={styles.infoButton}>
          <Ionicons name="information-circle-outline" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Posts */}
        <FlatList
          data={posts}
          keyExtractor={(item) => item.post_id}
          renderItem={renderPost}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="chatbubbles-outline" size={64} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>Nessun post ancora</Text>
              <Text style={styles.emptySubtext}>Sii il primo a condividere!</Text>
            </View>
          }
        />

        {/* New Post Input */}
        <View style={styles.newPostContainer}>
          <TextInput
            style={styles.newPostInput}
            placeholder="Condividi un pensiero, una preghiera..."
            placeholderTextColor={COLORS.textMuted}
            value={newPost}
            onChangeText={setNewPost}
            multiline
          />
          <TouchableOpacity
            style={[styles.postButton, !newPost.trim() && styles.postButtonDisabled]}
            onPress={handlePost}
            disabled={posting || !newPost.trim()}
          >
            {posting ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="send" size={20} color="#fff" />
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerSubtitle: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  infoButton: {
    padding: SPACING.sm,
  },
  keyboardView: {
    flex: 1,
  },
  listContent: {
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
  postAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  postAvatarText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
  },
  postMeta: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  postAuthor: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  postTime: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  prayerBadge: {
    backgroundColor: COLORS.accent + '20',
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
  },
  prayerBadgeText: {
    fontSize: 11,
    color: COLORS.accent,
  },
  postContent: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 24,
  },
  bibleRef: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.sm,
    gap: 6,
  },
  bibleRefText: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '500',
  },
  postActions: {
    flexDirection: 'row',
    marginTop: SPACING.md,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.lg,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  actionText: {
    fontSize: 13,
    color: COLORS.textLight,
  },
  comments: {
    marginTop: SPACING.md,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  comment: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  commentAuthor: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.text,
    marginRight: 6,
  },
  commentText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.textLight,
  },
  commentInput: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.sm,
    gap: SPACING.sm,
  },
  commentTextInput: {
    flex: 1,
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.full,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 14,
    color: COLORS.text,
  },
  commentSendButton: {
    padding: SPACING.sm,
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
  },
  newPostContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  newPostInput: {
    flex: 1,
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 15,
    color: COLORS.text,
    maxHeight: 100,
  },
  postButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  postButtonDisabled: {
    backgroundColor: COLORS.textMuted,
  },
});
