import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { useLanguageStore } from '../src/store/languageStore';
import { useAuthStore } from '../src/store/authStore';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

// Legal document version for consent tracking
const LEGAL_VERSION = '1.0.0';
const LEGAL_DATE = '2026-02-14';

// Translations for Privacy & Legal page
const translations: Record<string, Record<string, string>> = {
  it: {
    title: 'Privacy e Termini',
    back: 'Indietro',
    lastUpdate: 'Ultimo aggiornamento',
    tocTitle: 'Termini e Condizioni',
    privacyTitle: 'Privacy Policy',
    consentTitle: 'Consenso e Diritti',
    aiTransparency: 'Trasparenza AI',
    dataTable: 'Dati Trattati',
    rights: 'I Tuoi Diritti',
    contact: 'Contatti',
    acceptTerms: 'Accetto i Termini e Condizioni',
    accepted: 'Accettato',
    version: 'Versione',
  },
  en: {
    title: 'Privacy & Terms',
    back: 'Back',
    lastUpdate: 'Last update',
    tocTitle: 'Terms and Conditions',
    privacyTitle: 'Privacy Policy',
    consentTitle: 'Consent and Rights',
    aiTransparency: 'AI Transparency',
    dataTable: 'Data Processed',
    rights: 'Your Rights',
    contact: 'Contact',
    acceptTerms: 'I Accept Terms and Conditions',
    accepted: 'Accepted',
    version: 'Version',
  },
  es: {
    title: 'Privacidad y Términos',
    back: 'Volver',
    lastUpdate: 'Última actualización',
    tocTitle: 'Términos y Condiciones',
    privacyTitle: 'Política de Privacidad',
    consentTitle: 'Consentimiento y Derechos',
    aiTransparency: 'Transparencia IA',
    dataTable: 'Datos Procesados',
    rights: 'Tus Derechos',
    contact: 'Contacto',
    acceptTerms: 'Acepto los Términos y Condiciones',
    accepted: 'Aceptado',
    version: 'Versión',
  },
  de: {
    title: 'Datenschutz & Bedingungen',
    back: 'Zurück',
    lastUpdate: 'Letzte Aktualisierung',
    tocTitle: 'Allgemeine Geschäftsbedingungen',
    privacyTitle: 'Datenschutzrichtlinie',
    consentTitle: 'Einwilligung und Rechte',
    aiTransparency: 'KI-Transparenz',
    dataTable: 'Verarbeitete Daten',
    rights: 'Ihre Rechte',
    contact: 'Kontakt',
    acceptTerms: 'Ich akzeptiere die AGB',
    accepted: 'Akzeptiert',
    version: 'Version',
  },
  fr: {
    title: 'Confidentialité et Conditions',
    back: 'Retour',
    lastUpdate: 'Dernière mise à jour',
    tocTitle: 'Conditions Générales',
    privacyTitle: 'Politique de Confidentialité',
    consentTitle: 'Consentement et Droits',
    aiTransparency: 'Transparence IA',
    dataTable: 'Données Traitées',
    rights: 'Vos Droits',
    contact: 'Contact',
    acceptTerms: "J'accepte les Conditions",
    accepted: 'Accepté',
    version: 'Version',
  },
  pt: {
    title: 'Privacidade e Termos',
    back: 'Voltar',
    lastUpdate: 'Última atualização',
    tocTitle: 'Termos e Condições',
    privacyTitle: 'Política de Privacidade',
    consentTitle: 'Consentimento e Direitos',
    aiTransparency: 'Transparência IA',
    dataTable: 'Dados Processados',
    rights: 'Seus Direitos',
    contact: 'Contato',
    acceptTerms: 'Aceito os Termos e Condições',
    accepted: 'Aceito',
    version: 'Versão',
  },
};

