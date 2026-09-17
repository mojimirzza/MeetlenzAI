from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class CoverageSignal:
    expertise: str
    participant_count: int
    question_count: int
    category_count: int
    coverage: float
    status: str
    rationale: str


def _status(score: float) -> str:
    if score >= 0.67:
        return "well_covered"
    if score >= 0.34:
        return "partially_covered"
    return "underrepresented"


def build_coverage_signals(participants, questions) -> list[CoverageSignal]:
    participants_by_expertise: dict[str, set[str]] = defaultdict(set)
    expertise_names: set[str] = set()
    for p in participants:
        for exp in (p.expertise.split(",") if getattr(p, "expertise", "") else []):
            exp = exp.strip()
            if not exp:
                continue
            expertise_names.add(exp)
            participants_by_expertise[exp].add(p.user_id)

    questions_by_expertise: dict[str, list] = defaultdict(list)
    for q in questions:
        for exp in (q.expertise.split(",") if getattr(q, "expertise", "") else []):
            exp = exp.strip()
            if exp:
                questions_by_expertise[exp].append(q)
                expertise_names.add(exp)

    signals: list[CoverageSignal] = []
    for exp in sorted(expertise_names):
        pids = participants_by_expertise.get(exp, set())
        qs = questions_by_expertise.get(exp, [])
        distinct_participants = {q.user_id for q in qs}
        participant_coverage = len(distinct_participants) / max(1, len(pids)) if pids else 0.0
        # One or more questions from the expertise establishes demand coverage; additional questions
        # contribute with diminishing returns rather than dominating the signal.
        question_signal = min(1.0, len(qs) / 3.0)
        score = 0.60 * participant_coverage + 0.40 * question_signal
        status = _status(score)
        if not qs:
            rationale = f"No submitted questions were tagged with {exp}."
        elif distinct_participants and pids and len(distinct_participants) < len(pids):
            rationale = f"Questions exist for {exp}, but only {len(distinct_participants)} of {len(pids)} participants contributed one."
        else:
            rationale = f"{len(qs)} question(s) cover {exp} from {len(distinct_participants)} participant(s)."
        signals.append(CoverageSignal(exp, len(pids), len(qs), len({q.category_id for q in qs if getattr(q, 'category_id', None)}), round(score, 4), status, rationale))
    return signals


def coverage_report(participants, questions) -> dict:
    signals = build_coverage_signals(participants, questions)
    return {
        "signals": [s.__dict__ for s in signals],
        "underrepresented": [s.expertise for s in signals if s.status == "underrepresented"],
        "partially_covered": [s.expertise for s in signals if s.status == "partially_covered"],
        "well_covered": [s.expertise for s in signals if s.status == "well_covered"],
        "disclaimer": "Coverage is an evidence-backed moderator signal derived from declared participant expertise and submitted questions; it does not assert that an absent perspective is objectively needed.",
    }
