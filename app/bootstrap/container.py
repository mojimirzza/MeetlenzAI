from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache

from app.agents.priority_agent import PriorityAgent
from app.services.llm import LLMClient
from app.services.semantic import SemanticEncoder
from app.services.creative_catalyst import CreativeCatalyst
from app.features.meeting.application.pipeline import QuestionPipeline
from app.platform.resilience import AsyncCircuitBreaker


@dataclass
class AppContainer:
    llm: LLMClient
    semantic: SemanticEncoder
    catalyst: CreativeCatalyst
    pipeline: QuestionPipeline
    priority_agent: PriorityAgent
    llm_breaker: AsyncCircuitBreaker


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    llm = LLMClient()
    semantic = SemanticEncoder()
    catalyst = CreativeCatalyst()
    priority_agent = PriorityAgent(semantic=semantic)
    pipeline = QuestionPipeline(llm=llm, semantic=semantic, catalyst=catalyst)
    return AppContainer(
        llm=llm,
        semantic=semantic,
        catalyst=catalyst,
        pipeline=pipeline,
        priority_agent=priority_agent,
        llm_breaker=AsyncCircuitBreaker(failure_threshold=3, reset_after=30),
    )
