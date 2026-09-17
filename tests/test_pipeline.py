import pytest
from datetime import datetime, timezone
from app.services.pipeline import QuestionPipeline, IntakeQuestion


@pytest.mark.asyncio
async def test_fallback_pipeline_creates_nominees(monkeypatch):
    async def fail(*args, **kwargs):
        raise RuntimeError("no llm")
    p = QuestionPipeline()
    monkeypatch.setattr(p.llm, "structured", fail)
    qs = [
        IntakeQuestion("1", "u1", "What is the expected launch date?", 2, datetime.now(timezone.utc), []),
        IntakeQuestion("2", "u2", "When will the product launch?", 1, datetime.now(timezone.utc), []),
        IntakeQuestion("3", "u3", "What is the hiring budget?", 0, datetime.now(timezone.utc), []),
    ]
    result = await p.run(meeting_title="Roadmap", domain="product", agenda="launch", questions=qs)
    assert result.fallback is True
    assert len(result.categories) >= 2
    assert all(c.nominees for c in result.categories)