// Full legal content by language
const legalContent: Record<string, {
  toc: string[];
  privacy: string[];
  dataTable: { data: string; purpose: string; legal: string }[];
  aiInfo: string[];
  rights: string[];
}> = {
  it: {
    toc: [
      '1. DEFINIZIONI E LICENZA D\'USO',
      'L\'applicazione "Amen!" (di seguito "App") è fornita come servizio Software-as-a-Service (SaaS) dal Titolare. L\'utente ottiene una licenza d\'uso non esclusiva, non trasferibile e revocabile.',
      '',
      '2. DIVIETI ESPLICITI',
      '• Reverse Engineering: È vietata qualsiasi forma di decompilazione, disassemblaggio o tentativo di derivare il codice sorgente dell\'App.',
      '• Model Scraping: È vietato estrarre, raccogliere o replicare i modelli AI, i dataset o gli algoritmi proprietari.',
      '• Prompt Injection: Qualsiasi tentativo di manipolare le risposte AI tramite input malevoli costituisce violazione.',
      '',
      '3. CLAUSOLA DI RISOLUZIONE AUTOMATICA',
      'La violazione di qualsiasi termine comporta la risoluzione immediata della licenza d\'uso senza preavviso. Il Titolare si riserva il diritto di bloccare l\'accesso e richiedere risarcimento danni.',
      '',
      '4. SAFE HARBOR CLAUSE',
      'Il Titolare non è responsabile per l\'uso improprio dell\'App da parte dell\'utente, inclusi ma non limitati a: violazioni di copyright generate da prompt specifici, uso commerciale non autorizzato, diffusione di contenuti generati.',
      '',
      '5. LIMITAZIONE DI RESPONSABILITÀ',
      'L\'App è fornita "così com\'è". Il Titolare non garantisce l\'accuratezza teologica o storica dei contenuti generati dall\'AI. L\'utente è invitato a verificare con fonti autorevoli.',
    ],
    privacy: [
      'INFORMATIVA AI SENSI DEL REGOLAMENTO UE 2016/679 (GDPR) E EU AI ACT 2024',
      '',
      'Titolare del Trattamento:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'MODALITÀ DI TRATTAMENTO',
      'I dati sono trattati con strumenti elettronici con logiche di organizzazione correlate alle finalità. Il trattamento è effettuato in modalità "Ephemeris" (cancellazione post-sessione) salvo esplicito consenso alla conservazione.',
      '',
      'STANDARD C2PA',
      'Tutti gli asset generati dall\'AI includono metadati crittografici (Content Credentials) per garantire la provenienza sintetica e l\'attribuzione secondo lo standard Coalition for Content Provenance and Authenticity.',
      '',
      'THRESHOLD DI ORIGINALITÀ',
      'Il sistema implementa un filtro di scansione output. Se la somiglianza con opere protette supera il 15% (misurata tramite hashing percettivo e distanza di Levenshtein), la generazione viene bloccata (Error Code 403).',
    ],
    dataTable: [
      { data: 'Email', purpose: 'Autenticazione e comunicazioni', legal: 'Art. 6.1.b - Esecuzione contratto' },
      { data: 'Nome utente', purpose: 'Personalizzazione esperienza', legal: 'Art. 6.1.b - Esecuzione contratto' },
      { data: 'Preferenze lettura', purpose: 'Salvataggio progressi', legal: 'Art. 6.1.a - Consenso' },
      { data: 'Hash password (SHA-256)', purpose: 'Sicurezza accesso', legal: 'Art. 6.1.f - Legittimo interesse' },
      { data: 'Log di consenso', purpose: 'Prova accettazione T&C', legal: 'Art. 6.1.c - Obbligo legale' },
      { data: 'Prompt AI (ephemeris)', purpose: 'Elaborazione richieste', legal: 'Art. 6.1.b - Esecuzione contratto' },
    ],
    aiInfo: [
      'DICHIARAZIONE SULLA LOGICA ALGORITMICA (Art. 22 GDPR / EU AI Act)',
      '',
      'L\'App utilizza modelli di intelligenza artificiale (GPT-4o) per:',
      '• Spiegazione versetti biblici',
      '• Traduzione contenuti multilingua',
      '• Generazione quiz e contenuti educativi',
      '',
      'FUNZIONAMENTO:',
      'I modelli AI elaborano il testo di input, lo confrontano con pattern appresi durante il training e generano risposte probabilistiche. Non avviene profilazione automatizzata con effetti legali.',
      '',
      'LIMITAZIONI NOTE:',
      '• Possibili imprecisioni teologiche o storiche',
      '• Risposte basate su probabilità, non su verità assolute',
      '• Conoscenza limitata alla data di training del modello',
    ],
    rights: [
      'DIRITTI DELL\'INTERESSATO (Artt. 15-22 GDPR)',
      '',
      '• ACCESSO (Art. 15): Ottenere conferma del trattamento e copia dei dati',
      '• RETTIFICA (Art. 16): Correggere dati inesatti',
      '• CANCELLAZIONE (Art. 17): Richiedere la cancellazione ("diritto all\'oblio")',
      '• LIMITAZIONE (Art. 18): Limitare il trattamento',
      '• PORTABILITÀ (Art. 20): Ricevere i dati in formato strutturato',
      '• OPPOSIZIONE (Art. 21): Opporsi al trattamento',
      '',
      'PROCEDURA:',
      'Inviare richiesta a: andrehangar@live.it',
      'Tempo di risposta: 30 giorni',
      'Identificazione richiesta: Email registrata + conferma identità',
      '',
      'RECLAMO:',
      'È possibile proporre reclamo all\'Autorità Garante per la Protezione dei Dati Personali (www.garanteprivacy.it)',
    ],
  },
  en: {
    toc: [
      '1. DEFINITIONS AND LICENSE',
      'The "Amen!" application (hereinafter "App") is provided as a Software-as-a-Service (SaaS) by the Controller. The user obtains a non-exclusive, non-transferable, and revocable license.',
      '',
      '2. EXPLICIT PROHIBITIONS',
      '• Reverse Engineering: Any form of decompilation, disassembly, or attempt to derive the source code is prohibited.',
      '• Model Scraping: Extracting, collecting, or replicating AI models, datasets, or proprietary algorithms is prohibited.',
      '• Prompt Injection: Any attempt to manipulate AI responses through malicious inputs constitutes a violation.',
      '',
      '3. AUTOMATIC TERMINATION CLAUSE',
      'Violation of any term results in immediate license termination without notice. The Controller reserves the right to block access and seek damages.',
      '',
      '4. SAFE HARBOR CLAUSE',
      'The Controller is not liable for improper use of the App by the user, including but not limited to: copyright violations generated by specific prompts, unauthorized commercial use, distribution of generated content.',
      '',
      '5. LIMITATION OF LIABILITY',
      'The App is provided "as is". The Controller does not guarantee the theological or historical accuracy of AI-generated content. Users are advised to verify with authoritative sources.',
    ],
    privacy: [
      'PRIVACY NOTICE PURSUANT TO EU REGULATION 2016/679 (GDPR) AND EU AI ACT 2024',
      '',
      'Data Controller:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'PROCESSING METHODS',
      'Data is processed electronically with logic related to the purposes. Processing is performed in "Ephemeris" mode (post-session deletion) unless explicit consent for retention is given.',
      '',
      'C2PA STANDARD',
      'All AI-generated assets include cryptographic metadata (Content Credentials) to ensure synthetic provenance and attribution according to the Coalition for Content Provenance and Authenticity standard.',
      '',
      'ORIGINALITY THRESHOLD',
      'The system implements an output scanning filter. If similarity with protected works exceeds 15% (measured via perceptual hashing and Levenshtein distance), generation is blocked (Error Code 403).',
    ],
    dataTable: [
      { data: 'Email', purpose: 'Authentication and communications', legal: 'Art. 6.1.b - Contract performance' },
      { data: 'Username', purpose: 'Experience personalization', legal: 'Art. 6.1.b - Contract performance' },
      { data: 'Reading preferences', purpose: 'Progress saving', legal: 'Art. 6.1.a - Consent' },
      { data: 'Password hash (SHA-256)', purpose: 'Access security', legal: 'Art. 6.1.f - Legitimate interest' },
      { data: 'Consent log', purpose: 'T&C acceptance proof', legal: 'Art. 6.1.c - Legal obligation' },
      { data: 'AI prompts (ephemeris)', purpose: 'Request processing', legal: 'Art. 6.1.b - Contract performance' },
    ],
    aiInfo: [
      'ALGORITHMIC LOGIC DECLARATION (Art. 22 GDPR / EU AI Act)',
      '',
      'The App uses artificial intelligence models (GPT-4o) for:',
      '• Bible verse explanation',
      '• Multilingual content translation',
      '• Quiz and educational content generation',
      '',
      'OPERATION:',
      'AI models process input text, compare it with patterns learned during training, and generate probabilistic responses. No automated profiling with legal effects occurs.',
      '',
      'KNOWN LIMITATIONS:',
      '• Possible theological or historical inaccuracies',
      '• Responses based on probability, not absolute truth',
      '• Knowledge limited to model training date',
    ],
    rights: [
      'DATA SUBJECT RIGHTS (Arts. 15-22 GDPR)',
      '',
      '• ACCESS (Art. 15): Obtain confirmation of processing and data copy',
      '• RECTIFICATION (Art. 16): Correct inaccurate data',
      '• ERASURE (Art. 17): Request deletion ("right to be forgotten")',
      '• RESTRICTION (Art. 18): Restrict processing',
      '• PORTABILITY (Art. 20): Receive data in structured format',
      '• OBJECTION (Art. 21): Object to processing',
      '',
      'PROCEDURE:',
      'Send request to: andrehangar@live.it',
      'Response time: 30 days',
      'Identification required: Registered email + identity confirmation',
      '',
      'COMPLAINT:',
      'You may lodge a complaint with your national Data Protection Authority',
    ],
  },
  es: {
    toc: [
      '1. DEFINICIONES Y LICENCIA',
      'La aplicación "Amen!" (en adelante "App") se proporciona como Software-as-a-Service (SaaS). El usuario obtiene una licencia no exclusiva, intransferible y revocable.',
      '',
      '2. PROHIBICIONES EXPLÍCITAS',
      '• Ingeniería Inversa: Está prohibida cualquier forma de descompilación o intento de derivar el código fuente.',
      '• Model Scraping: Está prohibido extraer, recopilar o replicar modelos de IA, datasets o algoritmos propietarios.',
      '• Prompt Injection: Cualquier intento de manipular respuestas de IA mediante entradas maliciosas constituye una violación.',
      '',
      '3. CLÁUSULA DE TERMINACIÓN AUTOMÁTICA',
      'La violación de cualquier término resulta en la terminación inmediata de la licencia sin previo aviso.',
      '',
      '4. CLÁUSULA SAFE HARBOR',
      'El Titular no es responsable del uso indebido de la App por parte del usuario.',
      '',
      '5. LIMITACIÓN DE RESPONSABILIDAD',
      'La App se proporciona "tal cual". El Titular no garantiza la precisión teológica o histórica del contenido generado por IA.',
    ],
    privacy: [
      'AVISO DE PRIVACIDAD SEGÚN REGLAMENTO UE 2016/679 (GDPR) Y EU AI ACT 2024',
      '',
      'Responsable del Tratamiento:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'MÉTODOS DE PROCESAMIENTO',
      'Los datos se procesan electrónicamente en modo "Ephemeris" (eliminación post-sesión) salvo consentimiento explícito.',
      '',
      'ESTÁNDAR C2PA',
      'Todos los activos generados por IA incluyen metadatos criptográficos para garantizar la procedencia sintética.',
    ],
    dataTable: [
      { data: 'Email', purpose: 'Autenticación y comunicaciones', legal: 'Art. 6.1.b - Ejecución contrato' },
      { data: 'Nombre usuario', purpose: 'Personalización', legal: 'Art. 6.1.b - Ejecución contrato' },
      { data: 'Preferencias lectura', purpose: 'Guardar progreso', legal: 'Art. 6.1.a - Consentimiento' },
      { data: 'Hash contraseña (SHA-256)', purpose: 'Seguridad acceso', legal: 'Art. 6.1.f - Interés legítimo' },
      { data: 'Log de consentimiento', purpose: 'Prueba aceptación', legal: 'Art. 6.1.c - Obligación legal' },
      { data: 'Prompts IA (ephemeris)', purpose: 'Procesamiento solicitudes', legal: 'Art. 6.1.b - Ejecución contrato' },
    ],
    aiInfo: [
      'DECLARACIÓN DE LÓGICA ALGORÍTMICA (Art. 22 GDPR / EU AI Act)',
      '',
      'La App utiliza modelos de inteligencia artificial (GPT-4o) para:',
      '• Explicación de versículos bíblicos',
      '• Traducción de contenido multilingüe',
      '• Generación de cuestionarios y contenido educativo',
    ],
    rights: [
      'DERECHOS DEL INTERESADO (Arts. 15-22 GDPR)',
      '',
      '• ACCESO (Art. 15): Obtener confirmación del tratamiento',
      '• RECTIFICACIÓN (Art. 16): Corregir datos inexactos',
      '• SUPRESIÓN (Art. 17): Solicitar eliminación',
      '• LIMITACIÓN (Art. 18): Limitar el tratamiento',
      '• PORTABILIDAD (Art. 20): Recibir datos en formato estructurado',
      '• OPOSICIÓN (Art. 21): Oponerse al tratamiento',
      '',
      'PROCEDIMIENTO:',
      'Enviar solicitud a: andrehangar@live.it',
      'Tiempo de respuesta: 30 días',
    ],
  },
  de: {
    toc: [
      '1. DEFINITIONEN UND LIZENZ',
      'Die Anwendung "Amen!" wird als Software-as-a-Service (SaaS) bereitgestellt. Der Nutzer erhält eine nicht-exklusive, nicht übertragbare und widerrufliche Lizenz.',
      '',
      '2. AUSDRÜCKLICHE VERBOTE',
      '• Reverse Engineering: Jede Form der Dekompilierung oder des Versuchs, den Quellcode abzuleiten, ist verboten.',
      '• Model Scraping: Das Extrahieren von KI-Modellen, Datensätzen oder proprietären Algorithmen ist verboten.',
      '• Prompt Injection: Jeder Versuch, KI-Antworten durch bösartige Eingaben zu manipulieren, stellt einen Verstoß dar.',
      '',
      '3. AUTOMATISCHE KÜNDIGUNGSKLAUSEL',
      'Ein Verstoß gegen eine Bedingung führt zur sofortigen Lizenzkündigung ohne Vorankündigung.',
      '',
      '4. SAFE HARBOR KLAUSEL',
      'Der Verantwortliche haftet nicht für unsachgemäße Nutzung der App durch den Nutzer.',
      '',
      '5. HAFTUNGSBESCHRÄNKUNG',
      'Die App wird "wie besehen" bereitgestellt. Der Verantwortliche garantiert nicht die theologische oder historische Genauigkeit der KI-generierten Inhalte.',
    ],
    privacy: [
      'DATENSCHUTZHINWEIS GEMÄSS EU-VERORDNUNG 2016/679 (DSGVO) UND EU AI ACT 2024',
      '',
      'Verantwortlicher:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'VERARBEITUNGSMETHODEN',
      'Daten werden elektronisch im "Ephemeris"-Modus (Löschung nach Sitzung) verarbeitet, sofern keine ausdrückliche Einwilligung zur Aufbewahrung erteilt wird.',
      '',
      'C2PA-STANDARD',
      'Alle KI-generierten Assets enthalten kryptografische Metadaten zur Gewährleistung der synthetischen Herkunft.',
    ],
    dataTable: [
      { data: 'E-Mail', purpose: 'Authentifizierung und Kommunikation', legal: 'Art. 6.1.b - Vertragserfüllung' },
      { data: 'Benutzername', purpose: 'Personalisierung', legal: 'Art. 6.1.b - Vertragserfüllung' },
      { data: 'Leseeinstellungen', purpose: 'Fortschrittsspeicherung', legal: 'Art. 6.1.a - Einwilligung' },
      { data: 'Passwort-Hash (SHA-256)', purpose: 'Zugriffssicherheit', legal: 'Art. 6.1.f - Berechtigtes Interesse' },
      { data: 'Einwilligungsprotokoll', purpose: 'Nachweis AGB-Akzeptanz', legal: 'Art. 6.1.c - Rechtliche Verpflichtung' },
      { data: 'KI-Prompts (ephemeris)', purpose: 'Anfrageverarbeitung', legal: 'Art. 6.1.b - Vertragserfüllung' },
    ],
    aiInfo: [
      'ERKLÄRUNG ZUR ALGORITHMISCHEN LOGIK (Art. 22 DSGVO / EU AI Act)',
      '',
      'Die App verwendet KI-Modelle (GPT-4o) für:',
      '• Erklärung von Bibelversen',
      '• Mehrsprachige Inhaltsübersetzung',
      '• Quiz- und Bildungsinhalte',
    ],
    rights: [
      'BETROFFENENRECHTE (Art. 15-22 DSGVO)',
      '',
      '• AUSKUNFT (Art. 15): Bestätigung der Verarbeitung erhalten',
      '• BERICHTIGUNG (Art. 16): Unrichtige Daten korrigieren',
      '• LÖSCHUNG (Art. 17): Löschung verlangen',
      '• EINSCHRÄNKUNG (Art. 18): Verarbeitung einschränken',
      '• DATENÜBERTRAGBARKEIT (Art. 20): Daten in strukturiertem Format erhalten',
      '• WIDERSPRUCH (Art. 21): Der Verarbeitung widersprechen',
      '',
      'VERFAHREN:',
      'Anfrage senden an: andrehangar@live.it',
      'Antwortzeit: 30 Tage',
    ],
  },
  fr: {
    toc: [
      '1. DÉFINITIONS ET LICENCE',
      'L\'application "Amen!" est fournie en tant que Software-as-a-Service (SaaS). L\'utilisateur obtient une licence non exclusive, non transférable et révocable.',
      '',
      '2. INTERDICTIONS EXPLICITES',
      '• Ingénierie inverse: Toute forme de décompilation ou tentative de dériver le code source est interdite.',
      '• Model Scraping: L\'extraction de modèles IA, datasets ou algorithmes propriétaires est interdite.',
      '• Prompt Injection: Toute tentative de manipulation des réponses IA via des entrées malveillantes constitue une violation.',
      '',
      '3. CLAUSE DE RÉSILIATION AUTOMATIQUE',
      'La violation de tout terme entraîne la résiliation immédiate de la licence sans préavis.',
      '',
      '4. CLAUSE SAFE HARBOR',
      'Le Responsable n\'est pas responsable de l\'utilisation abusive de l\'App par l\'utilisateur.',
      '',
      '5. LIMITATION DE RESPONSABILITÉ',
      'L\'App est fournie "en l\'état". Le Responsable ne garantit pas l\'exactitude théologique ou historique du contenu généré par l\'IA.',
    ],
    privacy: [
      'AVIS DE CONFIDENTIALITÉ SELON LE RÈGLEMENT UE 2016/679 (RGPD) ET EU AI ACT 2024',
      '',
      'Responsable du Traitement:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'MÉTHODES DE TRAITEMENT',
      'Les données sont traitées électroniquement en mode "Ephemeris" (suppression post-session) sauf consentement explicite.',
      '',
      'STANDARD C2PA',
      'Tous les actifs générés par l\'IA incluent des métadonnées cryptographiques pour garantir la provenance synthétique.',
    ],
    dataTable: [
      { data: 'Email', purpose: 'Authentification et communications', legal: 'Art. 6.1.b - Exécution contrat' },
      { data: 'Nom utilisateur', purpose: 'Personnalisation', legal: 'Art. 6.1.b - Exécution contrat' },
      { data: 'Préférences lecture', purpose: 'Sauvegarde progression', legal: 'Art. 6.1.a - Consentement' },
      { data: 'Hash mot de passe (SHA-256)', purpose: 'Sécurité accès', legal: 'Art. 6.1.f - Intérêt légitime' },
      { data: 'Journal de consentement', purpose: 'Preuve acceptation', legal: 'Art. 6.1.c - Obligation légale' },
      { data: 'Prompts IA (ephemeris)', purpose: 'Traitement demandes', legal: 'Art. 6.1.b - Exécution contrat' },
    ],
    aiInfo: [
      'DÉCLARATION SUR LA LOGIQUE ALGORITHMIQUE (Art. 22 RGPD / EU AI Act)',
      '',
      'L\'App utilise des modèles d\'intelligence artificielle (GPT-4o) pour:',
      '• Explication de versets bibliques',
      '• Traduction de contenu multilingue',
      '• Génération de quiz et contenu éducatif',
    ],
    rights: [
      'DROITS DE LA PERSONNE CONCERNÉE (Arts. 15-22 RGPD)',
      '',
      '• ACCÈS (Art. 15): Obtenir confirmation du traitement',
      '• RECTIFICATION (Art. 16): Corriger les données inexactes',
      '• EFFACEMENT (Art. 17): Demander la suppression',
      '• LIMITATION (Art. 18): Limiter le traitement',
      '• PORTABILITÉ (Art. 20): Recevoir les données en format structuré',
      '• OPPOSITION (Art. 21): S\'opposer au traitement',
      '',
      'PROCÉDURE:',
      'Envoyer une demande à: andrehangar@live.it',
      'Délai de réponse: 30 jours',
    ],
  },
  pt: {
    toc: [
      '1. DEFINIÇÕES E LICENÇA',
      'O aplicativo "Amen!" é fornecido como Software-as-a-Service (SaaS). O usuário obtém uma licença não exclusiva, intransferível e revogável.',
      '',
      '2. PROIBIÇÕES EXPLÍCITAS',
      '• Engenharia Reversa: Qualquer forma de descompilação ou tentativa de derivar o código fonte é proibida.',
      '• Model Scraping: Extrair modelos de IA, datasets ou algoritmos proprietários é proibido.',
      '• Prompt Injection: Qualquer tentativa de manipular respostas de IA através de entradas maliciosas constitui violação.',
      '',
      '3. CLÁUSULA DE RESCISÃO AUTOMÁTICA',
      'A violação de qualquer termo resulta na rescisão imediata da licença sem aviso prévio.',
      '',
      '4. CLÁUSULA SAFE HARBOR',
      'O Responsável não é responsável pelo uso indevido do App pelo usuário.',
      '',
      '5. LIMITAÇÃO DE RESPONSABILIDADE',
      'O App é fornecido "como está". O Responsável não garante a precisão teológica ou histórica do conteúdo gerado por IA.',
    ],
    privacy: [
      'AVISO DE PRIVACIDADE NOS TERMOS DO REGULAMENTO UE 2016/679 (RGPD) E EU AI ACT 2024',
      '',
      'Responsável pelo Tratamento:',
      'Andrea Hangar',
      'Email: andrehangar@live.it',
      '',
      'MÉTODOS DE PROCESSAMENTO',
      'Os dados são processados eletronicamente em modo "Ephemeris" (exclusão pós-sessão) salvo consentimento explícito.',
      '',
      'PADRÃO C2PA',
      'Todos os ativos gerados por IA incluem metadados criptográficos para garantir a procedência sintética.',
    ],
    dataTable: [
      { data: 'Email', purpose: 'Autenticação e comunicações', legal: 'Art. 6.1.b - Execução contrato' },
      { data: 'Nome de usuário', purpose: 'Personalização', legal: 'Art. 6.1.b - Execução contrato' },
      { data: 'Preferências de leitura', purpose: 'Salvar progresso', legal: 'Art. 6.1.a - Consentimento' },
      { data: 'Hash senha (SHA-256)', purpose: 'Segurança de acesso', legal: 'Art. 6.1.f - Interesse legítimo' },
      { data: 'Log de consentimento', purpose: 'Prova de aceitação', legal: 'Art. 6.1.c - Obrigação legal' },
      { data: 'Prompts IA (ephemeris)', purpose: 'Processamento de solicitações', legal: 'Art. 6.1.b - Execução contrato' },
    ],
    aiInfo: [
      'DECLARAÇÃO SOBRE LÓGICA ALGORÍTMICA (Art. 22 RGPD / EU AI Act)',
      '',
      'O App utiliza modelos de inteligência artificial (GPT-4o) para:',
      '• Explicação de versículos bíblicos',
      '• Tradução de conteúdo multilíngue',
      '• Geração de quiz e conteúdo educativo',
    ],
    rights: [
      'DIREITOS DO TITULAR DOS DADOS (Arts. 15-22 RGPD)',
      '',
      '• ACESSO (Art. 15): Obter confirmação do tratamento',
      '• RETIFICAÇÃO (Art. 16): Corrigir dados inexatos',
      '• APAGAMENTO (Art. 17): Solicitar exclusão',
      '• LIMITAÇÃO (Art. 18): Limitar o tratamento',
      '• PORTABILIDADE (Art. 20): Receber dados em formato estruturado',
      '• OPOSIÇÃO (Art. 21): Opor-se ao tratamento',
      '',
      'PROCEDIMENTO:',
      'Enviar solicitação para: andrehangar@live.it',
      'Prazo de resposta: 30 dias',
    ],
  },
};

