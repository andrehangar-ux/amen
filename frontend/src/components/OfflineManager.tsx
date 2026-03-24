import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../utils/theme';
import Icon from './Icon';
import { offlineService } from '../services/OfflineService';
import { useAuthStore } from '../store/authStore';
import { useTranslation } from '../store/languageStore';

interface OfflineManagerProps {
  onDownloadComplete?: () => void;
}

export default function OfflineManager({ onDownloadComplete }: OfflineManagerProps) {
  const [isOnline, setIsOnline] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [currentItem, setCurrentItem] = useState('');
  const [storageInfo, setStorageInfo] = useState({ used: 0, items: 0 });
  const [isOfflineAvailable, setIsOfflineAvailable] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  
  const { sessionToken } = useAuthStore();
  const { t } = useTranslation();

  useEffect(() => {
    loadStatus();
    
    const unsubscribe = offlineService.onNetworkChange((online) => {
      setIsOnline(online);
    });
    
    return () => unsubscribe();
  }, []);

  const loadStatus = async () => {
    const online = await offlineService.checkOnline();
    setIsOnline(online);
    
    const status = await offlineService.getDownloadStatus();
    setIsDownloading(status.isDownloading);
    setDownloadProgress(status.progress);
    setCurrentItem(status.currentItem);
    
    const storage = await offlineService.getStorageInfo();
    setStorageInfo(storage);
    
    const available = await offlineService.isBibleAvailableOffline();
    setIsOfflineAvailable(available);
    
    const sync = await offlineService.getLastSyncTime();
    setLastSync(sync);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const showAlert = (title: string, message: string, buttons?: any[]) => {
    if (Platform.OS === 'web') {
      if (buttons && buttons.length > 1) {
        if (window.confirm(`${title}\n\n${message}`)) {
          buttons[1]?.onPress?.();
        }
      } else {
        window.alert(`${title}\n\n${message}`);
      }
    } else {
      Alert.alert(title, message, buttons);
    }
  };

  const handleDownloadBible = async () => {
    if (!sessionToken) {
      showAlert(t('error'), 'Devi essere autenticato per scaricare i contenuti offline');
      return;
    }

    showAlert(
      'Download Offline',
      'Vuoi scaricare la Bibbia (Nuova Diodati, Reina Valera, CEI), i quiz e i tuoi dati personali per l\'uso offline?\n\nQuesto potrebbe richiedere alcuni minuti e circa 100-200 MB di spazio.',
      [
        { text: 'Annulla', style: 'cancel' },
        {
          text: 'Scarica',
          onPress: async () => {
            setIsDownloading(true);
            setDownloadProgress(0);
            
            try {
              // Download Bible
              setCurrentItem('Scaricamento Bibbia...');
              const bibleSuccess = await offlineService.downloadFullBible(
                sessionToken,
                (status) => {
                  setDownloadProgress(status.progress * 0.7); // 70% for Bible
                  setCurrentItem(status.currentItem);
                }
              );

              // Download Quiz
              setCurrentItem('Scaricamento Quiz...');
              setDownloadProgress(75);
              await offlineService.downloadQuizData(sessionToken);
              setDownloadProgress(85);

              // Sync user data
              setCurrentItem('Sincronizzazione dati personali...');
              await offlineService.syncUserData(sessionToken);
              setDownloadProgress(100);

              setCurrentItem('Completato!');
              await loadStatus();
              
              showAlert('Successo', 'I contenuti sono stati scaricati per l\'uso offline!');
              onDownloadComplete?.();
            } catch (error) {
              console.error('Download error:', error);
              showAlert(t('error'), 'Errore durante il download. Riprova.');
            } finally {
              setIsDownloading(false);
            }
          },
        },
      ]
    );
  };

  const handleClearData = () => {
    showAlert(
      'Elimina dati offline',
      'Sei sicuro di voler eliminare tutti i dati scaricati? Dovrai riscaricarli per usarli offline.',
      [
        { text: 'Annulla', style: 'cancel' },
        {
          text: 'Elimina',
          style: 'destructive',
          onPress: async () => {
            await offlineService.clearOfflineData();
            await loadStatus();
            showAlert('Fatto', 'Dati offline eliminati.');
          },
        },
      ]
    );
  };

  const handleSyncData = async () => {
    if (!sessionToken) {
      showAlert(t('error'), 'Devi essere autenticato per sincronizzare');
      return;
    }

    setCurrentItem('Sincronizzazione...');
    const success = await offlineService.syncUserData(sessionToken);
    await loadStatus();
    
    if (success) {
      showAlert('Successo', 'Note e segnalibri sincronizzati!');
    } else {
      showAlert(t('error'), 'Errore durante la sincronizzazione');
    }
  };

  return (
    <View style={styles.container}>
      {/* Network Status */}
      <View style={styles.statusRow}>
        <View style={styles.statusIndicator}>
          <View style={[styles.statusDot, isOnline ? styles.online : styles.offline]} />
          <Text style={styles.statusText}>
            {isOnline ? 'Online' : 'Offline'}
          </Text>
        </View>
        {!isOnline && isOfflineAvailable && (
          <Text style={styles.offlineNote}>Modalità offline attiva</Text>
        )}
      </View>

      {/* Download Progress */}
      {isDownloading && (
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${downloadProgress}%` }]} />
          </View>
          <Text style={styles.progressText}>{Math.round(downloadProgress)}%</Text>
          <Text style={styles.currentItem}>{currentItem}</Text>
        </View>
      )}

      {/* Storage Info */}
      <View style={styles.infoCard}>
        <View style={styles.infoRow}>
          <Icon name="folder-outline" size={20} color={COLORS.textLight} />
          <Text style={styles.infoLabel}>Spazio utilizzato:</Text>
          <Text style={styles.infoValue}>{formatBytes(storageInfo.used)}</Text>
        </View>
        <View style={styles.infoRow}>
          <Icon name="document-outline" size={20} color={COLORS.textLight} />
          <Text style={styles.infoLabel}>Elementi salvati:</Text>
          <Text style={styles.infoValue}>{storageInfo.items}</Text>
        </View>
        {lastSync && (
          <View style={styles.infoRow}>
            <Icon name="sync-outline" size={20} color={COLORS.textLight} />
            <Text style={styles.infoLabel}>Ultima sincronizzazione:</Text>
            <Text style={styles.infoValue}>{formatDate(lastSync)}</Text>
          </View>
        )}
      </View>

      {/* Offline Availability */}
      <View style={styles.availabilityCard}>
        <Text style={styles.availabilityTitle}>Contenuti disponibili offline:</Text>
        <View style={styles.availabilityRow}>
          <Icon
            name={isOfflineAvailable ? 'checkmark-circle' : 'close-circle'}
            size={20}
            color={isOfflineAvailable ? COLORS.success : COLORS.error}
          />
          <Text style={styles.availabilityText}>Bibbia (Nuova Diodati, Reina Valera, CEI)</Text>
        </View>
        <View style={styles.availabilityRow}>
          <Icon
            name={storageInfo.items > 0 ? 'checkmark-circle' : 'close-circle'}
            size={20}
            color={storageInfo.items > 0 ? COLORS.success : COLORS.error}
          />
          <Text style={styles.availabilityText}>Quiz Biblici</Text>
        </View>
        <View style={styles.availabilityRow}>
          <Icon
            name={lastSync ? 'checkmark-circle' : 'close-circle'}
            size={20}
            color={lastSync ? COLORS.success : COLORS.error}
          />
          <Text style={styles.availabilityText}>Note e Segnalibri</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleDownloadBible}
          disabled={isDownloading || !isOnline}
        >
          {isDownloading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <>
              <Icon name="cloud-download-outline" size={20} color="#fff" />
              <Text style={styles.buttonText}>
                {isOfflineAvailable ? 'Aggiorna contenuti' : 'Scarica per offline'}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {isOnline && lastSync && (
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={handleSyncData}
          >
            <Icon name="sync-outline" size={20} color={COLORS.primary} />
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>
              Sincronizza dati
            </Text>
          </TouchableOpacity>
        )}

        {storageInfo.items > 0 && (
          <TouchableOpacity
            style={[styles.button, styles.dangerButton]}
            onPress={handleClearData}
          >
            <Icon name="trash-outline" size={20} color={COLORS.error} />
            <Text style={[styles.buttonText, styles.dangerButtonText]}>
              Elimina dati offline
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    // Removed padding since parent card already has it
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: SPACING.md,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  online: {
    backgroundColor: COLORS.success,
  },
  offline: {
    backgroundColor: COLORS.error,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  offlineNote: {
    fontSize: 12,
    color: COLORS.warning,
    fontStyle: 'italic',
  },
  progressContainer: {
    marginBottom: SPACING.md,
  },
  progressBar: {
    height: 8,
    backgroundColor: COLORS.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: SPACING.xs,
  },
  currentItem: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: 2,
  },
  infoCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  infoLabel: {
    flex: 1,
    fontSize: 14,
    color: COLORS.textLight,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  availabilityCard: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  availabilityTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  availabilityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  availabilityText: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  actions: {
    gap: SPACING.sm,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  dangerButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: COLORS.error,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  secondaryButtonText: {
    color: COLORS.primary,
  },
  dangerButtonText: {
    color: COLORS.error,
  },
});
