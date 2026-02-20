# Quiz 1000 - Nuove categorie di quiz biblici
# 1000 domande organizzate in 33 sottocategorie tematiche

import json
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load questions from JSON files
DATA_FILE = Path(__file__).parent / 'quiz_categories_data.json'
ADVANCED_DATA_FILE = Path(__file__).parent / 'quiz_advanced_data.json'
ADVANCED_SUBCATEGORIES_FILE = Path(__file__).parent / 'quiz_advanced_subcategories.json'
ADVANCED_TRANSLATIONS_FILE = Path(__file__).parent / 'quiz_advanced_translations.json'
TRANSLATIONS_CACHE_FILE = Path(__file__).parent / 'quiz_translations_cache.json'

def load_quiz_categories():
    """Load quiz categories from JSON files"""
    categories = {}
    
    # Load main categories
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            categories.update(json.load(f))
    
    # Load advanced categories
    if ADVANCED_DATA_FILE.exists():
        with open(ADVANCED_DATA_FILE, 'r', encoding='utf-8') as f:
            categories.update(json.load(f))
    
    return categories

def load_translations_cache():
    """Load cached translations"""
    if TRANSLATIONS_CACHE_FILE.exists():
        with open(TRANSLATIONS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_translations_cache(cache):
    """Save translations to cache file"""
    with open(TRANSLATIONS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# Translation cache
_translations_cache = None

def get_translations_cache():
    global _translations_cache
    if _translations_cache is None:
        _translations_cache = load_translations_cache()
    return _translations_cache

async def translate_question(question: dict, target_lang: str) -> dict:
    """Translate a single question using OpenAI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    
    lang_names = {
        'es': 'Spanish', 'en': 'English', 'de': 'German', 
        'fr': 'French', 'pt': 'Portuguese'
    }
    
    # Check cache first
    cache = get_translations_cache()
    cache_key = f"{question['id']}_{target_lang}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate_{question['id']}_{target_lang}",
            system_message=f"Translate the following Bible quiz from Italian to {lang_names.get(target_lang, 'English')}. Return JSON with keys: question, options (array of 4), explanation. Keep biblical names in their common form."
        ).with_model("openai", "gpt-4o")
        
        text = f"""Question: {question['question']}
Options: {json.dumps(question['options'], ensure_ascii=False)}
Explanation: {question['explanation']}"""
        
        response = await chat.send_message(UserMessage(text=text))
        
        # Parse JSON response
        # Find JSON in response
        import re
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            translated = json.loads(json_match.group())
        else:
            # Try parsing entire response as JSON
            translated = json.loads(response)
        
        result = {
            'id': question['id'],
            'question': translated.get('question', question['question']),
            'options': translated.get('options', question['options']),
            'correct': question['correct'],
            'explanation': translated.get('explanation', question['explanation']),
            'verse_ref': question.get('verse_ref', '')
        }
        
        # Cache the result
        cache[cache_key] = result
        save_translations_cache(cache)
        
        return result
        
    except Exception as e:
        print(f"Translation error for {question['id']}: {e}")
        # Return original on error
        return question

# Category metadata with translations
CATEGORY_TRANSLATIONS = {
    'canone_bibbia': {
        'it': {'title': 'Formazione del Canone', 'desc': 'Come si è formata la Bibbia'},
        'es': {'title': 'Formación del Canon', 'desc': 'Cómo se formó la Biblia'},
        'en': {'title': 'Canon Formation', 'desc': 'How the Bible was formed'},
        'pt': {'title': 'Formação do Cânon', 'desc': 'Como a Bíblia foi formada'},
        'fr': {'title': 'Formation du Canon', 'desc': 'Comment la Bible a été formée'},
        'de': {'title': 'Kanonbildung', 'desc': 'Wie die Bibel entstand'},
    },
    'manoscritti': {
        'it': {'title': 'Manoscritti e Traduzioni', 'desc': 'Trasmissione del testo biblico'},
        'es': {'title': 'Manuscritos y Traducciones', 'desc': 'Transmisión del texto bíblico'},
        'en': {'title': 'Manuscripts and Translations', 'desc': 'Biblical text transmission'},
        'pt': {'title': 'Manuscritos e Traduções', 'desc': 'Transmissão do texto bíblico'},
        'fr': {'title': 'Manuscrits et Traductions', 'desc': 'Transmission du texte biblique'},
        'de': {'title': 'Handschriften und Übersetzungen', 'desc': 'Überlieferung des Bibeltextes'},
    },
    'creazione': {
        'it': {'title': 'La Creazione', 'desc': 'Genesi 1-4: le origini'},
        'es': {'title': 'La Creación', 'desc': 'Génesis 1-4: los orígenes'},
        'en': {'title': 'The Creation', 'desc': 'Genesis 1-4: the origins'},
        'pt': {'title': 'A Criação', 'desc': 'Gênesis 1-4: as origens'},
        'fr': {'title': 'La Création', 'desc': 'Genèse 1-4: les origines'},
        'de': {'title': 'Die Schöpfung', 'desc': 'Genesis 1-4: die Ursprünge'},
    },
    'patriarchi_1': {
        'it': {'title': 'Noè e il Diluvio', 'desc': 'Genesi 6-11: il nuovo inizio'},
        'es': {'title': 'Noé y el Diluvio', 'desc': 'Génesis 6-11: el nuevo comienzo'},
        'en': {'title': 'Noah and the Flood', 'desc': 'Genesis 6-11: a new beginning'},
        'pt': {'title': 'Noé e o Dilúvio', 'desc': 'Gênesis 6-11: um novo começo'},
        'fr': {'title': 'Noé et le Déluge', 'desc': 'Genèse 6-11: un nouveau départ'},
        'de': {'title': 'Noah und die Sintflut', 'desc': 'Genesis 6-11: ein Neuanfang'},
    },
    'patriarchi_2': {
        'it': {'title': 'Abramo', 'desc': 'Il padre della fede'},
        'es': {'title': 'Abraham', 'desc': 'El padre de la fe'},
        'en': {'title': 'Abraham', 'desc': 'The father of faith'},
        'pt': {'title': 'Abraão', 'desc': 'O pai da fé'},
        'fr': {'title': 'Abraham', 'desc': 'Le père de la foi'},
        'de': {'title': 'Abraham', 'desc': 'Der Vater des Glaubens'},
    },
    'patriarchi_3': {
        'it': {'title': 'Giacobbe e Giuseppe', 'desc': 'Da Canaan all\'Egitto'},
        'es': {'title': 'Jacob y José', 'desc': 'De Canaán a Egipto'},
        'en': {'title': 'Jacob and Joseph', 'desc': 'From Canaan to Egypt'},
        'pt': {'title': 'Jacó e José', 'desc': 'De Canaã ao Egito'},
        'fr': {'title': 'Jacob et Joseph', 'desc': 'De Canaan à l\'Égypte'},
        'de': {'title': 'Jakob und Josef', 'desc': 'Von Kanaan nach Ägypten'},
    },
    'esodo_liberazione': {
        'it': {'title': 'L\'Esodo', 'desc': 'La liberazione dall\'Egitto'},
        'es': {'title': 'El Éxodo', 'desc': 'La liberación de Egipto'},
        'en': {'title': 'The Exodus', 'desc': 'Liberation from Egypt'},
        'pt': {'title': 'O Êxodo', 'desc': 'A libertação do Egito'},
        'fr': {'title': 'L\'Exode', 'desc': 'La libération d\'Égypte'},
        'de': {'title': 'Der Exodus', 'desc': 'Die Befreiung aus Ägypten'},
    },
    'legge': {
        'it': {'title': 'La Torah', 'desc': 'La Legge di Mosè'},
        'es': {'title': 'La Torá', 'desc': 'La Ley de Moisés'},
        'en': {'title': 'The Torah', 'desc': 'The Law of Moses'},
        'pt': {'title': 'A Torá', 'desc': 'A Lei de Moisés'},
        'fr': {'title': 'La Torah', 'desc': 'La Loi de Moïse'},
        'de': {'title': 'Die Tora', 'desc': 'Das Gesetz des Mose'},
    },
    'alleanza_teologia': {
        'it': {'title': 'L\'Alleanza', 'desc': 'Il Patto con Dio'},
        'es': {'title': 'La Alianza', 'desc': 'El Pacto con Dios'},
        'en': {'title': 'The Covenant', 'desc': 'The Pact with God'},
        'pt': {'title': 'A Aliança', 'desc': 'O Pacto com Deus'},
        'fr': {'title': 'L\'Alliance', 'desc': 'Le Pacte avec Dieu'},
        'de': {'title': 'Der Bund', 'desc': 'Der Pakt mit Gott'},
    },
    'conquista_giudici': {
        'it': {'title': 'Conquista e Giudici', 'desc': 'Dalla conquista ai Giudici'},
        'es': {'title': 'Conquista y Jueces', 'desc': 'De la conquista a los Jueces'},
        'en': {'title': 'Conquest and Judges', 'desc': 'From conquest to the Judges'},
        'pt': {'title': 'Conquista e Juízes', 'desc': 'Da conquista aos Juízes'},
        'fr': {'title': 'Conquête et Juges', 'desc': 'De la conquête aux Juges'},
        'de': {'title': 'Eroberung und Richter', 'desc': 'Von der Eroberung bis zu den Richtern'},
    },
    'sansone_samuele': {
        'it': {'title': 'Sansone e Samuele', 'desc': 'Gli ultimi Giudici'},
        'es': {'title': 'Sansón y Samuel', 'desc': 'Los últimos Jueces'},
        'en': {'title': 'Samson and Samuel', 'desc': 'The last Judges'},
        'pt': {'title': 'Sansão e Samuel', 'desc': 'Os últimos Juízes'},
        'fr': {'title': 'Samson et Samuel', 'desc': 'Les derniers Juges'},
        'de': {'title': 'Simson und Samuel', 'desc': 'Die letzten Richter'},
    },
    'saul_davide': {
        'it': {'title': 'Saul e Davide', 'desc': 'I primi re'},
        'es': {'title': 'Saúl y David', 'desc': 'Los primeros reyes'},
        'en': {'title': 'Saul and David', 'desc': 'The first kings'},
        'pt': {'title': 'Saul e Davi', 'desc': 'Os primeiros reis'},
        'fr': {'title': 'Saül et David', 'desc': 'Les premiers rois'},
        'de': {'title': 'Saul und David', 'desc': 'Die ersten Könige'},
    },
    'salomone_tempio': {
        'it': {'title': 'Salomone', 'desc': 'Il re saggio e il Tempio'},
        'es': {'title': 'Salomón', 'desc': 'El rey sabio y el Templo'},
        'en': {'title': 'Solomon', 'desc': 'The wise king and the Temple'},
        'pt': {'title': 'Salomão', 'desc': 'O rei sábio e o Templo'},
        'fr': {'title': 'Salomon', 'desc': 'Le roi sage et le Temple'},
        'de': {'title': 'Salomo', 'desc': 'Der weise König und der Tempel'},
    },
    'regni_scisma': {
        'it': {'title': 'Lo Scisma', 'desc': 'La divisione del Regno'},
        'es': {'title': 'El Cisma', 'desc': 'La división del Reino'},
        'en': {'title': 'The Schism', 'desc': 'The division of the Kingdom'},
        'pt': {'title': 'O Cisma', 'desc': 'A divisão do Reino'},
        'fr': {'title': 'Le Schisme', 'desc': 'La division du Royaume'},
        'de': {'title': 'Das Schisma', 'desc': 'Die Teilung des Reiches'},
    },
    'profeti_nord': {
        'it': {'title': 'Elia ed Eliseo', 'desc': 'I profeti del Nord'},
        'es': {'title': 'Elías y Eliseo', 'desc': 'Los profetas del Norte'},
        'en': {'title': 'Elijah and Elisha', 'desc': 'The prophets of the North'},
        'pt': {'title': 'Elias e Eliseu', 'desc': 'Os profetas do Norte'},
        'fr': {'title': 'Élie et Élisée', 'desc': 'Les prophètes du Nord'},
        'de': {'title': 'Elia und Elisa', 'desc': 'Die Propheten des Nordens'},
    },
    'profeti_isaia': {
        'it': {'title': 'Isaia', 'desc': 'Il profeta della consolazione'},
        'es': {'title': 'Isaías', 'desc': 'El profeta de la consolación'},
        'en': {'title': 'Isaiah', 'desc': 'The prophet of consolation'},
        'pt': {'title': 'Isaías', 'desc': 'O profeta da consolação'},
        'fr': {'title': 'Isaïe', 'desc': 'Le prophète de la consolation'},
        'de': {'title': 'Jesaja', 'desc': 'Der Prophet des Trostes'},
    },
    'profeti_geremia': {
        'it': {'title': 'Geremia', 'desc': 'Il profeta delle lacrime'},
        'es': {'title': 'Jeremías', 'desc': 'El profeta de las lágrimas'},
        'en': {'title': 'Jeremiah', 'desc': 'The weeping prophet'},
        'pt': {'title': 'Jeremias', 'desc': 'O profeta das lágrimas'},
        'fr': {'title': 'Jérémie', 'desc': 'Le prophète des larmes'},
        'de': {'title': 'Jeremia', 'desc': 'Der weinende Prophet'},
    },
    'profeti_ezechiele_daniele': {
        'it': {'title': 'Ezechiele e Daniele', 'desc': 'Profeti dell\'esilio'},
        'es': {'title': 'Ezequiel y Daniel', 'desc': 'Profetas del exilio'},
        'en': {'title': 'Ezekiel and Daniel', 'desc': 'Prophets of the exile'},
        'pt': {'title': 'Ezequiel e Daniel', 'desc': 'Profetas do exílio'},
        'fr': {'title': 'Ézéchiel et Daniel', 'desc': 'Prophètes de l\'exil'},
        'de': {'title': 'Hesekiel und Daniel', 'desc': 'Propheten des Exils'},
    },
    'profeti_minori': {
        'it': {'title': 'Profeti Minori', 'desc': 'I Dodici'},
        'es': {'title': 'Profetas Menores', 'desc': 'Los Doce'},
        'en': {'title': 'Minor Prophets', 'desc': 'The Twelve'},
        'pt': {'title': 'Profetas Menores', 'desc': 'Os Doze'},
        'fr': {'title': 'Petits Prophètes', 'desc': 'Les Douze'},
        'de': {'title': 'Kleine Propheten', 'desc': 'Die Zwölf'},
    },
    'esilio_ritorno': {
        'it': {'title': 'Esilio e Ritorno', 'desc': 'La cattività babilonese'},
        'es': {'title': 'Exilio y Regreso', 'desc': 'El cautiverio babilónico'},
        'en': {'title': 'Exile and Return', 'desc': 'The Babylonian captivity'},
        'pt': {'title': 'Exílio e Retorno', 'desc': 'O cativeiro babilônico'},
        'fr': {'title': 'Exil et Retour', 'desc': 'La captivité babylonienne'},
        'de': {'title': 'Exil und Rückkehr', 'desc': 'Die babylonische Gefangenschaft'},
    },
    'salmi_sapienza': {
        'it': {'title': 'Salmi e Sapienza', 'desc': 'Poesia e riflessione'},
        'es': {'title': 'Salmos y Sabiduría', 'desc': 'Poesía y reflexión'},
        'en': {'title': 'Psalms and Wisdom', 'desc': 'Poetry and reflection'},
        'pt': {'title': 'Salmos e Sabedoria', 'desc': 'Poesia e reflexão'},
        'fr': {'title': 'Psaumes et Sagesse', 'desc': 'Poésie et réflexion'},
        'de': {'title': 'Psalmen und Weisheit', 'desc': 'Poesie und Reflexion'},
    },
    'donne_bibbia': {
        'it': {'title': 'Donne della Bibbia', 'desc': 'Figure femminili'},
        'es': {'title': 'Mujeres de la Biblia', 'desc': 'Figuras femeninas'},
        'en': {'title': 'Women of the Bible', 'desc': 'Female figures'},
        'pt': {'title': 'Mulheres da Bíblia', 'desc': 'Figuras femininas'},
        'fr': {'title': 'Femmes de la Bible', 'desc': 'Figures féminines'},
        'de': {'title': 'Frauen der Bibel', 'desc': 'Weibliche Gestalten'},
    },
    'gesu_vita': {
        'it': {'title': 'La Vita di Gesù', 'desc': 'Dall\'infanzia al ministero'},
        'es': {'title': 'La Vida de Jesús', 'desc': 'De la infancia al ministerio'},
        'en': {'title': 'The Life of Jesus', 'desc': 'From childhood to ministry'},
        'pt': {'title': 'A Vida de Jesus', 'desc': 'Da infância ao ministério'},
        'fr': {'title': 'La Vie de Jésus', 'desc': 'De l\'enfance au ministère'},
        'de': {'title': 'Das Leben Jesu', 'desc': 'Von der Kindheit zum Dienst'},
    },
    'vangeli': {
        'it': {'title': 'I Vangeli', 'desc': 'I quattro evangelisti'},
        'es': {'title': 'Los Evangelios', 'desc': 'Los cuatro evangelistas'},
        'en': {'title': 'The Gospels', 'desc': 'The four evangelists'},
        'pt': {'title': 'Os Evangelhos', 'desc': 'Os quatro evangelistas'},
        'fr': {'title': 'Les Évangiles', 'desc': 'Les quatre évangélistes'},
        'de': {'title': 'Die Evangelien', 'desc': 'Die vier Evangelisten'},
    },
    'miracoli_parabole': {
        'it': {'title': 'Miracoli e Parabole', 'desc': 'L\'insegnamento di Gesù'},
        'es': {'title': 'Milagros y Parábolas', 'desc': 'La enseñanza de Jesús'},
        'en': {'title': 'Miracles and Parables', 'desc': 'The teaching of Jesus'},
        'pt': {'title': 'Milagres e Parábolas', 'desc': 'O ensino de Jesus'},
        'fr': {'title': 'Miracles et Paraboles', 'desc': 'L\'enseignement de Jésus'},
        'de': {'title': 'Wunder und Gleichnisse', 'desc': 'Die Lehre Jesu'},
    },
    'passione': {
        'it': {'title': 'Passione e Risurrezione', 'desc': 'La Pasqua del Signore'},
        'es': {'title': 'Pasión y Resurrección', 'desc': 'La Pascua del Señor'},
        'en': {'title': 'Passion and Resurrection', 'desc': 'The Lord\'s Easter'},
        'pt': {'title': 'Paixão e Ressurreição', 'desc': 'A Páscoa do Senhor'},
        'fr': {'title': 'Passion et Résurrection', 'desc': 'La Pâques du Seigneur'},
        'de': {'title': 'Passion und Auferstehung', 'desc': 'Ostern des Herrn'},
    },
    'atti_chiesa': {
        'it': {'title': 'La Chiesa Nascente', 'desc': 'Gli Atti degli Apostoli'},
        'es': {'title': 'La Iglesia Naciente', 'desc': 'Los Hechos de los Apóstoles'},
        'en': {'title': 'The Early Church', 'desc': 'The Acts of the Apostles'},
        'pt': {'title': 'A Igreja Nascente', 'desc': 'Os Atos dos Apóstolos'},
        'fr': {'title': 'L\'Église Naissante', 'desc': 'Les Actes des Apôtres'},
        'de': {'title': 'Die frühe Kirche', 'desc': 'Die Apostelgeschichte'},
    },
    'paolo': {
        'it': {'title': 'L\'Apostolo Paolo', 'desc': 'Missioni e Lettere'},
        'es': {'title': 'El Apóstol Pablo', 'desc': 'Misiones y Cartas'},
        'en': {'title': 'The Apostle Paul', 'desc': 'Missions and Letters'},
        'pt': {'title': 'O Apóstolo Paulo', 'desc': 'Missões e Cartas'},
        'fr': {'title': 'L\'Apôtre Paul', 'desc': 'Missions et Lettres'},
        'de': {'title': 'Der Apostel Paulus', 'desc': 'Missionen und Briefe'},
    },
    'apocalisse': {
        'it': {'title': 'Apocalisse', 'desc': 'La Rivelazione'},
        'es': {'title': 'Apocalipsis', 'desc': 'La Revelación'},
        'en': {'title': 'Revelation', 'desc': 'The Apocalypse'},
        'pt': {'title': 'Apocalipse', 'desc': 'A Revelação'},
        'fr': {'title': 'Apocalypse', 'desc': 'La Révélation'},
        'de': {'title': 'Offenbarung', 'desc': 'Die Apokalypse'},
    },
    'lingue_termini': {
        'it': {'title': 'Lingue e Termini', 'desc': 'Terminologia biblica'},
        'es': {'title': 'Lenguas y Términos', 'desc': 'Terminología bíblica'},
        'en': {'title': 'Languages and Terms', 'desc': 'Biblical terminology'},
        'pt': {'title': 'Línguas e Termos', 'desc': 'Terminologia bíblica'},
        'fr': {'title': 'Langues et Termes', 'desc': 'Terminologie biblique'},
        'de': {'title': 'Sprachen und Begriffe', 'desc': 'Biblische Terminologie'},
    },
    'feste_culto': {
        'it': {'title': 'Feste e Culto', 'desc': 'Celebrazioni e liturgia'},
        'es': {'title': 'Fiestas y Culto', 'desc': 'Celebraciones y liturgia'},
        'en': {'title': 'Feasts and Worship', 'desc': 'Celebrations and liturgy'},
        'pt': {'title': 'Festas e Culto', 'desc': 'Celebrações e liturgia'},
        'fr': {'title': 'Fêtes et Culte', 'desc': 'Célébrations et liturgie'},
        'de': {'title': 'Feste und Gottesdienst', 'desc': 'Feiern und Liturgie'},
    },
    'storia_geografia': {
        'it': {'title': 'Storia e Luoghi', 'desc': 'Geografia e archeologia'},
        'es': {'title': 'Historia y Lugares', 'desc': 'Geografía y arqueología'},
        'en': {'title': 'History and Places', 'desc': 'Geography and archaeology'},
        'pt': {'title': 'História e Lugares', 'desc': 'Geografia e arqueologia'},
        'fr': {'title': 'Histoire et Lieux', 'desc': 'Géographie et archéologie'},
        'de': {'title': 'Geschichte und Orte', 'desc': 'Geographie und Archäologie'},
    },
    'teologia_generale': {
        'it': {'title': 'Teologia Biblica', 'desc': 'Concetti fondamentali'},
        'es': {'title': 'Teología Bíblica', 'desc': 'Conceptos fundamentales'},
        'en': {'title': 'Biblical Theology', 'desc': 'Fundamental concepts'},
        'pt': {'title': 'Teologia Bíblica', 'desc': 'Conceitos fundamentais'},
        'fr': {'title': 'Théologie Biblique', 'desc': 'Concepts fondamentaux'},
        'de': {'title': 'Biblische Theologie', 'desc': 'Grundlegende Konzepte'},
    },
    'studio_avanzato': {
        'it': {'title': 'Studio Biblico Avanzato', 'desc': '100 domande di critica testuale ed esegesi'},
        'es': {'title': 'Estudio Bíblico Avanzado', 'desc': '100 preguntas de crítica textual y exégesis'},
        'en': {'title': 'Advanced Bible Study', 'desc': '100 questions on textual criticism and exegesis'},
        'pt': {'title': 'Estudo Bíblico Avançado', 'desc': '100 questões de crítica textual e exegese'},
        'fr': {'title': 'Étude Biblique Avancée', 'desc': '100 questions de critique textuelle et exégèse'},
        'de': {'title': 'Fortgeschrittenes Bibelstudium', 'desc': '100 Fragen zur Textkritik und Exegese'},
    },
}

# Translations for advanced subcategories
ADVANCED_SUBCATEGORY_TRANSLATIONS = {
    'critica_testuale': {
        'it': {'title': 'Critica Testuale', 'desc': 'Manoscritti, codici e varianti testuali'},
        'es': {'title': 'Critica Textual', 'desc': 'Manuscritos, codices y variantes textuales'},
        'en': {'title': 'Textual Criticism', 'desc': 'Manuscripts, codices and textual variants'},
        'pt': {'title': 'Critica Textual', 'desc': 'Manuscritos, codices e variantes textuais'},
        'fr': {'title': 'Critique Textuelle', 'desc': 'Manuscrits, codex et variantes textuelles'},
        'de': {'title': 'Textkritik', 'desc': 'Handschriften, Kodizes und Textvarianten'},
    },
    'esegesi_biblica': {
        'it': {'title': 'Esegesi e Metodi', 'desc': 'Tecniche interpretative e figure retoriche'},
        'es': {'title': 'Exegesis y Metodos', 'desc': 'Tecnicas interpretativas y figuras retoricas'},
        'en': {'title': 'Exegesis and Methods', 'desc': 'Interpretive techniques and rhetorical figures'},
        'pt': {'title': 'Exegese e Metodos', 'desc': 'Tecnicas interpretativas e figuras retoricas'},
        'fr': {'title': 'Exegese et Methodes', 'desc': 'Techniques interpretatives et figures rhetoriques'},
        'de': {'title': 'Exegese und Methoden', 'desc': 'Interpretationstechniken und rhetorische Figuren'},
    },
    'lingue_bibliche': {
        'it': {'title': 'Lingue Bibliche', 'desc': 'Ebraico, aramaico e greco del NT'},
        'es': {'title': 'Lenguas Biblicas', 'desc': 'Hebreo, arameo y griego del NT'},
        'en': {'title': 'Biblical Languages', 'desc': 'Hebrew, Aramaic and NT Greek'},
        'pt': {'title': 'Linguas Biblicas', 'desc': 'Hebraico, aramaico e grego do NT'},
        'fr': {'title': 'Langues Bibliques', 'desc': 'Hebreu, arameen et grec du NT'},
        'de': {'title': 'Biblische Sprachen', 'desc': 'Hebraisch, Aramaisch und NT-Griechisch'},
    },
    'teologia_nt': {
        'it': {'title': 'Teologia del NT', 'desc': 'Cristologia, soteriologia e escatologia'},
        'es': {'title': 'Teologia del NT', 'desc': 'Cristologia, soteriologia y escatologia'},
        'en': {'title': 'NT Theology', 'desc': 'Christology, soteriology and eschatology'},
        'pt': {'title': 'Teologia do NT', 'desc': 'Cristologia, soteriologia e escatologia'},
        'fr': {'title': 'Theologie du NT', 'desc': 'Christologie, soteriologie et eschatologie'},
        'de': {'title': 'NT-Theologie', 'desc': 'Christologie, Soteriologie und Eschatologie'},
    },
    'teologia_at': {
        'it': {'title': "Teologia dell'AT", 'desc': 'Pentateuco, profeti e sapienza'},
        'es': {'title': 'Teologia del AT', 'desc': 'Pentateuco, profetas y sabiduria'},
        'en': {'title': 'OT Theology', 'desc': 'Pentateuch, prophets and wisdom'},
        'pt': {'title': 'Teologia do AT', 'desc': 'Pentateuco, profetas e sabedoria'},
        'fr': {'title': "Theologie de l'AT", 'desc': 'Pentateuque, prophetes et sagesse'},
        'de': {'title': 'AT-Theologie', 'desc': 'Pentateuch, Propheten und Weisheit'},
    },
    'storia_chiesa': {
        'it': {'title': 'Storia e Padri', 'desc': 'Eresie, concili e Padri della Chiesa'},
        'es': {'title': 'Historia y Padres', 'desc': 'Herejias, concilios y Padres de la Iglesia'},
        'en': {'title': 'History and Fathers', 'desc': 'Heresies, councils and Church Fathers'},
        'pt': {'title': 'Historia e Padres', 'desc': 'Heresias, concilios e Padres da Igreja'},
        'fr': {'title': 'Histoire et Peres', 'desc': 'Heresies, conciles et Peres de l\'Eglise'},
        'de': {'title': 'Geschichte und Vater', 'desc': 'Haresien, Konzilien und Kirchenvater'},
    },
}

# Cache for loaded data
_quiz_data_cache = None

def reload_quiz_data():
    """Force reload of quiz data (invalidate cache)"""
    global _quiz_data_cache
    _quiz_data_cache = load_quiz_categories()
    return _quiz_data_cache

def get_quiz_1000_data():
    """Get all quiz categories data with caching"""
    global _quiz_data_cache
    if _quiz_data_cache is None:
        _quiz_data_cache = load_quiz_categories()
    return _quiz_data_cache

def get_quiz_1000_topics(lang: str = 'it') -> list:
    """Get list of quiz topics for the new 1000 questions quiz"""
    data = get_quiz_1000_data()
    topics = []
    
    for cat_id, cat_data in data.items():
        # Get translated metadata
        trans = CATEGORY_TRANSLATIONS.get(cat_id, {}).get(lang, {})
        title = trans.get('title', cat_data.get('title', cat_id))
        desc = trans.get('desc', cat_data.get('description', ''))
        
        topics.append({
            'id': f"cat_{cat_id}",
            'title': title,
            'description': desc,
            'questions_count': len(cat_data.get('questions', [])),
            'difficulty': 'medium'
        })
    
    # Sort by title
    topics.sort(key=lambda x: x['title'])
    return topics

def get_quiz_1000_by_category(category_id: str, lang: str = 'it') -> dict:
    """Get quiz questions for a specific category"""
    data = get_quiz_1000_data()
    
    # Remove "cat_" prefix if present
    cat_id = category_id.replace('cat_', '')
    
    if cat_id not in data:
        return None
    
    cat_data = data[cat_id]
    
    # Get translated metadata
    trans = CATEGORY_TRANSLATIONS.get(cat_id, {}).get(lang, {})
    title = trans.get('title', cat_data.get('title', cat_id))
    
    # Get questions - Italian by default
    questions = cat_data.get('questions', [])
    questions = questions[:30] if len(questions) > 30 else questions  # Limit to 30 per quiz session
    
    return {
        'id': f"cat_{cat_id}",
        'title': title,
        'questions': questions,
        'lang': lang
    }

# ==================== ADVANCED SUBCATEGORIES ====================

_advanced_subcategories_cache = None
_advanced_translations_cache = None

def load_advanced_subcategories():
    """Load advanced subcategories from JSON"""
    if ADVANCED_SUBCATEGORIES_FILE.exists():
        with open(ADVANCED_SUBCATEGORIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_advanced_translations():
    """Load pre-generated translations for advanced subcategories"""
    if ADVANCED_TRANSLATIONS_FILE.exists():
        with open(ADVANCED_TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_advanced_subcategories():
    """Get advanced subcategories data with caching"""
    global _advanced_subcategories_cache
    if _advanced_subcategories_cache is None:
        _advanced_subcategories_cache = load_advanced_subcategories()
    return _advanced_subcategories_cache

def get_advanced_translations():
    """Get pre-generated translations with caching"""
    global _advanced_translations_cache
    if _advanced_translations_cache is None:
        _advanced_translations_cache = load_advanced_translations()
    return _advanced_translations_cache

def get_advanced_subcategory_topics(lang: str = 'it') -> list:
    """Get list of advanced subcategory topics"""
    data = get_advanced_subcategories()
    topics = []
    for sub_id, sub_data in data.items():
        trans = ADVANCED_SUBCATEGORY_TRANSLATIONS.get(sub_id, {}).get(lang, {})
        title = trans.get('title', sub_data.get('title', sub_id))
        desc = trans.get('desc', sub_data.get('description', ''))
        topics.append({
            'id': f"adv_{sub_id}",
            'title': title,
            'description': desc,
            'questions_count': len(sub_data.get('questions', [])),
            'difficulty': 'advanced'
        })
    return topics

def get_advanced_subcategory_quiz(subcategory_id: str, lang: str = 'it') -> dict:
    """Get quiz questions for a specific advanced subcategory with translations"""
    data = get_advanced_subcategories()
    sub_id = subcategory_id.replace('adv_', '')
    if sub_id not in data:
        return None
    sub_data = data[sub_id]
    trans = ADVANCED_SUBCATEGORY_TRANSLATIONS.get(sub_id, {}).get(lang, {})
    title = trans.get('title', sub_data.get('title', sub_id))
    
    # For Italian, return original questions
    if lang == 'it':
        return {
            'id': f"adv_{sub_id}",
            'title': title,
            'questions': sub_data.get('questions', [])
        }
    
    # For other languages, use pre-generated translations
    translations = get_advanced_translations()
    if sub_id in translations and lang in translations[sub_id]:
        translated_qs = translations[sub_id][lang].get('questions', [])
        return {
            'id': f"adv_{sub_id}",
            'title': title,
            'questions': translated_qs
        }
    
    # Fallback to Italian if no translation available
    return {
        'id': f"adv_{sub_id}",
        'title': title,
        'questions': sub_data.get('questions', [])
    }

async def get_quiz_1000_by_category_translated(category_id: str, lang: str = 'it') -> dict:
    """Get quiz questions for a specific category with translation support"""
    data = get_quiz_1000_data()
    
    # Remove "cat_" prefix if present
    cat_id = category_id.replace('cat_', '')
    
    if cat_id not in data:
        return None
    
    cat_data = data[cat_id]
    
    # Get translated metadata
    trans = CATEGORY_TRANSLATIONS.get(cat_id, {}).get(lang, {})
    title = trans.get('title', cat_data.get('title', cat_id))
    
    # Get questions
    questions = cat_data.get('questions', [])
    questions = questions[:30] if len(questions) > 30 else questions
    
    # For Italian, return as-is
    if lang == 'it':
        return {
            'id': f"cat_{cat_id}",
            'title': title,
            'questions': questions
        }
    
    # For other languages, translate on-demand
    translated_questions = []
    for q in questions:
        translated_q = await translate_question(q, lang)
        translated_questions.append(translated_q)
    
    return {
        'id': f"cat_{cat_id}",
        'title': title,
        'questions': translated_questions
    }
