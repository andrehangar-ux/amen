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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface LiveEvent {
  event_id: string;
  creator_name: string;
  title: string;
  description: string;
  event_type: string;
  scheduled_at: string;
  duration_minutes: number;
  participants: string[];
  status: string;
  bible_book?: string;
  bible_chapter?: number;
}

const EVENT_TYPES = [
  { id: 'reading', name: 'Lettura Biblica', icon: 'book', color: '#4CAF50' },
  { id: 'worship', name: 'Lode e Adorazione', icon: 'musical-notes', color: '#9C27B0' },
  { id: 'prayer', name: 'Preghiera', icon: 'heart', color: '#E91E63' },
  { id: 'study', name: 'Studio Biblico', icon: 'school', color: '#2196F3' },
];

export default function EventsScreen() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [showNewEvent, setShowNewEvent] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // New event form
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newType, setNewType] = useState('');
  const [newDate, setNewDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const data = await api.getEvents();
      setEvents(data);
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setLoading(false);
    }
  };

  const joinEvent = async (eventId: string) => {
    try {
      await api.joinEvent(eventId);
      Alert.alert('Iscritto!', 'Ti sei iscritto all\'evento');
      loadEvents();
    } catch (error) {
      Alert.alert('Errore', 'Impossibile iscriversi');
    }
  };

  const createEvent = async () => {
    if (!newTitle.trim() || !newDescription.trim() || !newType) {
      Alert.alert('Errore', 'Compila tutti i campi');
      return;
    }

    setSubmitting(true);
    try {
      const event = await api.createEvent({
        title: newTitle,
        description: newDescription,
        event_type: newType,
        scheduled_at: newDate.toISOString(),
        duration_minutes: 60,
      });
      setEvents([event, ...events]);
      setShowNewEvent(false);
      resetForm();
      Alert.alert('Creato!', 'Il tuo evento è stato creato');
    } catch (error) {
      Alert.alert('Errore', 'Impossibile creare l\'evento');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setNewTitle('');
    setNewDescription('');
    setNewType('');
    setNewDate(new Date());
  };

  const getEventType = (typeId: string) => {
    return EVENT_TYPES.find(t => t.id === typeId) || EVENT_TYPES[0];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'live':
        return { text: 'IN DIRETTA', color: '#E91E63' };
      case 'scheduled':
        return { text: 'PROGRAMMATO', color: COLORS.primary };
      case 'ended':
        return { text: 'TERMINATO', color: COLORS.textMuted };
      default:
        return { text: status, color: COLORS.textMuted };
    }
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
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Eventi Live</Text>
        <TouchableOpacity onPress={() => setShowNewEvent(true)}>
          <Icon name="add-circle" size={28} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.heroCard}>
          <Icon name="videocam" size={40} color={COLORS.primary} />
          <Text style={styles.heroTitle}>Eventi Sincronizzati</Text>
          <Text style={styles.heroText}>
            Partecipa a letture bibliche, momenti di lode e preghiera con altri credenti in tempo reale.
          </Text>
        </View>

        {/* Event Types */}
        <Text style={styles.sectionTitle}>Tipi di Evento</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.typesScroll}>
          {EVENT_TYPES.map((type) => (
            <View key={type.id} style={styles.typeCard}>
              <View style={[styles.typeIcon, { backgroundColor: type.color + '20' }]}>
                <Icon name={type.icon as any} size={24} color={type.color} />
              </View>
              <Text style={styles.typeName}>{type.name}</Text>
            </View>
          ))}
        </ScrollView>

        {/* Events List */}
        <Text style={styles.sectionTitle}>Prossimi Eventi</Text>
        {events.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="calendar-outline" size={60} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>Nessun evento in programma</Text>
            <Text style={styles.emptySubtext}>Crea il primo evento!</Text>
          </View>
        ) : (
          events.map((event) => {
            const type = getEventType(event.event_type);
            const statusBadge = getStatusBadge(event.status);

            return (
              <View key={event.event_id} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={[styles.eventTypeIcon, { backgroundColor: type.color + '20' }]}>
                    <Icon name={type.icon as any} size={22} color={type.color} />
                  </View>
                  <View style={styles.eventHeaderContent}>
                    <Text style={styles.eventTitle}>{event.title}</Text>
                    <Text style={styles.eventCreator}>di {event.creator_name}</Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: statusBadge.color + '20' }]}>
                    <Text style={[styles.statusBadgeText, { color: statusBadge.color }]}>
                      {statusBadge.text}
                    </Text>
                  </View>
                </View>

                <Text style={styles.eventDescription} numberOfLines={2}>
                  {event.description}
                </Text>

                <View style={styles.eventMeta}>
                  <View style={styles.eventMetaItem}>
                    <Icon name="calendar" size={16} color={COLORS.textMuted} />
                    <Text style={styles.eventMetaText}>{formatDate(event.scheduled_at)}</Text>
                  </View>
                  <View style={styles.eventMetaItem}>
                    <Icon name="time" size={16} color={COLORS.textMuted} />
                    <Text style={styles.eventMetaText}>{event.duration_minutes} min</Text>
                  </View>
                  <View style={styles.eventMetaItem}>
                    <Icon name="people" size={16} color={COLORS.textMuted} />
                    <Text style={styles.eventMetaText}>{event.participants.length}</Text>
                  </View>
                </View>

                {event.status === 'scheduled' && (
                  <TouchableOpacity
                    style={styles.joinButton}
                    onPress={() => joinEvent(event.event_id)}
                  >
                    <Text style={styles.joinButtonText}>Partecipa</Text>
                  </TouchableOpacity>
                )}

                {event.status === 'live' && (
                  <TouchableOpacity style={[styles.joinButton, styles.liveButton]}>
                    <Icon name="radio" size={18} color="#fff" />
                    <Text style={styles.joinButtonText}>Entra nella Diretta</Text>
                  </TouchableOpacity>
                )}
              </View>
            );
          })
        )}
      </ScrollView>

      {/* New Event Modal */}
      {showNewEvent && (
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Nuovo Evento</Text>
              <TouchableOpacity onPress={() => setShowNewEvent(false)}>
                <Icon name="close" size={28} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalContent}>
              <Text style={styles.fieldLabel}>Tipo di Evento</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                {EVENT_TYPES.map((type) => (
                  <TouchableOpacity
                    key={type.id}
                    style={[
                      styles.typeOption,
                      newType === type.id && styles.typeOptionSelected,
                    ]}
                    onPress={() => setNewType(type.id)}
                  >
                    <Icon name={type.icon as any} size={20} color={newType === type.id ? '#fff' : type.color} />
                    <Text style={[styles.typeOptionText, newType === type.id && { color: '#fff' }]}>
                      {type.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>

              <Text style={styles.fieldLabel}>Titolo</Text>
              <TextInput
                style={styles.input}
                placeholder="Titolo dell'evento..."
                placeholderTextColor={COLORS.textMuted}
                value={newTitle}
                onChangeText={setNewTitle}
              />

              <Text style={styles.fieldLabel}>Descrizione</Text>
              <TextInput
                style={[styles.input, styles.descInput]}
                placeholder="Descrivi l'evento..."
                placeholderTextColor={COLORS.textMuted}
                multiline
                numberOfLines={3}
                value={newDescription}
                onChangeText={setNewDescription}
              />

              <Text style={styles.fieldLabel}>Data e Ora</Text>
              <TouchableOpacity
                style={styles.dateButton}
                onPress={() => setShowDatePicker(true)}
              >
                <Icon name="calendar" size={20} color={COLORS.primary} />
                <Text style={styles.dateButtonText}>
                  {newDate.toLocaleDateString('it-IT', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </TouchableOpacity>

              {showDatePicker && (
                <DateTimePicker
                  value={newDate}
                  mode="datetime"
                  display="default"
                  onChange={(event, date) => {
                    setShowDatePicker(false);
                    if (date) setNewDate(date);
                  }}
                />
              )}

              <TouchableOpacity
                style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
                onPress={createEvent}
                disabled={submitting}
              >
                {submitting ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.submitButtonText}>Crea Evento</Text>
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
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  heroCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.md,
  },
  heroText: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: SPACING.sm,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
    marginTop: SPACING.md,
  },
  typesScroll: {
    marginBottom: SPACING.md,
  },
  typeCard: {
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  typeIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  typeName: {
    fontSize: 11,
    color: COLORS.textLight,
    marginTop: SPACING.xs,
    textAlign: 'center',
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
  eventCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  eventHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  eventTypeIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  eventHeaderContent: {
    flex: 1,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  eventCreator: {
    fontSize: 12,
    color: COLORS.textMuted,
  },
  statusBadge: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: BORDER_RADIUS.sm,
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  eventDescription: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: SPACING.sm,
    lineHeight: 20,
  },
  eventMeta: {
    flexDirection: 'row',
    marginTop: SPACING.md,
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  eventMetaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: SPACING.lg,
  },
  eventMetaText: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginLeft: SPACING.xs,
  },
  joinButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.sm,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: SPACING.md,
  },
  liveButton: {
    backgroundColor: '#E91E63',
  },
  joinButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: SPACING.xs,
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
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.background,
    marginRight: SPACING.sm,
  },
  typeOptionSelected: {
    backgroundColor: COLORS.primary,
  },
  typeOptionText: {
    fontSize: 13,
    marginLeft: SPACING.xs,
    color: COLORS.text,
  },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
  },
  descInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
  },
  dateButtonText: {
    fontSize: 15,
    color: COLORS.text,
    marginLeft: SPACING.sm,
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
