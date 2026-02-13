import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface Message {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

const QUICK_PROMPTS = [
  "Come posso trovare pace interiore?",
  "Cosa dice la Bibbia sull'ansia?",
  "Come posso crescere nella fede?",
  "Ho bisogno di incoraggiamento",
];

export default function AssistantScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const history = await api.getChatHistory();
      setMessages(history);
    } catch (error) {
      console.log('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    setInput('');
    setSending(true);

    // Add user message locally
    const userMessage: Message = {
      message_id: Date.now().toString(),
      role: 'user',
      content: messageText,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.sendMessage(messageText);
      
      // Add assistant response
      const assistantMessage: Message = {
        message_id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      // Show error message
      const errorMessage: Message = {
        message_id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Mi dispiace, si è verificato un errore. Riprova più tardi.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await api.clearChatHistory();
      setMessages([]);
    } catch (error) {
      console.log('Error clearing history:', error);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.messageContainer, isUser && styles.userMessageContainer]}>
        {!isUser && (
          <View style={styles.assistantAvatar}>
            <Icon name="sparkles" size={18} color={COLORS.primary} />
          </View>
        )}
        <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.assistantBubble]}>
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {item.content}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
          <Icon name="close" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Assistente Spirituale</Text>
          <Text style={styles.headerSubtitle}>Chiedi guida e conforto</Text>
        </View>
        <TouchableOpacity style={styles.clearButton} onPress={handleClearHistory}>
          <Icon name="trash-outline" size={22} color={COLORS.textLight} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Messages */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
        ) : messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIcon}>
              <Icon name="chatbubble-ellipses" size={48} color={COLORS.primary} />
            </View>
            <Text style={styles.emptyTitle}>Ciao! Sono qui per te</Text>
            <Text style={styles.emptyText}>
              Chiedimi qualsiasi cosa sulla fede, la Bibbia, o semplicemente condividi come ti senti.
            </Text>
            
            <Text style={styles.quickPromptsTitle}>Inizia con una domanda:</Text>
            <View style={styles.quickPrompts}>
              {QUICK_PROMPTS.map((prompt, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.quickPromptButton}
                  onPress={() => handleSend(prompt)}
                >
                  <Text style={styles.quickPromptText}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.message_id}
            renderItem={renderMessage}
            contentContainerStyle={styles.messagesContent}
            onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
            onLayout={() => flatListRef.current?.scrollToEnd()}
          />
        )}

        {/* Sending indicator */}
        {sending && (
          <View style={styles.sendingIndicator}>
            <ActivityIndicator size="small" color={COLORS.primary} />
            <Text style={styles.sendingText}>L'assistente sta pensando...</Text>
          </View>
        )}

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Scrivi il tuo messaggio..."
            placeholderTextColor={COLORS.textMuted}
            value={input}
            onChangeText={setInput}
            multiline
            maxLength={1000}
          />
          <TouchableOpacity
            style={[styles.sendButton, !input.trim() && styles.sendButtonDisabled]}
            onPress={() => handleSend()}
            disabled={!input.trim() || sending}
          >
            <Icon name="send" size={20} color="#fff" />
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
  closeButton: {
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
  clearButton: {
    padding: SPACING.sm,
  },
  keyboardView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    padding: SPACING.xl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  emptyText: {
    fontSize: 15,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.lg,
  },
  quickPromptsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textLight,
    marginBottom: SPACING.md,
  },
  quickPrompts: {
    width: '100%',
    gap: SPACING.sm,
  },
  quickPromptButton: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  quickPromptText: {
    fontSize: 14,
    color: COLORS.text,
    textAlign: 'center',
  },
  messagesContent: {
    padding: SPACING.md,
    paddingBottom: SPACING.lg,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: SPACING.md,
    alignItems: 'flex-end',
  },
  userMessageContainer: {
    justifyContent: 'flex-end',
  },
  assistantAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.sm,
  },
  messageBubble: {
    maxWidth: '75%',
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
  },
  userBubble: {
    backgroundColor: COLORS.primary,
    borderBottomRightRadius: SPACING.xs,
  },
  assistantBubble: {
    backgroundColor: COLORS.card,
    borderBottomLeftRadius: SPACING.xs,
    ...SHADOWS.small,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
    color: COLORS.text,
  },
  userMessageText: {
    color: '#fff',
  },
  sendingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.sm,
    gap: SPACING.sm,
  },
  sendingText: {
    fontSize: 13,
    color: COLORS.textLight,
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
});