export default function PrivacyScreen() {
  const { currentLanguage } = useLanguageStore();
  const { user } = useAuthStore();
  const [expandedSection, setExpandedSection] = useState<string | null>('toc');
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [loading, setLoading] = useState(false);

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;
  const content = legalContent[currentLanguage] || legalContent['it'];

  useEffect(() => {
    // Check if user has already accepted terms
    checkConsentStatus();
  }, []);

  const checkConsentStatus = async () => {
    try {
      const response = await api.getConsentStatus();
      setConsentAccepted(response?.accepted || false);
    } catch (error) {
      console.log('Error checking consent:', error);
    }
  };

  const acceptTerms = async () => {
    setLoading(true);
    try {
      await api.acceptTerms(LEGAL_VERSION);
      setConsentAccepted(true);
    } catch (error) {
      console.log('Error accepting terms:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const renderSection = (title: string, sectionKey: string, content: React.ReactNode) => (
    <View style={styles.section}>
      <TouchableOpacity
        style={styles.sectionHeader}
        onPress={() => toggleSection(sectionKey)}
      >
        <Text style={styles.sectionTitle}>{title}</Text>
        <Icon
          name={expandedSection === sectionKey ? 'chevron-up' : 'chevron-down'}
          size={20}
          color={COLORS.textLight}
        />
      </TouchableOpacity>
      {expandedSection === sectionKey && (
        <View style={styles.sectionContent}>
          {content}
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('title')}</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Version Info */}
        <View style={styles.versionCard}>
          <Icon name="shield-checkmark" size={24} color={COLORS.primary} />
          <View style={styles.versionInfo}>
            <Text style={styles.versionText}>
              {t('version')}: {LEGAL_VERSION}
            </Text>
            <Text style={styles.dateText}>
              {t('lastUpdate')}: {new Date(LEGAL_DATE).toLocaleDateString(currentLanguage)}
            </Text>
          </View>
          {consentAccepted && (
            <View style={styles.acceptedBadge}>
              <Icon name="checkmark-circle" size={16} color="#fff" />
              <Text style={styles.acceptedText}>{t('accepted')}</Text>
            </View>
          )}
        </View>

        {/* Terms and Conditions */}
        {renderSection(t('tocTitle'), 'toc', (
          <View>
            {content.toc.map((line, index) => (
              <Text
                key={index}
                style={[
                  styles.legalText,
                  line.startsWith('•') && styles.bulletPoint,
                  (line.match(/^\d\./) || line === '') && styles.sectionHeading,
                ]}
              >
                {line}
              </Text>
            ))}
          </View>
        ))}

        {/* Privacy Policy */}
        {renderSection(t('privacyTitle'), 'privacy', (
          <View>
            {content.privacy.map((line, index) => (
              <Text
                key={index}
                style={[
                  styles.legalText,
                  (line.includes(':') && !line.includes('@')) && styles.sectionHeading,
                ]}
              >
                {line}
              </Text>
            ))}
          </View>
        ))}

        {/* Data Table */}
        {renderSection(t('dataTable'), 'data', (
          <View style={styles.table}>
            <View style={styles.tableHeader}>
              <Text style={[styles.tableCell, styles.tableHeaderText, { flex: 1 }]}>
                {currentLanguage === 'it' ? 'Dato' : 'Data'}
              </Text>
              <Text style={[styles.tableCell, styles.tableHeaderText, { flex: 1.5 }]}>
                {currentLanguage === 'it' ? 'Finalità' : 'Purpose'}
              </Text>
              <Text style={[styles.tableCell, styles.tableHeaderText, { flex: 1.5 }]}>
                {currentLanguage === 'it' ? 'Base Giuridica' : 'Legal Basis'}
              </Text>
            </View>
            {content.dataTable.map((row, index) => (
              <View key={index} style={[styles.tableRow, index % 2 === 0 && styles.tableRowAlt]}>
                <Text style={[styles.tableCell, { flex: 1 }]}>{row.data}</Text>
                <Text style={[styles.tableCell, { flex: 1.5 }]}>{row.purpose}</Text>
                <Text style={[styles.tableCell, styles.legalBasis, { flex: 1.5 }]}>{row.legal}</Text>
              </View>
            ))}
          </View>
        ))}

        {/* AI Transparency */}
        {renderSection(t('aiTransparency'), 'ai', (
          <View>
            {content.aiInfo.map((line, index) => (
              <Text
                key={index}
                style={[
                  styles.legalText,
                  line.startsWith('•') && styles.bulletPoint,
                  (line.includes(':') && line.length < 50) && styles.sectionHeading,
                ]}
              >
                {line}
              </Text>
            ))}
          </View>
        ))}

        {/* Rights */}
        {renderSection(t('rights'), 'rights', (
          <View>
            {content.rights.map((line, index) => (
              <Text
                key={index}
                style={[
                  styles.legalText,
                  line.startsWith('•') && styles.bulletPoint,
                  (line.includes(':') && !line.includes('@') && line.length < 50) && styles.sectionHeading,
                ]}
              >
                {line}
              </Text>
            ))}
          </View>
        ))}

        {/* Contact */}
        <View style={styles.contactCard}>
          <Icon name="mail" size={24} color={COLORS.primary} />
          <View style={styles.contactInfo}>
            <Text style={styles.contactTitle}>{t('contact')}</Text>
            <Text style={styles.contactEmail}>andrehangar@live.it</Text>
          </View>
        </View>

        {/* Accept Button */}
        {!consentAccepted && user && (
          <TouchableOpacity
            style={[styles.acceptButton, loading && styles.acceptButtonDisabled]}
            onPress={acceptTerms}
            disabled={loading}
          >
            <Icon name="checkmark-circle" size={20} color="#fff" />
            <Text style={styles.acceptButtonText}>{t('acceptTerms')}</Text>
          </TouchableOpacity>
        )}

        <View style={styles.bottomPadding} />
      </ScrollView>
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
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  backButton: {
    padding: SPACING.xs,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  placeholder: {
    width: 32,
  },
  content: {
    flex: 1,
    padding: SPACING.md,
  },
  versionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  versionInfo: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  versionText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  dateText: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  acceptedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.success,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
  },
  acceptedText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 4,
  },
  section: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.md,
    overflow: 'hidden',
    ...SHADOWS.small,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  sectionContent: {
    padding: SPACING.md,
  },
  legalText: {
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.textLight,
    marginBottom: 8,
  },
  bulletPoint: {
    paddingLeft: SPACING.md,
    color: COLORS.text,
  },
  sectionHeading: {
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 8,
  },
  table: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    overflow: 'hidden',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary + '20',
    paddingVertical: SPACING.sm,
  },
  tableHeaderText: {
    fontWeight: '600',
    color: COLORS.text,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  tableRowAlt: {
    backgroundColor: COLORS.background,
  },
  tableCell: {
    fontSize: 11,
    color: COLORS.textLight,
    paddingHorizontal: SPACING.xs,
  },
  legalBasis: {
    fontSize: 10,
    fontStyle: 'italic',
  },
  contactCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  contactInfo: {
    marginLeft: SPACING.md,
  },
  contactTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  contactEmail: {
    fontSize: 14,
    color: COLORS.primary,
    marginTop: 2,
  },
  acceptButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.medium,
  },
  acceptButtonDisabled: {
    opacity: 0.6,
  },
  acceptButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginLeft: SPACING.sm,
  },
  bottomPadding: {
    height: 40,
  },
});
