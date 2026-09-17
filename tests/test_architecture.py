import asyncio

from app.bootstrap.container import get_container
from app.features.meeting.application.pipeline import QuestionPipeline
from app.services.pipeline import QuestionPipeline as CompatPipeline
from app.platform.resilience import AsyncCircuitBreaker, CircuitOpenError


def test_modular_monolith_composition_root_is_stable():
    c = get_container()
    assert isinstance(c.pipeline, QuestionPipeline)
    assert c.pipeline.llm is c.llm
    assert c.pipeline.semantic is c.semantic
    assert c.pipeline.catalyst is c.catalyst
    assert CompatPipeline is QuestionPipeline
    assert isinstance(c.llm_breaker, AsyncCircuitBreaker)


def test_circuit_breaker_opens_after_failures_and_resets():
    async def scenario():
        breaker = AsyncCircuitBreaker(failure_threshold=2, reset_after=0.01)
        async def fail():
            raise RuntimeError("boom")
        for _ in range(2):
            try:
                await breaker.call(fail)
            except RuntimeError:
                pass
        try:
            await breaker.call(fail)
        except CircuitOpenError:
            blocked = True
        else:
            blocked = False
        assert blocked
        await asyncio.sleep(0.02)
        assert await breaker.call(lambda: asyncio.sleep(0, result=42)) == 42
    asyncio.run(scenario())
