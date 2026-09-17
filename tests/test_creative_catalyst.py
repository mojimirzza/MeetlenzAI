from datetime import datetime, timezone

import pytest

from app.services.creative_catalyst import CreativeCatalyst
from app.services.pipeline import IntakeQuestion, QuestionPipeline
from app.services.semantic import SemanticEncoder


def q(qid: str, text: str) -> IntakeQuestion:
    return IntakeQuestion(qid, "u", text, 0, datetime.now(timezone.utc), [])


def test_catalyst_finds_cross_group_angle_without_llm():
    groups = [
        [q("q1", "Why is onboarding taking so long?")],
        [q("q2", "Why has activation dropped for new users?")],
    ]
    out = CreativeCatalyst().analyze(
        groups=groups,
        group_intents={0: "onboarding new users", 1: "activation new users"},
        semantic=SemanticEncoder(),
    )
    assert out is not None
    assert out.kind == "cross_cluster_connection"
    assert set(out.source_group_indexes) == {0, 1}
    assert set(out.source_question_ids) == {"q1", "q2"}
    assert "onboarding new users" in out.candidate_angle
    assert "activation new users" in out.candidate_angle


def test_catalyst_is_silent_when_only_one_group():
    out = CreativeCatalyst().analyze(
        groups=[[q("q1", "What is the launch date?")]],
        group_intents={0: "launch timing"},
        semantic=SemanticEncoder(),
    )
    assert out is None


@pytest.mark.asyncio
async def test_pipeline_catalyst_failure_does_not_break_flow(monkeypatch):
    p = QuestionPipeline()

    async def fail(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(p.llm, "structured", fail)
    monkeypatch.setattr(p.catalyst, "analyze", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    qs = [
        q("q1", "Why is onboarding taking so long?"),
        q("q2", "Why has activation dropped for new users?"),
        q("q3", "What is the hiring budget?"),
    ]
    result = await p.run(meeting_title="Product", domain="product", agenda="growth", questions=qs)
    assert result.categories
    assert "creative_catalyst" not in result.meta


@pytest.mark.asyncio
async def test_pipeline_hands_catalyst_context_to_existing_nominee_generator(monkeypatch):
    p = QuestionPipeline()
    calls = []

    async def structured(system, user, schema):
        calls.append(user)
        if schema.__name__ == "LLMCategory":
            return schema.model_validate({
                "groups": [[0], [1]],
                "labels": {"0": "onboarding", "1": "activation"},
                "intents": {"0": "onboarding new users", "1": "activation new users"},
            })
        return schema.model_validate({"nominees": ["Could onboarding friction be connected to activation?"]})

    monkeypatch.setattr(p.llm, "structured", structured)
    qs = [q("q1", "Why is onboarding taking so long?"), q("q2", "Why has activation dropped for new users?")]
    result = await p.run(meeting_title="Product", domain="product", agenda="growth", questions=qs)

    assert result.categories
    assert "creative_catalyst" in result.meta
    assert any("Optional Creative Catalyst insight" in call for call in calls)


def test_catalyst_three_cluster_chain_is_still_one_handoff():
    from app.catalyst import CatalystContext, CatalystGroup, CreativeCatalystEngine
    ctx = CatalystContext(
        meeting_title="Growth",
        domain="product",
        agenda="activation",
        groups=(
            CatalystGroup(0, "onboarding friction", "onboarding", ("q1",), ("Why do new users struggle?",)),
            CatalystGroup(1, "feature adoption decline", "adoption", ("q2",), ("Why are existing features underused?",)),
            CatalystGroup(2, "retention decline", "retention", ("q3",), ("Why are returning users declining?",)),
        ),
    )
    out = CreativeCatalystEngine().analyze(ctx)
    assert out is not None
    assert len(out.source_group_indexes) in {2, 3}
    assert out.handoff_payload.startswith("CREATIVE_CATALYST_HANDOFF")
    assert "authority=existing_nominee_generator" in out.handoff_payload


def test_catalyst_has_no_network_or_meetlens_ranking_dependency():
    import inspect
    from app.catalyst.engine import CreativeCatalystEngine
    source = inspect.getsource(CreativeCatalystEngine)
    assert "httpx" not in source
    assert "category_priority" not in source
    assert "PriorityAgent" not in source


@pytest.mark.parametrize("count", [2, 4, 8])
def test_catalyst_output_is_bounded(count):
    from app.catalyst import CatalystContext, CatalystGroup, CreativeCatalystEngine
    groups = tuple(
        CatalystGroup(i, f"topic {i} adoption", f"g{i}", (f"q{i}",), (f"Question about topic {i}",))
        for i in range(count)
    )
    out = CreativeCatalystEngine().analyze(CatalystContext("T", "D", "A", groups))
    assert out is None or len(out.source_group_indexes) <= 3
