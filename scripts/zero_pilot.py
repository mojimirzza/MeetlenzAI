from __future__ import annotations

# Allow direct execution from the repository root (e.g. `python scripts/benchmark.py`).
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import asyncio, json, math, time
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from app.services.pipeline import QuestionPipeline, IntakeQuestion
from app.agents.priority_agent import PriorityAgent
from app.services.coverage import coverage_report

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "zero_pilot"

SCENARIO = {
    "meeting_title": "Fintech Architecture & Launch Readiness Review",
    "domain": "fintech-architecture",
    "agenda": "launch readiness, migration safety, compliance, observability, performance, resilience",
    "participants": [
        ("architect", "Architect", ["architecture", "resilience"]),
        ("backend", "Backend Lead", ["backend", "databases"]),
        ("security", "Security Lead", ["security", "compliance"]),
        ("sre", "SRE Lead", ["observability", "reliability"]),
        ("product", "Product Lead", ["product", "launch"]),
        ("risk", "Risk Lead", ["risk", "compliance"]),
        ("performance", "Performance Lead", ["performance", "capacity"]),
        ("customer", "Customer Lead", ["customer", "operations"]),
    ],
}

INTENTS = {
    "launch": [
        "What is the target production launch date?",
        "Are we still aiming for the planned go-live date?",
        "When is the customer-facing release expected?",
        "What date are we committing to for production?",
        "When will customers actually receive the release?",
        "Has the launch timing been confirmed?",
        "Can the team confirm the go-live window?",
        "What is the current release target?",
    ],
    "rollback": [
        "What is the rollback plan for the database migration?",
        "How do we revert safely if the migration fails?",
        "What is our migration rollback procedure?",
        "Can we restore the previous database state after a bad migration?",
        "What is the tested recovery path for a failed migration?",
        "How quickly can we roll back the schema change?",
        "Which rollback mechanism will we use during migration?",
    ],
    "compliance": [
        "Which audit controls cover the migration?",
        "How do we ensure the migration meets compliance requirements?",
        "What evidence do we need for the audit?",
        "Which controls prevent a migration compliance gap?",
        "How will we demonstrate regulatory compliance for this change?",
    ],
    "observability": [
        "Which signals tell us the new architecture is degrading?",
        "What monitoring will detect production degradation?",
        "Which metrics should trigger an incident?",
        "How will we know if the service becomes unhealthy after launch?",
        "What observability signals should we watch during rollout?",
        "How early can monitoring detect a production problem?",
    ],
    "performance": [
        "What latency target are we committing to?",
        "How will the new architecture affect response time?",
        "What performance threshold should block the release?",
        "Do we have an agreed target for API latency?",
    ],
    "resilience": [
        "What is the failover strategy if the primary service fails?",
        "How quickly can we recover from a regional failure?",
        "What recovery objective are we using for the new architecture?",
    ],
    "capacity": [
        "How much traffic can the new architecture handle?",
        "What is the expected capacity limit at launch?",
    ],
    "customer_impact": [
        "What customer impact should we expect during migration?",
    ],
}

PARTICIPANT_FOR_INTENT = {
    "launch": "product", "rollback": "backend", "compliance": "security", "observability": "sre",
    "performance": "performance", "resilience": "architect", "capacity": "performance", "customer_impact": "customer",
}


def pair_f1(pred_groups: list[list[int]], truth: list[str]) -> float:
    pred = set(); tp = fp = fn = 0
    for g in pred_groups:
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                pred.add(tuple(sorted((g[i], g[j]))))
    truth_pairs = {(i, j) for i in range(len(truth)) for j in range(i + 1, len(truth)) if truth[i] == truth[j]}
    tp = len(pred & truth_pairs)
    fp = len(pred - truth_pairs)
    fn = len(truth_pairs - pred)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def baseline_top_questions(items: list[IntakeQuestion], k: int = 5) -> list[IntakeQuestion]:
    # Manual-style frequency/popularity baseline: rank individual questions by likes, then recency.
    return sorted(items, key=lambda q: (q.likes, q.created_at), reverse=True)[:k]


