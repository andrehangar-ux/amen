#!/usr/bin/env python3
"""
Script per tradurre le 1000 domande del quiz in tutte le lingue supportate.
Usa OpenAI GPT-4o per le traduzioni.
"""

import json
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage

# Configurazione
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
LANGUAGES = ['es', 'en', 'de', 'fr', 'pt']  # Italiano è la lingua base
BATCH_SIZE = 10  # Numero di domande per batch

DATA_FILE = Path(__file__).parent / 'quiz_categories_data.json'
OUTPUT_FILE = Path(__file__).parent / 'quiz_categories_translated.json'

async def translate_batch(questions: list, target_lang: str) -> list:
    """Traduce un batch di domande in una lingua specifica"""
    
    lang_names = {
        'es': 'Spanish',
        'en': 'English', 
        'de': 'German',
        'fr': 'French',
        'pt': 'Portuguese'
    }
    
    # Prepara il testo da tradurre
    questions_text = []
    for i, q in enumerate(questions):
        q_text = f"""[Q{i}]
Question: {q['question']}
Option A: {q['options'][0]}
Option B: {q['options'][1]}
Option C: {q['options'][2]}
Option D: {q['options'][3]}
Explanation: {q['explanation']}
"""
        questions_text.append(q_text)
    
    full_text = "\n".join(questions_text)
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"translate_{target_lang}_{hash(full_text) % 10000}",
        system_message=f"""You are a professional Bible translator. Translate the following quiz questions from Italian to {lang_names[target_lang]}.
Keep the [Q0], [Q1], etc. markers. Keep the structure exactly the same (Question:, Option A:, etc.).
Only translate the text content, not the markers. Preserve biblical names in their common form for {lang_names[target_lang]}."""
    ).with_model("openai", "gpt-4o")
    
    try:
        response = await chat.send_message(UserMessage(text=full_text))
        
        # Parse della risposta
        translated = []
        parts = response.split('[Q')
        
        for i, part in enumerate(parts[1:]):  # Skip prima parte vuota
            lines = part.strip().split('\n')
            q_data = {}
            
            for line in lines:
                if line.startswith('Question:'):
                    q_data['question'] = line.replace('Question:', '').strip()
                elif line.startswith('Option A:'):
                    q_data['option_a'] = line.replace('Option A:', '').strip()
                elif line.startswith('Option B:'):
                    q_data['option_b'] = line.replace('Option B:', '').strip()
                elif line.startswith('Option C:'):
                    q_data['option_c'] = line.replace('Option C:', '').strip()
                elif line.startswith('Option D:'):
                    q_data['option_d'] = line.replace('Option D:', '').strip()
                elif line.startswith('Explanation:'):
                    q_data['explanation'] = line.replace('Explanation:', '').strip()
            
            if 'question' in q_data:
                translated.append({
                    'question': q_data.get('question', questions[i]['question']),
                    'options': [
                        q_data.get('option_a', questions[i]['options'][0]),
                        q_data.get('option_b', questions[i]['options'][1]),
                        q_data.get('option_c', questions[i]['options'][2]),
                        q_data.get('option_d', questions[i]['options'][3])
                    ],
                    'explanation': q_data.get('explanation', questions[i]['explanation'])
                })
            else:
                # Fallback se parsing fallisce
                translated.append({
                    'question': questions[i]['question'],
                    'options': questions[i]['options'],
                    'explanation': questions[i]['explanation']
                })
        
        # Se mancano traduzioni, usa originali
        while len(translated) < len(questions):
            idx = len(translated)
            translated.append({
                'question': questions[idx]['question'],
                'options': questions[idx]['options'],
                'explanation': questions[idx]['explanation']
            })
        
        return translated
        
    except Exception as e:
        print(f"Error translating batch: {e}")
        # Ritorna originali in caso di errore
        return [{'question': q['question'], 'options': q['options'], 'explanation': q['explanation']} for q in questions]


async def translate_all_questions():
    """Traduce tutte le domande in tutte le lingue"""
    
    # Carica dati originali
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Struttura output con traduzioni
    translated_data = {}
    
    total_questions = sum(len(cat['questions']) for cat in data.values())
    print(f"Starting translation of {total_questions} questions into {len(LANGUAGES)} languages...")
    
    for cat_id, cat_data in data.items():
        print(f"\n=== Category: {cat_data['title']} ({len(cat_data['questions'])} questions) ===")
        
        translated_data[cat_id] = {
            'title': cat_data['title'],
            'description': cat_data['description'],
            'questions': {
                'it': cat_data['questions']  # Italiano originale
            }
        }
        
        questions = cat_data['questions']
        
        for lang in LANGUAGES:
            print(f"  Translating to {lang}...")
            translated_questions = []
            
            # Traduce in batch
            for i in range(0, len(questions), BATCH_SIZE):
                batch = questions[i:i+BATCH_SIZE]
                print(f"    Batch {i//BATCH_SIZE + 1}/{(len(questions)-1)//BATCH_SIZE + 1}...")
                
                translated_batch = await translate_batch(batch, lang)
                
                # Merge con dati originali (mantiene id, correct, verse_ref)
                for j, trans in enumerate(translated_batch):
                    orig = batch[j]
                    translated_questions.append({
                        'id': orig['id'],
                        'question': trans['question'],
                        'options': trans['options'],
                        'correct': orig['correct'],
                        'explanation': trans['explanation'],
                        'verse_ref': orig.get('verse_ref', '')
                    })
                
                # Piccola pausa per non sovraccaricare l'API
                await asyncio.sleep(0.5)
            
            translated_data[cat_id]['questions'][lang] = translated_questions
    
    # Salva risultato
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Translation complete! Saved to {OUTPUT_FILE}")
    return translated_data


if __name__ == '__main__':
    asyncio.run(translate_all_questions())
