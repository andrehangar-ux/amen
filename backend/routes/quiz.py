"""
Quiz endpoints.

Three quiz systems coexist:
- Classic topic-based quizzes (`quiz_data.MULTILINGUAL_QUIZZES`)
- Category quizzes ("Quiz 1000" — `quiz_1000.get_quiz_1000_*`)
- Advanced subcategory quizzes (`quiz_1000.get_advanced_subcategory_*`)

Submit endpoint produces AI feedback in the requested language and persists
the result to `db.quiz_results`.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict
import uuid

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from emergentintegrations.llm.chat import LlmChat, UserMessage

from core import api_router, db, EMERGENT_LLM_KEY
from dependencies import require_auth
from models import User

from quiz_data import get_quiz_for_language, get_all_topics_for_language
from quiz_1000 import (
    get_quiz_1000_topics,
    get_quiz_1000_by_category,
    get_quiz_1000_by_category_translated,
    get_advanced_subcategory_topics,
    get_advanced_subcategory_quiz,
)


@api_router.get("/quiz/topics")
async def get_quiz_topics(lang: str = "it"):
    """Get available quiz topics in specified language"""
    return get_all_topics_for_language(lang)


@api_router.get("/quiz/categories")
async def get_quiz_categories(lang: str = "it"):
    """Get all quiz categories (1000+ questions organized by theme)"""
    return get_quiz_1000_topics(lang)


@api_router.get("/quiz/advanced-subcategories")
async def get_advanced_subcategories_endpoint(lang: str = "it"):
    """Get the advanced subcategory topics"""
    return get_advanced_subcategory_topics(lang)


@api_router.get("/quiz/advanced-subcategory/{subcategory_id}")
async def get_advanced_subcategory_endpoint(subcategory_id: str, lang: str = "it"):
    """Get quiz questions for a specific advanced subcategory"""
    quiz = get_advanced_subcategory_quiz(subcategory_id, lang)
    if not quiz:
        raise HTTPException(status_code=404, detail="Sottocategoria non trovata")
    return quiz


@api_router.get("/quiz/category/{category_id}")
async def get_quiz_by_category(category_id: str, lang: str = "it", translate: bool = True):
    """Get quiz questions for a specific category with optional translation"""
    if translate and lang != "it":
        quiz = await get_quiz_1000_by_category_translated(category_id, lang)
    else:
        quiz = get_quiz_1000_by_category(category_id, lang)

    if not quiz:
        raise HTTPException(status_code=404, detail="Categoria non trovata")
    return quiz


@api_router.get("/quiz/history")
async def get_quiz_history(user: User = Depends(require_auth)):
    """Get user's quiz history"""
    history = await db.quiz_results.find(
        {"user_id": user.user_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(50).to_list(50)
    return history


@api_router.get("/quiz/stats")
async def get_quiz_stats(user: User = Depends(require_auth)):
    """Get user's quiz statistics"""
    all_results = await db.quiz_results.find(
        {"user_id": user.user_id},
        {"_id": 0},
    ).to_list(1000)

    if not all_results:
        return {
            "total_quizzes": 0,
            "total_questions": 0,
            "total_correct": 0,
            "average_score": 0,
            "best_score": 0,
            "categories_completed": {},
            "recent_quizzes": [],
            "streak": 0,
        }

    total_quizzes = len(all_results)
    total_questions = sum(r.get("total", 0) for r in all_results)
    total_correct = sum(r.get("correct_count", 0) for r in all_results)
    average_score = round(sum(r.get("score", 0) for r in all_results) / total_quizzes, 1) if total_quizzes > 0 else 0
    best_score = max((r.get("score", 0) for r in all_results), default=0)

    categories_completed: Dict[str, Dict] = {}
    for r in all_results:
        topic = r.get("topic", "unknown")
        if topic not in categories_completed:
            categories_completed[topic] = {
                "attempts": 0,
                "best_score": 0,
                "total_correct": 0,
                "total_questions": 0,
            }
        categories_completed[topic]["attempts"] += 1
        categories_completed[topic]["best_score"] = max(
            categories_completed[topic]["best_score"],
            r.get("score", 0),
        )
        categories_completed[topic]["total_correct"] += r.get("correct_count", 0)
        categories_completed[topic]["total_questions"] += r.get("total", 0)

    dates_with_quiz = set()
    for r in all_results:
        if "created_at" in r:
            date = r["created_at"]
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            dates_with_quiz.add(date.date())

    streak = 0
    current_date = datetime.now(timezone.utc).date()
    while current_date in dates_with_quiz:
        streak += 1
        current_date -= timedelta(days=1)

    recent_quizzes = sorted(all_results, key=lambda x: x.get("created_at", ""), reverse=True)[:10]

    return {
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "average_score": average_score,
        "best_score": best_score,
        "categories_completed": categories_completed,
        "recent_quizzes": recent_quizzes,
        "streak": streak,
    }


@api_router.get("/quiz/{topic}")
async def get_quiz(topic: str, lang: str = "it"):
    """Get quiz by topic in specified language"""
    quiz = get_quiz_for_language(topic, lang)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz non trovato")
    return quiz


class QuizSubmission(BaseModel):
    topic: str
    answers: Dict[str, int]  # question_id -> selected_option_index
    language: str = "it"


@api_router.post("/quiz/submit")
async def submit_quiz(data: QuizSubmission, user: User = Depends(require_auth)):
    """Submit quiz answers and get AI feedback - supports classic, category and advanced quizzes"""
    lang = data.language or "it"
    quiz = None
    quiz_title = ""

    if data.topic.startswith("cat_"):
        category_quiz = get_quiz_1000_by_category(data.topic, lang)
        if category_quiz:
            quiz = {"questions": category_quiz["questions"], "title": category_quiz["title"]}
            quiz_title = category_quiz["title"]
    elif data.topic.startswith("adv_"):
        adv_quiz = get_advanced_subcategory_quiz(data.topic, lang)
        if adv_quiz:
            quiz = {"questions": adv_quiz["questions"], "title": adv_quiz["title"]}
            quiz_title = adv_quiz["title"]
    else:
        quiz = get_quiz_for_language(data.topic, lang)
        if quiz:
            quiz_title = quiz.get("title", data.topic)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz non trovato")

    correct_count = 0
    total = len(quiz["questions"])
    results = []

    for question in quiz["questions"]:
        user_answer = data.answers.get(question["id"], -1)
        is_correct = user_answer == question["correct"]
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": question["id"],
            "is_correct": is_correct,
            "correct_answer": question["correct"],
            "user_answer": user_answer,
            "explanation": question.get("explanation", ""),
            "verse_ref": question.get("verse_ref", ""),
            "question_text": question.get("question", ""),
            "options": question.get("options", []),
        })

    score = (correct_count / total) * 100 if total > 0 else 0

    feedback_prompts = {
        "it": f"L'utente ha completato il quiz '{quiz_title}' con un punteggio di {score:.0f}% ({correct_count}/{total} risposte corrette). Dai un feedback breve e incoraggiante in italiano.",
        "es": f"El usuario completó el quiz '{quiz_title}' con una puntuación del {score:.0f}% ({correct_count}/{total} respuestas correctas). Da un feedback breve y alentador en español.",
        "en": f"The user completed the quiz '{quiz_title}' with a score of {score:.0f}% ({correct_count}/{total} correct answers). Give brief and encouraging feedback in English.",
        "de": f"Der Benutzer hat das Quiz '{quiz_title}' mit {score:.0f}% ({correct_count}/{total} richtige Antworten) abgeschlossen. Gib kurzes, ermutigendes Feedback auf Deutsch.",
        "fr": f"L'utilisateur a terminé le quiz '{quiz_title}' avec un score de {score:.0f}% ({correct_count}/{total} bonnes réponses). Donne un feedback bref et encourageant en français.",
        "pt": f"O usuário completou o quiz '{quiz_title}' com pontuação de {score:.0f}% ({correct_count}/{total} respostas corretas). Dê um feedback breve e encorajador em português.",
    }

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"quiz_{user.user_id}_{data.topic}",
            system_message="You are a Bible teacher. Give encouraging feedback based on quiz scores.",
        ).with_model("openai", "gpt-4o")

        feedback = await chat.send_message(UserMessage(
            text=feedback_prompts.get(lang, feedback_prompts["it"])
        ))
    except Exception:
        default_feedback = {
            "it": f"Hai completato il quiz con {correct_count}/{total} risposte corrette!",
            "es": f"¡Completaste el quiz con {correct_count}/{total} respuestas correctas!",
            "en": f"You completed the quiz with {correct_count}/{total} correct answers!",
            "de": f"Du hast das Quiz mit {correct_count}/{total} richtigen Antworten abgeschlossen!",
            "fr": f"Vous avez terminé le quiz avec {correct_count}/{total} bonnes réponses !",
            "pt": f"Você completou o quiz com {correct_count}/{total} respostas corretas!",
        }
        feedback = default_feedback.get(lang, default_feedback["it"])

    await db.quiz_results.insert_one({
        "result_id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "topic": data.topic,
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "language": lang,
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "results": results,
        "feedback": feedback,
    }
