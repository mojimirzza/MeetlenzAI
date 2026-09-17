from __future__ import annotations
from typing import Sequence

from app.catalyst import CatalystContext, CatalystGroup, CatalystInsight, CreativeCatalystEngine


class CreativeCatalyst:
    """Thin MeetLens adapter around the independent Catalyst module."""

    def __init__(self) -> None:
        self.engine = CreativeCatalystEngine()

    def analyze(
        self,
        *,
        groups: Sequence[Sequence[object]],
        group_intents: dict[int, str],
        group_labels: dict[int, str] | None = None,
        meeting_title: str = "",
        domain: str = "",
        agenda: str = "",
        semantic=None,
    ) -> CatalystInsight | None:
        labels = group_labels or {}
        packaged: list[CatalystGroup] = []
        for idx, group in enumerate(groups):
            question_texts = tuple(
                str(getattr(q, "text", "")).strip()
                for q in group
                if getattr(q, "text", None)
            )
            question_ids = tuple(
                str(getattr(q, "id"))
                for q in group
                if getattr(q, "id", None)
            )
            packaged.append(
                CatalystGroup(
                    index=idx,
                    intent=str(group_intents.get(idx, "")).strip(),
                    label=str(labels.get(idx, "")).strip(),
                    question_ids=question_ids,
                    questions=question_texts,
                )
            )

        return self.engine.analyze(
            CatalystContext(
                meeting_title=meeting_title,
                domain=domain,
                agenda=agenda,
                groups=tuple(packaged),
            )
        )
