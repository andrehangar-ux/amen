import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { COLORS } from '../utils/theme';
import { useLanguageStore } from '../store/languageStore';
import { api } from '../utils/api';
import { FontAwesome5 } from '@expo/vector-icons';

const TERMS_VERSION = '1.0';

// Translations for the modal
const modalTranslations: Record<string, Record<string, string>> = {
  it: {
    title: 'Termini e Condizioni',
    subtitle: 'Prima di continuare, leggi e accetta i nostri termini',
    termsIntro: 'Utilizzando Amen!, accetti i seguenti termini:',
    term1: 'Trattamento dei dati personali secondo il GDPR',
    term2: 'Uso dei cookie per migliorare l\'esperienza',
    term3: 'Rispetto delle linee guida della community',
    term4: 'Nessuna condivisione dei tuoi dati con terze parti senza consenso',
    privacyTitle: 'Privacy',
    privacyText: 'I tuoi dati sono al sicuro. Puoi richiedere la cancellazione in qualsiasi momento dalla sezione Profilo.',
    acceptButton: 'Accetto i Termini e Condizioni',
    readFull: 'Leggi i termini completi',
    loading: 'Caricamento...',
    error: 'Errore nel salvataggio. Riprova.',
  },
  es: {
    title: 'Términos y Condiciones',
    subtitle: 'Antes de continuar, lee y acepta nuestros términos',
    termsIntro: 'Al usar Amen!, aceptas los siguientes términos:',
    term1: 'Tratamiento de datos personales según el GDPR',
    term2: 'Uso de cookies para mejorar la experiencia',
    term3: 'Respeto de las directrices de la comunidad',
    term4: 'Sin compartir tus datos con terceros sin consentimiento',
    privacyTitle: 'Privacidad',
    privacyText: 'Tus datos están seguros. Puedes solicitar la eliminación en cualquier momento desde la sección Perfil.',
    acceptButton: 'Acepto los Términos y Condiciones',
    readFull: 'Leer términos completos',
    loading: 'Cargando...',
    error: 'Error al guardar. Inténtalo de nuevo.',
  },
  en: {
    title: 'Terms and Conditions',
    subtitle: 'Before continuing, please read and accept our terms',
    termsIntro: 'By using Amen!, you agree to the following terms:',
    term1: 'Processing of personal data according to GDPR',
    term2: 'Use of cookies to improve your experience',
    term3: 'Respect for community guidelines',
    term4: 'No sharing of your data with third parties without consent',
    privacyTitle: 'Privacy',
    privacyText: 'Your data is safe. You can request deletion at any time from the Profile section.',
    acceptButton: 'I Accept the Terms and Conditions',
    readFull: 'Read full terms',
    loading: 'Loading...',
    error: 'Error saving. Please try again.',
  },
  pt: {
    title: 'Termos e Condições',
    subtitle: 'Antes de continuar, leia e aceite nossos termos',
    termsIntro: 'Ao usar o Amen!, você concorda com os seguintes termos:',
    term1: 'Tratamento de dados pessoais de acordo com o GDPR',
    term2: 'Uso de cookies para melhorar a experiência',
    term3: 'Respeito às diretrizes da comunidade',
    term4: 'Sem compartilhamento de seus dados com terceiros sem consentimento',
    privacyTitle: 'Privacidade',
    privacyText: 'Seus dados estão seguros. Você pode solicitar a exclusão a qualquer momento na seção Perfil.',
    acceptButton: 'Aceito os Termos e Condições',
    readFull: 'Ler termos completos',
    loading: 'Carregando...',
    error: 'Erro ao salvar. Tente novamente.',
  },
  fr: {
    title: 'Conditions Générales',
    subtitle: 'Avant de continuer, veuillez lire et accepter nos conditions',
    termsIntro: 'En utilisant Amen!, vous acceptez les conditions suivantes:',
    term1: 'Traitement des données personnelles selon le RGPD',
    term2: 'Utilisation de cookies pour améliorer l\'expérience',
    term3: 'Respect des directives de la communauté',
    term4: 'Aucun partage de vos données avec des tiers sans consentement',
    privacyTitle: 'Confidentialité',
    privacyText: 'Vos données sont en sécurité. Vous pouvez demander la suppression à tout moment depuis la section Profil.',
    acceptButton: 'J\'accepte les Conditions Générales',
    readFull: 'Lire les conditions complètes',
    loading: 'Chargement...',
    error: 'Erreur lors de l\'enregistrement. Veuillez réessayer.',
  },
  de: {
    title: 'Allgemeine Geschäftsbedingungen',
    subtitle: 'Bevor Sie fortfahren, lesen und akzeptieren Sie bitte unsere Bedingungen',
    termsIntro: 'Durch die Nutzung von Amen! stimmen Sie den folgenden Bedingungen zu:',
    term1: 'Verarbeitung personenbezogener Daten gemäß DSGVO',
    term2: 'Verwendung von Cookies zur Verbesserung der Erfahrung',
    term3: 'Einhaltung der Community-Richtlinien',
    term4: 'Keine Weitergabe Ihrer Daten an Dritte ohne Zustimmung',
    privacyTitle: 'Datenschutz',
    privacyText: 'Ihre Daten sind sicher. Sie können jederzeit im Profil-Bereich die Löschung beantragen.',
    acceptButton: 'Ich akzeptiere die AGB',
    readFull: 'Vollständige Bedingungen lesen',
    loading: 'Laden...',
    error: 'Fehler beim Speichern. Bitte versuchen Sie es erneut.',
  },
};

