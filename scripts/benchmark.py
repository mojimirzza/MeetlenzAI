from __future__ import annotations

# Allow direct execution from the repository root (e.g. `python scripts/benchmark.py`).
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
import json
import time
from datetime import datetime, timezone
from collections import Counter

from app.services.pipeline import IntakeQuestion, QuestionPipeline
from app.agents.priority_agent import PriorityAgent
from app.services.ranking import diminishing_ratio

INTENTS = {
    "launch": [
        "What is the target production launch date?",
        "Are we still aiming for the planned go-live date?",
        "When is the customer-facing release expected?",
        "What date are we committing to for production?",
    ],
    "rollback": [
        "What is the rollback plan for the database migration?",
        "How do we revert safely if the migration fails?",
        "What is our migration rollback procedure?",
        "Can we restore the previous database state after a bad migration?",
    ],
    "compliance": [
        "Which audit controls cover the migration?",
        "How do we ensure the migration meets compliance requirements?",
    ],
    "observability": [
        "Which signals tell us the new architecture is degrading?",
        "What monitoring will detect production degradation?",
    ],
}
PARTICIPANTS = {
    "launch": ("product", ["product", "launch"]),
    "rollback": ("backend", ["backend", "databases"]),
    "compliance": ("security", ["security", "compliance"]),
    "observability": ("sre", ["observability", "reliability"]),
}


def pair_f1(pred_groups: list[list[int]], truth: list[str]) -> float:
    pred: set[tuple[int, int]] = set()
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


def build_items() -> tuple[list[IntakeQuestion], list[str]]:
    now = datetime.now(timezone.utc)
    items: list[IntakeQuestion] = []
    truth: list[str] = []
    for intent, texts in INTENTS.items():
        uid, expertise = PARTICIPANTS[intent]
        for idx, text in enumerate(texts):
            likes = 4 if intent == "launch" else 3 if intent == "rollback" else 1
            items.append(IntakeQuestion(f"bq-{len(items)+1:03d}", uid, text, likes, now, expertise))
            truth.append(intent)
    return items, truth


def popularity_baseline(items: list[IntakeQuestion], truth: list[str], k: int = 5) -> dict:
    id_to_i = {q.id: i for i, q in enumerate(items)}
    selected = sorted(items, key=lambda q: (q.likes, q.created_at), reverse=True)[:k]
    labels = [truth[id_to_i[q.id]] for q in selected]
    return {"labels": labels, "unique_intents": len(set(labels))}


async def main() -> None:
    items, truth = build_items()
    pipeline = QuestionPipeline()
    start = time.perf_counter()
    result = await pipeline.run(
        meeting_id="benchmark",
        meeting_title="Architecture Launch Review",
        domain="fintech-architecture",
        agenda="launch, migration safety, compliance, observability",
        questions=items,
    )
    result.categories = PriorityAgent().rank(result.categories)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    id_to_i = {q.id: i for i, q in enumerate(items)}
    pred = [[id_to_i[qid] for qid in c.source_question_ids] for c in result.categories]
    labels = [truth[id_to_i[c.source_question_ids[0]]] for c in result.categories if c.source_question_ids]
    result_payload = {
        "status": "controlled_synthetic_benchmark",
        "questions": len(items),
        "ground_truth_intents": len(set(truth)),
        "predicted_intents": len(result.categories),
        "pair_f1": round(pair_f1(pred, truth), 4),
        "compression_rate": round(1 - len(result.categories) / len(items), 4),
        "pipeline_latency_ms": elapsed,
        "meetlens_top5_unique_intents": len(set(labels[:5])),
        "baseline": popularity_baseline(items, truth),
        "note": "Synthetic controlled evidence only; not external customer validation.",
    }
    print(json.dumps(result_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
