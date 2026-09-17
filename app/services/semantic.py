from __future__ import annotations
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticEncoder:
    """Local semantic encoder with optional sentence-transformers and deterministic fallback."""
    def __init__(self) -> None:
        self._model = None
        self._tfidf: TfidfVectorizer | None = None

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            except Exception:
                self._model = False
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        texts = [self.normalize(t) for t in texts]
        model = self._load_model()
        if model is not False and model is not None:
            return np.asarray(model.encode(texts, normalize_embeddings=True), dtype=float)
        # Fit one vectorizer per batch only. This is deterministic and avoids cross-request vocabulary leakage.
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, max_features=8000)
        return vectorizer.fit_transform(texts).toarray().astype(float)

    def similarity_matrix(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0))
        return cosine_similarity(self.encode(texts))

    def pairwise(self, a: str, b: str) -> float:
        return float(self.similarity_matrix([a, b])[0, 1])


# Conservative, non-overlapping fallback concepts. These are intentionally narrower than the previous alias sets.
_CONCEPT_ALIASES = {
    "launch": {"launch", "go live", "go-live", "release", "launch date", "customer release", "release target", "go-live window", "committing to for production", "عرضه", "لانچ", "رونمایی", "انتشار"},
    "rollback": {"rollback", "revert", "restore previous", "recovery path", "rollback plan", "restore the previous database", "roll back", "rollback mechanism", "بازگشت", "برگردان"},
    "compliance": {"audit", "compliance", "regulatory", "control", "controls", "requirement", "ممیزی", "انطباق", "الزام"},
    "observability": {"observability", "monitoring", "degradation", "degrading", "metrics", "signals", "unhealthy", "incident", "detect production", "مانیتورینگ", "رخداد", "افت", "مشاهده پذیری"},
    "performance": {"latency", "response time", "performance", "speed", "زمان پاسخ", "تاخیر", "سرعت"},
    "resilience": {"resilience", "failover", "regional failure", "recovery objective", "recover from", "بازیابی", "سوییچ"},
    "capacity": {"capacity", "traffic", "throughput", "load", "ظرفیت", "ترافیک"},
    "customer_impact": {"customer impact", "users affected", "customer disruption", "customer effect", "اثر مشتری", "تأثیر مشتری"},
}


def _tokens(text: str) -> set[str]:
    stop = {
        "و", "یا", "که", "از", "به", "را", "در", "با", "برای", "چه", "کی", "است", "هست", "می", "شود",
        "will", "when", "what", "is", "the", "a", "an", "of", "to", "and", "do", "we", "are", "how", "does", "can",
    }
    return {t for t in re.findall(r"[\w\u0600-\u06ff]+", text.lower()) if t not in stop and len(t) > 1}


def concept_hints(text: str) -> set[str]:
    low = text.lower()
    found = set()
    for concept, aliases in _CONCEPT_ALIASES.items():
        if any(alias in low for alias in aliases):
            found.add(concept)
    return found


def primary_concept(text: str) -> str | None:
    """Choose one strongest concept for deterministic grouping in offline mode."""
    low = text.lower()
    candidates: list[tuple[int, int, str]] = []
    for concept, aliases in _CONCEPT_ALIASES.items():
        hits = [alias for alias in aliases if alias in low]
        if hits:
            # More hits and longer matched phrases indicate a stronger semantic anchor.
            candidates.append((len(hits), max(len(x) for x in hits), concept))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def concept_overlap(a: str, b: str) -> float:
    ca, cb = concept_hints(a), concept_hints(b)
    if not ca or not cb:
        return 0.0
    return len(ca & cb) / len(ca | cb)


def keyword_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    common = len(ta & tb)
    lexical = common / max(1, min(len(ta), len(tb)))
    concept = concept_overlap(a, b)
    return max(lexical, concept)


def hybrid_match(a: str, b: str, tfidf_similarity: float = 0.0) -> float:
    """Conservative fallback score. Strongly conflicting concepts block false merges."""
    hints_a, hints_b = concept_hints(a), concept_hints(b)
    if hints_a and hints_b and not (hints_a & hints_b):
        return 0.0
    lexical = keyword_overlap(a, b)
    concepts = concept_overlap(a, b)
    if concepts >= 0.75:
        return 0.92
    if lexical >= 0.50 and tfidf_similarity >= 0.30:
        return 0.60 + 0.25 * lexical + 0.15 * tfidf_similarity
    return 0.65 * tfidf_similarity + 0.35 * lexical