interface TermsModalProps {
  visible: boolean;
  onAccept: () => void;
}

export const TermsModal: React.FC<TermsModalProps> = ({ visible, onAccept }) => {
  const { currentLanguage } = useLanguageStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const t = modalTranslations[currentLanguage] || modalTranslations.it;

  const handleAccept = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await api.acceptTerms(TERMS_VERSION);
      onAccept();
    } catch (err) {
      setError(t.error);
    } finally {
      setIsLoading(false);
    }
  };

  const openFullTerms = () => {
    // Link to a full terms page (could be configured)
    Linking.openURL('https://www.iubenda.com/privacy-policy/example');
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={false}
      statusBarTranslucent
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <FontAwesome5 name="shield-alt" size={48} color={COLORS.primary} />
          <Text style={styles.title}>{t.title}</Text>
          <Text style={styles.subtitle}>{t.subtitle}</Text>
        </View>

        <ScrollView 
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.introText}>{t.termsIntro}</Text>
          
          <View style={styles.termItem}>
            <FontAwesome5 name="check-circle" size={20} color={COLORS.success} style={styles.termIcon} />
            <Text style={styles.termText}>{t.term1}</Text>
          </View>
          
          <View style={styles.termItem}>
            <FontAwesome5 name="check-circle" size={20} color={COLORS.success} style={styles.termIcon} />
            <Text style={styles.termText}>{t.term2}</Text>
          </View>
          
          <View style={styles.termItem}>
            <FontAwesome5 name="check-circle" size={20} color={COLORS.success} style={styles.termIcon} />
            <Text style={styles.termText}>{t.term3}</Text>
          </View>
          
          <View style={styles.termItem}>
            <FontAwesome5 name="check-circle" size={20} color={COLORS.success} style={styles.termIcon} />
            <Text style={styles.termText}>{t.term4}</Text>
          </View>

          <View style={styles.privacyBox}>
            <FontAwesome5 name="lock" size={24} color={COLORS.primary} />
            <View style={styles.privacyContent}>
              <Text style={styles.privacyTitle}>{t.privacyTitle}</Text>
              <Text style={styles.privacyText}>{t.privacyText}</Text>
            </View>
          </View>

          <TouchableOpacity 
            style={styles.readMoreLink}
            onPress={openFullTerms}
          >
            <FontAwesome5 name="external-link-alt" size={14} color={COLORS.primary} />
            <Text style={styles.readMoreText}>{t.readFull}</Text>
          </TouchableOpacity>
        </ScrollView>

        <View style={styles.footer}>
          {error && <Text style={styles.errorText}>{error}</Text>}
          
          <TouchableOpacity
            style={[styles.acceptButton, isLoading && styles.acceptButtonDisabled]}
            onPress={handleAccept}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <FontAwesome5 name="check" size={18} color="#fff" style={styles.acceptIcon} />
                <Text style={styles.acceptButtonText}>{t.acceptButton}</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    alignItems: 'center',
    paddingTop: 60,
    paddingBottom: 24,
    paddingHorizontal: 24,
    backgroundColor: COLORS.surface,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 16,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginTop: 8,
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 24,
  },
  introText: {
    fontSize: 16,
    color: COLORS.text,
    lineHeight: 24,
    marginBottom: 20,
  },
  termItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    backgroundColor: COLORS.surface,
    padding: 16,
    borderRadius: 12,
  },
  termIcon: {
    marginRight: 12,
    marginTop: 2,
  },
  termText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 22,
  },
  privacyBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.primaryLight + '20',
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  privacyContent: {
    flex: 1,
    marginLeft: 12,
  },
  privacyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  privacyText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  readMoreLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
  },
  readMoreText: {
    fontSize: 14,
    color: COLORS.primary,
    marginLeft: 8,
    textDecorationLine: 'underline',
  },
  footer: {
    padding: 24,
    paddingBottom: 40,
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  errorText: {
    color: COLORS.error,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  acceptButton: {
    backgroundColor: COLORS.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  acceptButtonDisabled: {
    opacity: 0.7,
  },
  acceptIcon: {
    marginRight: 10,
  },
  acceptButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
});

export default TermsModal;