async def main():
    now = datetime.now(timezone.utc)
    items: list[IntakeQuestion] = []
    truth: list[str] = []
    expertise_by_user = {uid: exp for uid, _, exp in SCENARIO["participants"]}
    for intent, texts in INTENTS.items():
        uid = PARTICIPANT_FOR_INTENT[intent]
        for idx, text in enumerate(texts):
            qid = f"zq-{len(items)+1:03d}"
            # Popularity is intentionally skewed: launch/rollback receive more likes than rarer but important concerns.
            likes = 4 if intent == "launch" else 3 if intent == "rollback" else 1 if intent in {"compliance", "observability"} else 0
            items.append(IntakeQuestion(qid, uid, text, likes, now, expertise_by_user[uid]))
            truth.append(intent)

    pipeline = QuestionPipeline()
    started = time.perf_counter()
    result = await pipeline.run(
        meeting_id="zero-pilot",
        meeting_title=SCENARIO["meeting_title"],
        domain=SCENARIO["domain"],
        agenda=SCENARIO["agenda"],
        questions=items,
    )
    result.categories = PriorityAgent().rank(result.categories)
    pipeline_ms = round((time.perf_counter() - started) * 1000, 2)

    pred_groups = [[truth.index(next(t for t in truth if False))] for _ in []]  # structural placeholder; replaced below
    id_to_idx = {q.id: i for i, q in enumerate(items)}
    pred_groups = [[id_to_idx[qid] for qid in c.source_question_ids] for c in result.categories]
    f1 = pair_f1(pred_groups, truth)

    selected = result.categories[:5]
    baseline = baseline_top_questions(items, 5)
    baseline_intents = [truth[id_to_idx[q.id]] for q in baseline]
    meetlens_intents = []
    for c in selected:
        members = [truth[id_to_idx[qid]] for qid in c.source_question_ids]
        meetlens_intents.append(Counter(members).most_common(1)[0][0])

    coverage = coverage_report(
        [type("P", (), {"user_id": uid, "expertise": ",".join(exp)})() for uid, _, exp in SCENARIO["participants"]],
        [type("Q", (), {"user_id": q.user_id, "expertise": ",".join(q.expertise), "category_id": next((c.category_id for c in result.categories if q.id in c.source_question_ids), None)})() for q in items],
    )

    baseline_unique = len(set(baseline_intents))
    meetlens_unique = len(set(meetlens_intents))
    report = {
        "scenario": SCENARIO,
        "status": "synthetic_zero_pilot",
        "warning": "Synthetic controlled evidence only; not external customer validation.",
        "input": {"questions": len(items), "ground_truth_intents": len(set(truth)), "participants": len(SCENARIO["participants"])},
        "meetlens": {
            "fallback": result.fallback,
            "predicted_intents": len(result.categories),
            "compression_rate": round(1 - len(result.categories)/len(items), 4),
            "cluster_pair_f1": round(f1, 4),
            "top5_intents": meetlens_intents,
            "top5_unique_intents": meetlens_unique,
            "pipeline_latency_ms": pipeline_ms,
            "top5_categories": [
                {"label": c.label, "intent": c.intent, "priority": c.priority_score, "support": len(c.source_question_ids)}
                for c in selected
            ],
        },
        "baseline": {
            "method": "manual-style individual-question popularity/frequency proxy",
            "top5_intents": baseline_intents,
            "top5_unique_intents": baseline_unique,
            "intent_redundancy": round(1 - baseline_unique / len(baseline_intents), 4),
        },
        "coverage": coverage,
        "interpretation": {
            "core_question": "Does semantic compression preserve useful diversity better than popularity-only triage?",
            "finding": "MeetLens selects by intent-level candidates rather than individual raw questions; the benchmark should therefore be judged on intent coverage, redundancy, and moderator usefulness—not only compression.",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raw_questions.json").write_text(json.dumps([q.__dict__ for q in items], ensure_ascii=False, indent=2, default=str))
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    md = [
        "# MeetLens Zero Pilot",
        "",
        "> Synthetic controlled evidence only; not external customer validation.",
        "",
        f"- Questions: {len(items)}",
        f"- Ground-truth intents: {len(set(truth))}",
        f"- MeetLens predicted intents: {len(result.categories)}",
        f"- Pair F1: {f1:.4f}",
        f"- MeetLens top-5 unique intents: {meetlens_unique}/5",
        f"- Baseline top-5 unique intents: {baseline_unique}/5",
        f"- MeetLens compression: {1 - len(result.categories)/len(items):.4f}",
        "",
        "## MeetLens top-5",
    ]
    for c in selected:
        md.append(f"- **{c.label}** — {c.intent} — priority={c.priority_score:.3f} — support={len(c.source_question_ids)}")
    md += ["", "## Baseline top-5 intent labels", "- " + ", ".join(baseline_intents), "", "## Blind Spot Radar", "The radar flags underrepresented declared expertise areas as moderator signals; it does not assert that an absent perspective is objectively required.", "", "## Next Evidence Gate", "Run the same scorecard in 3 real technical/design-review meetings and compare moderator acceptance/edit/rejection and triage time against baseline."]
    (OUT / "report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
