from __future__ import annotations
from dataclasses import dataclass
from app.core.models import QuestionCategory
from app.services.ranking import KPIWeights, mmr_select
from app.services.semantic import SemanticEncoder


@dataclass(frozen=True)
class PriorityPolicy:
    weights: KPIWeights = KPIWeights()
    diversity_lambda: float = 0.72


class PriorityAgent:
    """Policy-bounded ordering agent. It cannot approve, ask, or mutate meeting state."""
    def __init__(self, policy: PriorityPolicy | None = None, semantic=None) -> None:
        self.policy = policy or PriorityPolicy()
        self.semantic = semantic or SemanticEncoder()

    def rank(self, categories: list[QuestionCategory]) -> list[QuestionCategory]:
        if len(categories) <= 1:
            return categories
        picked = mmr_select(
            [(c, c.priority_score) for c in categories],
            similarity_fn=lambda a, b: self.semantic.pairwise(a.intent, b.intent),
            limit=len(categories),
            lambda_=self.policy.diversity_lambda,
        )
        for order, (category, mmr_score) in enumerate(picked):
            category.priority_explanation["mmr_selection_score"] = float(mmr_score)
            category.priority_explanation["selection_order"] = float(order + 1)
        return [c for c, _ in picked]
