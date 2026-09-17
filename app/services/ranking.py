from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class KPIWeights:
    meeting_relevance: float = 0.28
    frequency: float = 0.18
    unique_participants: float = 0.16
    likes: float = 0.12
    expertise_fit: float = 0.10
    novelty: float = 0.08
    recency: float = 0.08


DEFAULT_WEIGHTS = KPIWeights()


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def diminishing_ratio(value: int | float, maximum: int | float) -> float:
    if value <= 0 or maximum <= 0:
        return 0.0
    return _clip(math.log1p(value) / math.log1p(maximum))


def category_priority(*, relevance: float, question_count: int, participant_count: int, likes: int,
                      expertise_fit: float, novelty: float, newest_at: datetime,
                      max_question_count: int, max_participant_count: int, max_likes: int,
                      weights: KPIWeights = DEFAULT_WEIGHTS) -> tuple[float, dict[str, float]]:
    if newest_at.tzinfo is None:
        newest_at = newest_at.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (datetime.now(timezone.utc) - newest_at).total_seconds() / 3600)
    parts = {
        "meeting_relevance": _clip(relevance),
        "frequency": diminishing_ratio(question_count, max_question_count),
        "unique_participants": diminishing_ratio(participant_count, max_participant_count),
        "likes": diminishing_ratio(likes, max_likes),
        "expertise_fit": _clip(expertise_fit),
        "novelty": _clip(novelty),
        "recency": _clip(math.exp(-age_hours / 24.0)),
    }
    score = sum(getattr(weights, key) * value for key, value in parts.items())
    return _clip(score), parts


def mmr_select(items: Iterable[tuple[object, float]], similarity_fn, limit: int = 5, lambda_: float = 0.72):
    pool = list(items)
    selected: list[tuple[object, float]] = []
    while pool and len(selected) < limit:
        best_idx = 0
        best_value = -float("inf")
        for i, (item, relevance) in enumerate(pool):
            redundancy = 0.0
            for prior, _ in selected:
                redundancy = max(redundancy, float(similarity_fn(item, prior)))
            value = lambda_ * relevance - (1 - lambda_) * redundancy
            if value > best_value:
                best_value, best_idx = value, i
        selected.append(pool.pop(best_idx))
    return selected

# Backward-compatible primitive for existing integrations/tests.
def question_score(*, relevance: float, frequency: int, likes: int, expertise_fit: float,
                   novelty: float, created_at: datetime, max_frequency: int, max_likes: int,
                   weights: KPIWeights = KPIWeights(meeting_relevance=0.30, frequency=0.22,
                                                    unique_participants=0.0, likes=0.18,
                                                    expertise_fit=0.12, novelty=0.10, recency=0.08)) -> tuple[float, dict[str, float]]:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (datetime.now(timezone.utc) - created_at).total_seconds() / 3600)
    parts = {
        "meeting_relevance": _clip(relevance),
        "frequency": diminishing_ratio(frequency, max_frequency),
        "likes": diminishing_ratio(likes, max_likes),
        "expertise_fit": _clip(expertise_fit),
        "novelty": _clip(novelty),
        "recency": _clip(math.exp(-age_hours / 24.0)),
    }
    score = (weights.meeting_relevance*parts["meeting_relevance"] + weights.frequency*parts["frequency"] +
             weights.likes*parts["likes"] + weights.expertise_fit*parts["expertise_fit"] +
             weights.novelty*parts["novelty"] + weights.recency*parts["recency"])
    return _clip(score), parts
