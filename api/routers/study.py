"""Study Tools Router: Flashcards Sets and Subject Skill Tree Mastery."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_user
from db.models.study import FlashcardItem, FlashcardSet, SkillNode, StudentSkill
from db.models.user import User
from db.session import get_db

router = APIRouter(prefix="/study", tags=["Study Tools"])


@router.get("/flashcards")
async def get_flashcard_sets(
    subject_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists available flashcard decks with their cards."""
    stmt = (
        select(FlashcardSet)
        .where(FlashcardSet.school_id == current_user.school_id, FlashcardSet.is_published == True)
        .options(selectinload(FlashcardSet.cards))
    )
    if subject_id:
        stmt = stmt.where(FlashcardSet.subject_id == subject_id)

    sets = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "card_count": len(s.cards),
            "cards": [
                {"id": c.id, "front": c.front_text, "back": c.back_text, "hint": c.hint_text}
                for c in s.cards
            ],
        }
        for s in sets
    ]


@router.get("/skills/{subject_id}")
async def get_subject_skill_tree(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the visual prerequisite skill tree for a subject and student's mastery."""
    # Fetch all skill nodes for this subject
    stmt = select(SkillNode).where(SkillNode.subject_id == subject_id).order_by(SkillNode.order_index.asc())
    nodes = (await db.execute(stmt)).scalars().all()

    # Fetch student's progress
    progress_stmt = select(StudentSkill).where(StudentSkill.student_id == current_user.id)
    progress_records = (await db.execute(progress_stmt)).scalars().all()
    mastery_map = {p.skill_node_id: p.mastery_percentage for p in progress_records}

    return [
        {
            "id": n.id,
            "title_ru": n.title_ru,
            "title_uz": n.title_uz,
            "description": n.description,
            "prerequisite_id": n.prerequisite_id,
            "mastery_pct": mastery_map.get(n.id, 0),
        }
        for n in nodes
    ]
