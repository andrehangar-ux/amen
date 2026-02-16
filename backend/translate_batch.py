#!/usr/bin/env python3
"""
Batch translation script - translates biblical dictionary terms using AI
Processes terms in smaller batches to avoid timeout issues
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

LANGUAGES = ["en", "es", "de", "fr", "pt"]
LANG_NAMES = {
    "en": "English",
    "es": "Spanish", 
    "de": "German",
    "fr": "French",
    "pt": "Portuguese"
}

async def translate_multiple_terms(terms_batch: list, target_lang: str) -> dict:
    """Translate multiple terms in one API call for efficiency"""
    lang_name = LANG_NAMES[target_lang]
    
    # Build prompt with multiple terms
    terms_text = ""
    for term_id in terms_batch:
        term_data = BIBLICAL_DICTIONARY[term_id]
        terms_text += f"""
Term ID: {term_id}
Term: {term_data['term']}
Meaning (Italian): {term_data['meaning']}
Description (Italian): {term_data['description'][:500]}

"""
    
    prompt = f"""Translate these biblical dictionary terms to {lang_name}.
Return a JSON object where each key is the term_id and the value has "meaning" and "description".

{terms_text}

Return ONLY valid JSON like:
{{"term_id1": {{"meaning": "...", "description": "..."}}, "term_id2": ...}}
"""
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"batch_{target_lang}_{terms_batch[0]}",
            system_message="You are a professional biblical scholar and translator. Return only valid JSON, no markdown."
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=prompt))
        response = response.strip()
        
        # Clean response
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[-1].strip() == "```":
                response = "\n".join(lines[1:-1])
            else:
                response = "\n".join(lines[1:])
        if response.strip().startswith("json"):
            response = response.strip()[4:].strip()
            
        return json.loads(response)
    except Exception as e:
        print(f"Error in batch translation to {target_lang}: {e}")
        # Return empty translations for failed batch
        return {term_id: {"meaning": "", "description": ""} for term_id in terms_batch}

async def main():
    all_translations = {}
    term_ids = list(BIBLICAL_DICTIONARY.keys())
    batch_size = 5  # Process 5 terms at a time
    
    print(f"Total terms: {len(term_ids)}")
    print(f"Batch size: {batch_size}")
    
    for lang in LANGUAGES:
        print(f"\n=== Translating to {LANG_NAMES[lang]} ===")
        
        for i in range(0, len(term_ids), batch_size):
            batch = term_ids[i:i+batch_size]
            print(f"  Batch {i//batch_size + 1}: {batch}")
            
            translations = await translate_multiple_terms(batch, lang)
            
            for term_id, trans in translations.items():
                if term_id not in all_translations:
                    all_translations[term_id] = {}
                all_translations[term_id][lang] = trans
            
            await asyncio.sleep(0.5)  # Rate limiting
    
    # Generate output file
    print("\n=== Saving translations ===")
    
    output = "# Auto-generated translations for biblical dictionary\n\n"
    output += "DICT_TERM_TRANSLATIONS = {\n"
    
    for term_id in sorted(all_translations.keys()):
        output += f'    "{term_id}": {{\n'
        for lang in LANGUAGES:
            if lang in all_translations[term_id]:
                trans = all_translations[term_id][lang]
                meaning = trans.get("meaning", "").replace('"', '\\"').replace('\n', ' ')
                description = trans.get("description", "").replace('"', '\\"').replace('\n', ' ')
                output += f'        "{lang}": {{"meaning": "{meaning}", "description": "{description}"}},\n'
        output += "    },\n"
    
    output += "}\n"
    
    output_path = ROOT_DIR / "dictionary_translations.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Saved to {output_path}")
    print(f"Total terms: {len(all_translations)}")

if __name__ == "__main__":
    asyncio.run(main())
