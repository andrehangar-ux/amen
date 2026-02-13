#!/usr/bin/env python3
"""
Script to generate translations for biblical dictionary terms using AI
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage
from biblical_dictionary import BIBLICAL_DICTIONARY

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "de": "German", 
    "fr": "French",
    "pt": "Portuguese"
}

async def translate_term(term_id: str, term_data: dict, target_lang: str) -> dict:
    """Translate a single term to target language"""
    lang_name = LANGUAGES[target_lang]
    
    prompt = f"""Translate the following biblical dictionary entry to {lang_name}.
Return ONLY a JSON object with two fields: "meaning" and "description".
Do not add any markdown formatting or explanation.

Original term: {term_data['term']}
Original meaning (Italian): {term_data['meaning']}
Original description (Italian): {term_data['description']}

Return JSON format:
{{"meaning": "translated meaning in {lang_name}", "description": "translated description in {lang_name}"}}
"""
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate_{term_id}_{target_lang}",
            system_message="You are a professional biblical translator. Return only valid JSON."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=prompt))
        response = response.strip()
        
        # Clean up response - remove markdown if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        if response.startswith("json"):
            response = response[4:].strip()
            
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error translating {term_id} to {target_lang}: {e}")
        return {"meaning": term_data['meaning'], "description": term_data['description']}

async def translate_batch(terms: list, target_lang: str) -> dict:
    """Translate a batch of terms to target language"""
    results = {}
    for term_id in terms:
        term_data = BIBLICAL_DICTIONARY[term_id]
        print(f"  Translating {term_id} to {target_lang}...")
        translation = await translate_term(term_id, term_data, target_lang)
        results[term_id] = translation
        await asyncio.sleep(0.3)  # Rate limiting
    return results

async def main():
    all_translations = {}
    
    term_ids = list(BIBLICAL_DICTIONARY.keys())
    print(f"Total terms to translate: {len(term_ids)}")
    
    for lang_code, lang_name in LANGUAGES.items():
        print(f"\n=== Translating to {lang_name} ({lang_code}) ===")
        lang_translations = await translate_batch(term_ids, lang_code)
        
        for term_id, translation in lang_translations.items():
            if term_id not in all_translations:
                all_translations[term_id] = {}
            all_translations[term_id][lang_code] = translation
    
    # Generate Python code for DICT_TERM_TRANSLATIONS
    print("\n=== Generating Python code ===")
    
    output = "# Auto-generated translations for biblical dictionary\n"
    output += "DICT_TERM_TRANSLATIONS = {\n"
    
    for term_id in sorted(all_translations.keys()):
        output += f'    "{term_id}": {{\n'
        for lang_code in ["en", "es", "de", "fr", "pt"]:
            if lang_code in all_translations[term_id]:
                trans = all_translations[term_id][lang_code]
                meaning = trans.get("meaning", "").replace('"', '\\"')
                description = trans.get("description", "").replace('"', '\\"')
                output += f'        "{lang_code}": {{"meaning": "{meaning}", "description": "{description}"}},\n'
        output += "    },\n"
    
    output += "}\n"
    
    # Save to file
    with open(ROOT_DIR / "dictionary_translations.py", "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"\nTranslations saved to dictionary_translations.py")
    print(f"Total terms translated: {len(all_translations)}")

if __name__ == "__main__":
    asyncio.run(main())
