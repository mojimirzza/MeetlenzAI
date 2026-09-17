from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.services.pipeline import IntakeQuestion, QuestionPipeline
from app.agents.priority_agent import PriorityAgent
from app.services.semantic import keyword_overlap


@dataclass(frozen=True)
class FixtureQuestion:
    qid: str
    user_id: str
    text: str
    intent: str
    expertise: tuple[str, ...]
    likes: int


SCENARIOS: list[tuple[str, list[FixtureQuestion]]] = [
    (
        "architecture_review",
        [
            FixtureQuestion("a1", "u1", "What is the rollback plan for the database migration?", "migration", ("database",), 3),
            FixtureQuestion("a2", "u2", "How do we revert the database change if migration fails?", "migration", ("backend",), 2),
            FixtureQuestion("a3", "u3", "What is the target production launch date?", "launch", ("product",), 3),
            FixtureQuestion("a4", "u4", "When will customers see the new release in production?", "launch", ("product",), 1),
            FixtureQuestion("a5", "u1", "Which signals tell us the new architecture is degrading?", "observability", ("architecture",), 2),
            FixtureQuestion("a6", "u4", "Which metrics should trigger an incident for the new system?", "observability", ("observability",), 1),
            FixtureQuestion("a7", "u2", "How do we satisfy audit controls during migration?", "compliance", ("risk",), 2),
            FixtureQuestion("a8", "u3", "What controls prove the migration remains compliant?", "compliance", ("compliance",), 1),
        ],
    ),
    (
        "incident_review",
        [
            FixtureQuestion("i1", "u1", "What caused the outage?", "root_cause", ("backend",), 4),
            FixtureQuestion("i2", "u2", "What was the root cause of the production incident?", "root_cause", ("operations",), 2),
            FixtureQuestion("i3", "u3", "How quickly did we detect the incident?", "detection", ("observability",), 2),
            FixtureQuestion("i4", "u4", "What is our detection time for incidents?", "detection", ("observability",), 1),
            FixtureQuestion("i5", "u1", "What prevents this failure from happening again?", "prevention", ("architecture",), 3),
            FixtureQuestion("i6", "u3", "Which safeguards stop a repeat of this outage?", "prevention", ("risk",), 1),
        ],
    ),
    (
        "fintech_design",
        [
            FixtureQuestion("f1", "u1", "How will we recover if the primary database fails?", "resilience", ("database",), 4),
            FixtureQuestion("f2", "u2", "What is the failover process when the primary DB goes down?", "resilience", ("distributed-systems",), 2),
            FixtureQuestion("f3", "u3", "How do we keep transaction processing auditable?", "auditability", ("compliance",), 3),
            FixtureQuestion("f4", "u4", "Which controls preserve an auditable transaction trail?", "auditability", ("risk",), 1),
            FixtureQuestion("f5", "u1", "What is the expected transaction latency after the redesign?", "performance", ("backend",), 3),
            FixtureQuestion("f6", "u2", "How fast should transactions complete with the new architecture?", "performance", ("architecture",), 1),
        ],
    ),
]


def pairwise_scores(predicted: list[list[int]], truth: list[list[int]]) -> tuple[float, float, float]:
    def pairs(groups: list[list[int]]) -> set[tuple[int, int]]:
        out: set[tuple[int, int]] = set()
        for g in groups:
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    out.add((g[i], g[j]))
        return out

    pp = pairs(predicted)
    tt = pairs(truth)
    tp = len(pp & tt)
    precision = tp / len(pp) if pp else 1.0
    recall = tp / len(tt) if tt else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def build_truth(questions: list[FixtureQuestion]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, q in enumerate(questions):
        groups[q.intent].append(i)
    return list(groups.values())


async def evaluate_scenario(name: str, rows: list[FixtureQuestion]) -> dict:
    p = QuestionPipeline()
    async def offline_llm(*_args, **_kwargs):
        raise RuntimeError("intentional offline evaluation")
    p.llm.structured = offline_llm
    now = datetime.now(timezone.utc)
    questions = [
        IntakeQuestion(r.qid, r.user_id, r.text, r.likes, now, list(r.expertise))
        for r in rows
    ]
    result = await p.run(
        meeting_title=name,
        domain="technical-review",
        agenda="design decisions, risk, rollout, reliability",
        questions=questions,
        meeting_id=f"fixture-{name}",
    )
    result.categories = PriorityAgent().rank(result.categories)
    predicted = [
        [i for i, q in enumerate(rows) if q.qid in c.source_question_ids]
        for c in result.categories
    ]
    truth = build_truth(rows)
    precision, recall, f1 = pairwise_scores(predicted, truth)
    multi = sum(1 for g in predicted if len(g) > 1)
    selected_participants = set()
    for g in predicted:
        if g:
            selected_participants.add(rows[g[0]].user_id)
    return {
        "scenario": name,
        "questions": len(rows),
        "predicted_intents": len(result.categories),
        "truth_intents": len(truth),
        "multi_question_intents": multi,
        "semantic_compression_rate": round(1 - len(result.categories) / len(rows), 4),
        "cluster_pair_precision": precision,
        "cluster_pair_recall": recall,
        "cluster_pair_f1": f1,
        "participant_coverage_in_intents": len({r.user_id for r in rows if r}),
        "nominee_count": sum(len(c.nominees) for c in result.categories),
        "avg_nominees_per_intent": round(sum(len(c.nominees) for c in result.categories) / max(1, len(result.categories)), 2),
        "fallback_mode": result.fallback,
    }


async def main() -> None:
    rows = [await evaluate_scenario(name, fixture) for name, fixture in SCENARIOS]
    aggregate = {
        "scenarios": len(rows),
        "questions": sum(r["questions"] for r in rows),
        "mean_cluster_pair_f1": round(sum(r["cluster_pair_f1"] for r in rows) / len(rows), 4),
        "mean_compression_rate": round(sum(r["semantic_compression_rate"] for r in rows) / len(rows), 4),
        "mean_nominees_per_intent": round(sum(r["avg_nominees_per_intent"] for r in rows) / len(rows), 2),
        "fully_offline": all(r["fallback_mode"] for r in rows),
    }
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PRE_PILOT_CONTROLLED_EVIDENCE",
        "warning": "Synthetic fixtures only. This is not external customer validation.",
        "aggregate": aggregate,
        "scenarios": rows,
    }
    out_path = Path("artifacts/pilot_evidence.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
