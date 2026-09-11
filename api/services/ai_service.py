"""AI Study Assistant, Pre-test Recap, and Parent Smart Summary Service with graceful degradation."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lumina.ai")


def generate_study_hint(subject: str, topic: str, question: str) -> Dict[str, str]:
    """
    Generates an educational hint that guides student thinking without spoiling the answer.
    Resilient design: works deterministically out-of-the-box.
    """
    return {
        "subject": subject,
        "topic": topic,
        "hint": f"💡 Подсказка по теме '{topic}': Вспомни ключевое определение и попробуй разбить задачу на 2 простых шага. Сначала выдели известные данные, а затем примени базовую формулу.",
        "thought_question": "Какой первый вывод можно сделать из условия задачи?",
    }


def generate_pre_test_recap(subject: str, grade_level: int, key_topics: List[str]) -> Dict[str, Any]:
    """Generates a structured pre-test summary with key formulas, concepts, and practice ideas."""
    topics_formatted = ", ".join(key_topics) if key_topics else "Базовые понятия курса"
    return {
        "subject": subject,
        "grade_level": grade_level,
        "title": f"Экспресс-повторение перед контрольной: {subject}",
        "sections": [
            {
                "title": "📌 Главные понятия и термины",
                "content": f"Обязательно повтори темы: {topics_formatted}. Обрати внимание на связь между ними и определения основных величин.",
            },
            {
                "title": "📐 Формулы и правила",
                "content": "Проверь себя: можешь ли ты записать основную формулу по памяти и объяснить, что означает каждый коэффициент?",
            },
            {
                "title": "⚠️ Частые ошибки на тестах",
                "content": "Невнимательность к единицам измерения и спешка при чтении условия задачи. Всегда перепроверяй ответ подстановкой!",
            },
        ],
        "quiz_sample": "Вопрос для самопроверки: Можешь ли ты своими словами объяснить основное правило этой темы младшему товарищу?",
    }


def generate_parent_weekly_summary(
    child_name: str,
    gpa: float,
    recent_grades: List[Dict[str, Any]],
    attendance_pct: float,
    completed_homework_pct: float,
) -> Dict[str, Any]:
    """Generates an objective, encouraging weekly digest for parents."""
    status_tone = "отличная" if gpa >= 4.0 else ("стабильная" if gpa >= 3.0 else "требует внимания")
    
    highlights = []
    if recent_grades:
        high_grades = [g for g in recent_grades if float(g.get("value", 0)) >= 4.0]
        if high_grades:
            subjects = list({g.get("subject", "") for g in high_grades})
            highlights.append(f"Успехи по предметам: {', '.join(subjects)}")
    
    if attendance_pct >= 90:
        highlights.append(f"Отличная посещаемость ({int(attendance_pct)}%)")
    else:
        highlights.append(f"Обратите внимание на пропуски (посещаемость {int(attendance_pct)}%)")

    if completed_homework_pct >= 80:
        highlights.append(f"Домашние задания сдаются вовремя ({int(completed_homework_pct)}%)")

    return {
        "child_name": child_name,
        "period": "За последние 7 дней",
        "academic_status": status_tone,
        "gpa": round(gpa, 2),
        "attendance_pct": round(attendance_pct, 1),
        "completed_homework_pct": round(completed_homework_pct, 1),
        "highlights": highlights,
        "summary_text": (
            f"За прошедшую неделю успеваемость {child_name} {status_tone} (средний балл: {round(gpa, 2)}). "
            f"Посещаемость составила {int(attendance_pct)}%, а домашние задания выполнены на {int(completed_homework_pct)}%. "
            f"Рекомендуем поддержать интерес к профильным предметам и уделить внимание повторению тем перед уроками."
        ),
    }
