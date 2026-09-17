from __future__ import annotations

# Allow direct execution from the repository root (e.g. `python scripts/benchmark.py`).
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import asyncio
import json
from datetime import datetime, timezone
from app.core.models import ModeratorAction
from app.services.pipeline import QuestionPipeline, IntakeQuestion
from app.agents.priority_agent import PriorityAgent
from app.services.evidence import build_evidence_report, report_dict
from app.storage.db import init_db, create_meeting, upsert_participant, add_question, add_like, save_categories, update_questions_category, get_questions, add_decision, add_outcome, add_event

async def main() -> None:
    init_db()
    meeting = create_meeting(
        "Fintech Architecture Review",
        "fintech-architecture",
        "launch readiness, resilience, database migration, observability",
        "moderator",
    )
    for uid, name, exp in [
        ("arch", "Architect", ["architecture", "distributed-systems"]),
        ("risk", "Risk Lead", ["risk", "compliance"]),
        ("backend", "Backend Lead", ["python", "databases"]),
        ("product", "Product Lead", ["product", "launch"]),
    ]:
        upsert_participant(meeting.id, uid, name, exp)
    raw = [
        ("arch", "When is the target production launch date?", ["architecture"]),
        ("product", "Do we have a confirmed go-live date for customers?", ["product"]),
        ("backend", "What is the rollback plan for the database migration?", ["databases"]),
        ("risk", "What controls prevent the migration from violating our audit requirements?", ["risk", "compliance"]),
        ("arch", "How will we know if the new architecture is degrading in production?", ["architecture", "observability"]),
        ("backend", "Which observability signals trigger an incident?", ["observability"]),
    ]
    questions = []
    for uid, text, exp in raw:
        row = add_question(meeting.id, uid, text, exp)
        questions.append(row)
    add_like(questions[0].id, "risk")
    add_like(questions[0].id, "product")
    items = [IntakeQuestion(q.id, q.user_id, q.text, q.likes, q.created_at, q.expertise.split(",") if q.expertise else []) for q in get_questions(meeting.id)]
    result = await QuestionPipeline().run(meeting_id=meeting.id, meeting_title=meeting.title, domain=meeting.domain, agenda=meeting.agenda, questions=items)
    result.categories = PriorityAgent().rank(result.categories)
    update_questions_category(meeting.id, {qid:c.category_id for c in result.categories for qid in c.source_question_ids}, {q.id: next(c.priority_score for c in result.categories if q.id in c.source_question_ids) for q in items})
    save_categories(meeting.id, result.categories)
    add_event(meeting.id, "PILOT_DEMO_READY", {"categories": len(result.categories), "fallback": result.fallback}, "system")
    if result.categories:
        c = result.categories[0]
        n = c.nominees[0]
        decision, asked = add_decision(meeting.id, c.category_id, ModeratorAction.APPROVE, n.nominee_id, None, "moderator", "pilot demo", n.text)
        if asked:
            add_event(meeting.id, "MODERATOR_APPROVED", {"asked_question_id": asked.id, "nominee_id": n.nominee_id}, "moderator")
            outcome = add_outcome(asked.id, "answered", 5, "Pilot demo answer captured")
            add_event(meeting.id, "QUESTION_OUTCOME_RECORDED", {"asked_question_id": asked.id, "outcome": outcome.outcome, "usefulness": outcome.usefulness}, None)
    report = build_evidence_report(meeting.id)
    print(json.dumps(report_dict(report), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
