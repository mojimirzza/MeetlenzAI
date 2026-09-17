from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence

@dataclass(frozen=True)
class CatalystGroup:
    index: int
    intent: str
    label: str
    question_ids: tuple[str, ...]
    questions: tuple[str, ...]

@dataclass(frozen=True)
class CatalystContext:
    meeting_title: str
    domain: str
    agenda: str
    groups: tuple[CatalystGroup, ...]

@dataclass(frozen=True)
class CatalystInsight:
    kind: str
    source_group_indexes: tuple[int, ...]
    source_question_ids: tuple[str, ...]
    insight: str
    candidate_angle: str
    confidence: float
    novelty: float
    evidence: tuple[str, ...] = field(default_factory=tuple)
    handoff_payload: str = ""

    @property
    def recommended(self) -> bool:
        return bool(self.insight and self.candidate_angle)
