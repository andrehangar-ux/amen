"""Batch translate advanced quiz subcategories to all languages"""
import json
import asyncio
import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUBCATEGORIES_FILE = Path(__file__).parent / 'quiz_advanced_subcategories.json'
OUTPUT_FILE = Path(__file__).parent / 'quiz_advanced_translations.json'
LANGUAGES = ['en', 'es', 'de', 'fr', 'pt']

LANG_NAMES = {
    'es': 'Spanish', 'en': 'English', 'de': 'German',
    'fr': 'French', 'pt': 'Portuguese'
}

async def translate_question_batch(questions: list, target_lang: str) -> list:
    """Translate a batch of questions in one LLM call"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    
    batch_text = json.dumps([{
        "id": q["id"],
        "question": q["question"],
        "options": q["options"],
        "explanation": q["explanation"]
    } for q in questions], ensure_ascii=False)
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"batch_translate_{target_lang}_{questions[0]['id']}",
        system_message=f"Translate the following Bible quiz questions from Italian to {LANG_NAMES[target_lang]}. Return a JSON array with objects containing: id, question, options (array of 4 strings), explanation. Keep biblical names and references in their common {LANG_NAMES[target_lang]} form. Return ONLY the JSON array, no markdown."
    ).with_model("openai", "gpt-4o-mini")
    
    response = await chat.send_message(UserMessage(text=batch_text))
    
    # Parse JSON response
    json_match = re.search(r'\[.*\]', response, re.DOTALL)
    if json_match:
        translated = json.loads(json_match.group())
    else:
        translated = json.loads(response)
    
    # Merge with original data (keep correct answer index)
    results = []
    for i, q in enumerate(questions):
        t = translated[i] if i < len(translated) else {}
        results.append({
            "id": q["id"],
            "question": t.get("question", q["question"]),
            "options": t.get("options", q["options"]),
            "correct": q["correct"],
            "explanation": t.get("explanation", q["explanation"])
        })
    return results


async def main():
    with open(SUBCATEGORIES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load existing translations if any
    translations = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
    
    total = len(data) * len(LANGUAGES)
    done = 0
    
    for sub_id, sub_data in data.items():
        if sub_id not in translations:
            translations[sub_id] = {}
        
        for lang in LANGUAGES:
            if lang in translations[sub_id]:
                done += 1
                print(f"[{done}/{total}] SKIP {sub_id} -> {lang} (already translated)")
                continue
            
            print(f"[{done+1}/{total}] Translating {sub_id} -> {lang}...")
            try:
                translated_qs = await translate_question_batch(sub_data["questions"], lang)
                translations[sub_id][lang] = {
                    "questions": translated_qs
                }
                done += 1
                print(f"[{done}/{total}] OK {sub_id} -> {lang}")
                
                # Save after each batch
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                done += 1
                print(f"[{done}/{total}] ERROR {sub_id} -> {lang}: {e}")
    
    print(f"\nDone! Translations saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
