"""
Articulate cryptic quiz questions: for each candidate (short Q + [123]-ref explanation),
ask the LLM to rewrite ONLY the `question` and `explanation` text in clear Italian,
keeping options and `correct` intact. Saves results incrementally.

Run with: python3 articulate_quiz.py
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
SRC = '/app/backend/quiz_categories_data.json'
PROGRESS = '/tmp/articulate_progress.json'
BATCH_SIZE = 8  # questions per LLM call
CONCURRENCY = 1  # sequential (LiteLLM has issues with parallel async chat instances)
LLM_TIMEOUT = 45  # per-batch timeout


def is_candidate(q):
    text = q['question'].strip()
    exp = q.get('explanation', '').strip()
    return len(text) < 30 and bool(re.search(r'\[\d+', exp))


SYSTEM = """Sei un esperto di didattica biblica. Riformuli quiz biblici in italiano chiaro.
INPUT: lista JSON di domande quiz brevi/cripte con campi: id, question, options (4), correct (indice 0-3), explanation, verse_ref.
OUTPUT: identica lista JSON in cui:
- riscrivi `question` come domanda completa, comprensibile, in italiano fluido, di lunghezza 40-100 caratteri
- riscrivi `explanation` come frase chiara di 15-200 caratteri, RIMUOVENDO riferimenti `[123, 456]` e simili
- MANTIENI INVARIATI: id, options (esattamente), correct (indice), verse_ref (a meno che tu non sappia un riferimento biblico più preciso, in tal caso aggiornalo)
- Non aggiungere nuove domande, non rimuovere domande
- Rispondi SOLO con il JSON array, senza commenti, senza markdown."""


async def articulate_batch(batch_id: int, questions: list) -> list:
    """Ask LLM to articulate a batch. Return list with rewritten question/explanation."""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"articulate_batch_{batch_id}",
        system_message=SYSTEM,
    ).with_model("openai", "gpt-4o-mini")

    payload = json.dumps(questions, ensure_ascii=False)
    response = await chat.send_message(UserMessage(text=payload))

    # Strip code fences if any
    txt = response.strip()
    txt = re.sub(r'^```(?:json)?\s*', '', txt)
    txt = re.sub(r'\s*```$', '', txt)

    try:
        result = json.loads(txt)
    except json.JSONDecodeError as e:
        print(f"[batch {batch_id}] JSON parse error: {e}. Raw: {txt[:200]}")
        return questions  # fallback: return originals

    # Validate: must be list of same length with same IDs
    if not isinstance(result, list) or len(result) != len(questions):
        print(f"[batch {batch_id}] shape mismatch ({len(result) if isinstance(result, list) else '?'} vs {len(questions)})")
        return questions

    # Merge: keep all original keys, override only question + explanation + verse_ref
    out = []
    by_id = {r.get('id'): r for r in result if isinstance(r, dict)}
    for orig in questions:
        r = by_id.get(orig['id'])
        if not r:
            out.append(orig)
            continue
        merged = dict(orig)
        new_q = (r.get('question') or '').strip()
        new_e = (r.get('explanation') or '').strip()
        new_vr = (r.get('verse_ref') or '').strip()
        if 25 <= len(new_q) <= 200:
            merged['question'] = new_q
        if 10 <= len(new_e) <= 400:
            merged['explanation'] = new_e
        if new_vr and len(new_vr) <= 60:
            merged['verse_ref'] = new_vr
        out.append(merged)
    return out


async def main():
    data = json.load(open(SRC))

    # Build list of (cat_id, q_index, q) for all candidates
    todo = []
    for cat_id, cat in data.items():
        for idx, q in enumerate(cat.get('questions', [])):
            if is_candidate(q):
                todo.append((cat_id, idx, q))

    # Resume support
    done_ids = set()
    if Path(PROGRESS).exists():
        done_ids = set(json.load(open(PROGRESS)).get('done', []))

    todo = [t for t in todo if t[2]['id'] not in done_ids]
    print(f"Candidate da articolare: {len(todo)} (già fatte: {len(done_ids)})")

    # Chunk into batches
    batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    print(f"Batches: {len(batches)} da {BATCH_SIZE} domande ({CONCURRENCY} in parallelo)")

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def process(batch_id: int, batch: list):
        async with semaphore:
            print(f"[batch {batch_id}/{len(batches)-1}] start ({len(batch)} q)", flush=True)
            questions_only = [
                {
                    'id': q['id'],
                    'question': q['question'],
                    'options': q.get('options', []),
                    'correct': q.get('correct'),
                    'explanation': q.get('explanation', ''),
                    'verse_ref': q.get('verse_ref', ''),
                }
                for _, _, q in batch
            ]
            try:
                rewritten = await asyncio.wait_for(
                    articulate_batch(batch_id, questions_only),
                    timeout=LLM_TIMEOUT,
                )
            except asyncio.TimeoutError:
                print(f"[batch {batch_id}] TIMEOUT after {LLM_TIMEOUT}s", flush=True)
                return batch_id, batch, None
            except Exception as e:
                print(f"[batch {batch_id}] error: {type(e).__name__}: {e}", flush=True)
                return batch_id, batch, None
            print(f"[batch {batch_id}] done", flush=True)
            return batch_id, batch, rewritten

    tasks = [asyncio.create_task(process(i, b)) for i, b in enumerate(batches)]
    completed = 0
    for fut in asyncio.as_completed(tasks):
        batch_id, batch, rewritten = await fut
        completed += 1
        if rewritten is None:
            continue
        # Apply rewrites in-memory
        rewritten_by_id = {r['id']: r for r in rewritten}
        for cat_id, idx, q in batch:
            new = rewritten_by_id.get(q['id'])
            if new:
                data[cat_id]['questions'][idx] = new
                done_ids.add(q['id'])

        # Periodic save (atomic write)
        if completed % 5 == 0 or completed == len(batches):
            tmp_src = SRC + '.tmp'
            with open(tmp_src, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_src, SRC)
            with open(PROGRESS, 'w') as f:
                json.dump({'done': sorted(done_ids)}, f)
            print(f"[{completed}/{len(batches)}] salvato — domande articolate: {len(done_ids)}")

    # Final save (atomic)
    tmp_src = SRC + '.tmp'
    with open(tmp_src, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_src, SRC)
    with open(PROGRESS, 'w') as f:
        json.dump({'done': sorted(done_ids)}, f)
    print(f"\n✓ DONE. {len(done_ids)} domande articolate.")


if __name__ == '__main__':
    asyncio.run(main())
