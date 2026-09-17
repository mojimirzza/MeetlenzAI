from datetime import datetime, timezone
from app.services.ranking import question_score


def test_question_score_is_bounded_and_explainable():
    score, parts = question_score(
        relevance=0.9, frequency=10, likes=8, expertise_fit=0.7,
        novelty=0.8, created_at=datetime.now(timezone.utc), max_frequency=10, max_likes=8,
    )
    assert 0 <= score <= 1
    assert set(parts) == {"meeting_relevance", "frequency", "likes", "expertise_fit", "novelty", "recency"}
