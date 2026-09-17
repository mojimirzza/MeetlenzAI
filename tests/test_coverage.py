from types import SimpleNamespace
from app.services.coverage import coverage_report


def test_blind_spot_radar_is_evidence_backed():
    participants = [
        SimpleNamespace(user_id="arch", expertise="architecture,security"),
        SimpleNamespace(user_id="backend", expertise="backend,databases"),
        SimpleNamespace(user_id="risk", expertise="risk,compliance"),
    ]
    questions = [
        SimpleNamespace(user_id="arch", expertise="architecture", category_id="cat-a"),
        SimpleNamespace(user_id="backend", expertise="backend", category_id="cat-b"),
    ]
    report = coverage_report(participants, questions)
    assert "security" in report["underrepresented"]
    assert "compliance" in report["underrepresented"]
    assert "architecture" in report["well_covered"]
    assert "disclaimer" in report

import asyncio
from datetime import datetime, timezone
from app.services.pipeline import QuestionPipeline, IntakeQuestion
from scripts.zero_pilot import INTENTS, PARTICIPANT_FOR_INTENT, pair_f1

def test_zero_pilot_fallback_recovers_intents_from_strong_anchors():
    now = datetime.now(timezone.utc)
    qs=[]; truth=[]
    for intent, texts in INTENTS.items():
        uid=PARTICIPANT_FOR_INTENT[intent]
        for i,t in enumerate(texts):
            qs.append(IntakeQuestion(f"q-{len(qs)}",uid,t,0,now,[])); truth.append(intent)
    groups=QuestionPipeline().fallback_groups(qs)
    assert len(groups)==8
    assert pair_f1(groups, truth) == 1.0
