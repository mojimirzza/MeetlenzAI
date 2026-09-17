from __future__ import annotations
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.coverage import coverage_report
from app.storage.db import (
    get_meeting, get_questions, get_participants, get_events, get_categories,
    get_nominees, get_decisions, get_asked_questions, get_outcomes,
)


@dataclass(frozen=True)
class EvidenceReport:
    meeting_id: str
    generated_at: str
    summary: dict[str, Any]
    metrics: dict[str, Any]
    decisions: list[dict[str, Any]]
    outcomes: list[dict[str, Any]]
    audit: list[dict[str, Any]]


def _pct(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def build_evidence_report(meeting_id: str) -> EvidenceReport:
    meeting = get_meeting(meeting_id)
    if meeting is None:
        raise ValueError("meeting not found")

    participants = get_participants(meeting_id)
    questions = get_questions(meeting_id)
    categories = get_categories(meeting_id)
    nominees = get_nominees(meeting_id)
    decisions = get_decisions(meeting_id)
    asked = get_asked_questions(meeting_id)
    outcomes = get_outcomes(meeting_id)
    events = get_events(meeting_id)

    semantic_compression = 1.0 - _pct(len(categories), len(questions))
    accepted = [d for d in decisions if d.action in {"approve", "edit"}]
    edited = [d for d in decisions if d.action == "edit"]
    rejected = [d for d in decisions if d.action == "reject"]
    answered = [o for o in outcomes if o.outcome == "answered"]

    category_sizes = Counter(q.category_id for q in questions if q.category_id)
    participant_coverage = len({q.user_id for q in questions if q.category_id})

    coverage = coverage_report(participants, questions)

    report = EvidenceReport(
        meeting_id=meeting_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary={
            "title": meeting.title,
            "domain": meeting.domain,
            "agenda": meeting.agenda,
            "participants": len(participants),
            "questions": len(questions),
            "intents": len(categories),
            "nominees": len(nominees),
            "asked_questions": len(asked),
        },
        metrics={
            "semantic_compression_rate": round(semantic_compression, 4),
            "moderator_acceptance_rate": _pct(len(accepted), len(decisions)),
            "moderator_edit_rate": _pct(len(edited), len(decisions)),
            "moderator_rejection_rate": _pct(len(rejected), len(decisions)),
            "answer_rate": _pct(len(answered), len(outcomes)),
            "question_coverage_participants": participant_coverage,
            "categories_with_multiple_questions": sum(1 for v in category_sizes.values() if v > 1),
            "event_count": len(events),
            "coverage_underrepresented": coverage["underrepresented"],
            "coverage_partially_covered": coverage["partially_covered"],
            "coverage_well_covered": coverage["well_covered"],
        },
        decisions=[{
            "id": d.id,
            "category_id": d.category_id,
            "action": d.action,
            "nominee_id": d.nominee_id,
            "edited_text": d.edited_text,
            "moderator_user_id": d.moderator_user_id,
            "reason": d.reason,
            "created_at": d.created_at.isoformat(),
        } for d in decisions],
        outcomes=[{
            "id": o.id,
            "asked_question_id": o.asked_question_id,
            "outcome": o.outcome,
            "usefulness": o.usefulness,
            "notes": o.notes,
            "created_at": o.created_at.isoformat(),
        } for o in outcomes],
        audit=[{
            "id": e.id,
            "event_type": e.event_type,
            "actor_id": e.actor_id,
            "payload": json.loads(e.payload or "{}"),
            "trace_id": e.trace_id,
            "created_at": e.created_at.isoformat(),
        } for e in events],
    )
    return report


def report_dict(report: EvidenceReport) -> dict[str, Any]:
    return {
        "meeting_id": report.meeting_id,
        "generated_at": report.generated_at,
        "summary": report.summary,
        "metrics": report.metrics,
        "decisions": report.decisions,
        "outcomes": report.outcomes,
        "audit": report.audit,
    }
