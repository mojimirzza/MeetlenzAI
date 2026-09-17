from __future__ import annotations
import re
from collections import Counter
from dataclasses import dataclass
from uuid import uuid4
from hashlib import sha256
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.core.models import PipelineResult, QuestionCategory, Nominee
from app.services.llm import LLMClient
from app.services.ranking import category_priority, diminishing_ratio
from app.services.semantic import SemanticEncoder, keyword_overlap, hybrid_match, concept_hints, primary_concept
from app.services.creative_catalyst import CatalystInsight, CreativeCatalyst
from prompts.registry import PROMPT_VERSION


class LLMCategory(BaseModel):
    groups: list[list[int]] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    intents: dict[str, str] = Field(default_factory=dict)


class LLMNominee(BaseModel):
    nominees: list[str]


@dataclass
class IntakeQuestion:
    id: str
    user_id: str
    text: str
    likes: int
    created_at: object
    expertise: list[str]


class QuestionPipeline:
    def __init__(self, *, llm=None, semantic=None, catalyst=None) -> None:
        self.s = get_settings()
        self.llm = llm or LLMClient()
        self.semantic = semantic or SemanticEncoder()
        self.catalyst = catalyst or CreativeCatalyst()

    @staticmethod
    def normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text.strip())
        return text

    def fallback_groups(self, questions: list[IntakeQuestion]) -> list[list[int]]:
        if not questions:
            return []
        texts = [self.normalize(q.text) for q in questions]
        anchors = [primary_concept(t) for t in texts]
        groups_by_anchor: dict[str, list[int]] = {}
        unresolved: list[int] = []
        for i, anchor in enumerate(anchors):
            if anchor:
                groups_by_anchor.setdefault(anchor, []).append(i)
            else:
                unresolved.append(i)

        groups: list[list[int]] = list(groups_by_anchor.values())
        if not unresolved:
            return sorted(groups, key=lambda g: min(g))

        unresolved_texts = [texts[i] for i in unresolved]
        sim = self.semantic.similarity_matrix(unresolved_texts)
        threshold = self.s.question_similarity_threshold
        used: set[int] = set()
        for local_i, global_i in enumerate(unresolved):
            if local_i in used:
                continue
            group = [global_i]
            for local_j in range(local_i + 1, len(unresolved)):
                if local_j in used:
                    continue
                score = hybrid_match(unresolved_texts[local_i], unresolved_texts[local_j], float(sim[local_i, local_j]))
                if score >= threshold:
                    group.append(unresolved[local_j])
                    used.add(local_j)
            used.add(local_i)
            groups.append(group)
        return sorted(groups, key=lambda g: min(g))

    def fallback_nominees(self, group: list[IntakeQuestion]) -> list[Nominee]:
        ordered = sorted(group, key=lambda q: (q.likes, len(q.text)), reverse=True)
        nominees: list[Nominee] = []
        for q in ordered[:2]:
            nominees.append(Nominee(
                nominee_id=str(uuid4()), text=q.text, source_question_ids=[x.id for x in group],
                semantic_distinctiveness=1.0, quality_score=0.55 + min(0.4, q.likes * 0.05),
                evaluation={"source_fidelity": 1.0, "clarity": 0.6, "answerability": 0.7, "neutrality": 1.0},
                rationale="Representative candidate selected by deterministic fallback quality policy."
            ))
        if not nominees:
            nominees.append(Nominee(nominee_id=str(uuid4()), text=group[0].text,
                                    source_question_ids=[q.id for q in group], quality_score=0.5))
        return nominees

    @staticmethod
    def heuristic_relevance(text: str, title: str, agenda: str, domain: str) -> float:
        context = f"{title} {agenda} {domain}".lower()
        return min(1.0, 0.5 + 0.25 * keyword_overlap(text, context))

    def evaluate_nominees(self, nominees: list[Nominee]) -> list[Nominee]:
        if not nominees:
            return nominees
        texts = [self.normalize(n.text) for n in nominees]
        matrix = self.semantic.similarity_matrix(texts) if len(texts) > 1 else None
        for i, n in enumerate(nominees):
            redundancy = max((float(matrix[i, j]) for j in range(len(nominees)) if j != i), default=0.0) if matrix is not None else 0.0
            distinct = 1.0 - redundancy
            n.semantic_distinctiveness = max(0.0, min(1.0, distinct))
            n.evaluation["distinctiveness"] = n.semantic_distinctiveness
            n.quality_score = max(0.0, min(1.0,
                0.30 * n.evaluation.get("source_fidelity", 0.8) +
                0.20 * n.evaluation.get("clarity", 0.7) +
                0.20 * n.evaluation.get("answerability", 0.7) +
                0.10 * n.evaluation.get("neutrality", 0.9) +
                0.20 * n.semantic_distinctiveness))
        return nominees

    async def run(self, *, meeting_title: str, domain: str, agenda: str,
                  questions: list[IntakeQuestion], meeting_id: str | None = None) -> PipelineResult:
        if not questions:
            return PipelineResult(categories=[], prompt_version=PROMPT_VERSION,
                                  model_name=self.s.llm_model, fallback=True)

        fallback = False
        try:
            numbered = "\n".join(f"[{i}] {q.text}" for i, q in enumerate(questions))
            system = open_prompt("cluster")
            user = open_prompt("cluster_input").format(title=meeting_title, domain=domain, agenda=agenda, questions=numbered)
            out = await self.llm.structured(system, user, LLMCategory)
            groups = []
            covered = set()
            for g in out.groups:
                clean = [i for i in g if 0 <= i < len(questions) and i not in covered]
                if clean:
                    groups.append(clean); covered.update(clean)
            groups.extend([[i] for i in range(len(questions)) if i not in covered])
            if not groups:
                raise ValueError("LLM returned no usable groups")
        except Exception:
            groups = self.fallback_groups(questions)
            fallback = True

        max_q = max(len(g) for g in groups)
        max_participants = max(len({questions[i].user_id for i in g}) for g in groups)
        max_likes = max(sum(questions[i].likes for i in g) for g in groups)
        categories = []
        llm_labels = getattr(out, "labels", {}) if not fallback else {}
        llm_intents = getattr(out, "intents", {}) if not fallback else {}
        intents_by_group: dict[int, str] = {}
        labels_by_group: dict[int, str] = {}
        prepared_groups: list[list[IntakeQuestion]] = []
        for idx, group_ids in enumerate(groups):
            group = [questions[i] for i in group_ids]
            prepared_groups.append(group)
            raw_intent = str(llm_intents.get(str(idx), llm_intents.get(idx, ""))).strip() if isinstance(llm_intents, dict) else ""
            intents_by_group[idx] = raw_intent or self._fallback_intent(group, meeting_title)
            raw_label = str(llm_labels.get(str(idx), llm_labels.get(idx, ""))).strip() if isinstance(llm_labels, dict) else ""
            labels_by_group[idx] = raw_label or self._label_from_intent(intents_by_group[idx])

        catalyst: CatalystInsight | None = None
        try:
            catalyst = self.catalyst.analyze(
                groups=prepared_groups,
                group_intents=intents_by_group,
                group_labels=labels_by_group,
                meeting_title=meeting_title,
                domain=domain,
                agenda=agenda,
            )
        except Exception:
            catalyst = None

        catalyst_by_group: dict[int, CatalystInsight] = {}
        if catalyst:
            for group_index in catalyst.source_group_indexes:
                catalyst_by_group[group_index] = catalyst

        for idx, group_ids in enumerate(groups):
            group = prepared_groups[idx]
            group = [questions[i] for i in group_ids]
            source_ids = [q.id for q in group]
            intent = intents_by_group[idx]
            label = labels_by_group[idx]
            stable_key = self._stable_intent_key(meeting_id or "local", meeting_title, intent)
            cid = "cat-" + sha256(stable_key.encode()).hexdigest()[:12]
            nominees = self.fallback_nominees(group)
            if not fallback:
                try:
                    source = "\n".join(f"- {q.text}" for q in group)
                    catalyst_context = ""
                    insight = catalyst_by_group.get(idx)
                    if insight:
                        catalyst_context = (
                            "\nOptional Creative Catalyst insight (not authoritative; do not copy blindly):\n"
                            f"- {insight.insight}\n"
                            f"- Candidate angle: {insight.candidate_angle}\n"
                            f"- Confidence: {insight.confidence:.2f}\n"                            f"- Evidence: {'; '.join(insight.evidence)}\n"
                            "Use this only to enrich the nominee if it remains grounded in the source questions.\n"
                        )
                    no = await self.llm.structured(
                        open_prompt("nominate"),
                        f"Meeting title: {meeting_title}\nDomain: {domain}\nAgenda: {agenda}\nIntent: {intent}\nQuestions:\n{source}{catalyst_context}",
                        LLMNominee,
                    )
                    texts = [self.normalize(x) for x in no.nominees if self.normalize(x)]
                    if texts:
                        nominees = [Nominee(nominee_id="nom-" + sha256((cid + "|" + t).encode()).hexdigest()[:12], text=t, source_question_ids=source_ids,
                                            rationale="LLM nominee; source-grounded and moderator approval required.") for t in texts[:self.s.max_candidates_per_cluster]]
                except Exception:
                    nominees = self.fallback_nominees(group)
            for n in nominees:
                n.nominee_id = "nom-" + sha256((cid + "|" + n.text).encode()).hexdigest()[:12]
            nominees = self.evaluate_nominees(nominees)
            participant_count = len({q.user_id for q in group})
            likes = sum(q.likes for q in group)
            relevance = max(self.heuristic_relevance(q.text, meeting_title, agenda, domain) for q in group)
            expertise_fit = min(1.0, sum(bool(q.expertise) for q in group) / max(1, len(group)))
            newest_at = max(q.created_at for q in group)
            score, parts = category_priority(
                relevance=relevance, question_count=len(group), participant_count=participant_count,
                likes=likes, expertise_fit=expertise_fit, novelty=sum(n.semantic_distinctiveness for n in nominees) / max(1, len(nominees)),
                newest_at=newest_at, max_question_count=max_q, max_participant_count=max_participants,
                max_likes=max_likes,
            )
            categories.append(QuestionCategory(category_id=cid, label=label, intent=intent,
                                                source_question_ids=source_ids, nominees=nominees,
                                                priority_score=score, priority_explanation=parts))
        categories.sort(key=lambda c: c.priority_score, reverse=True)
        meta = {"question_count": len(questions), "category_count": len(categories)}
        if catalyst:
            meta["creative_catalyst"] = {
                "kind": catalyst.kind,
                "source_group_indexes": list(catalyst.source_group_indexes),
                "source_question_ids": list(catalyst.source_question_ids),
                "insight": catalyst.insight,
                "candidate_angle": catalyst.candidate_angle,
                "confidence": catalyst.confidence,
                "novelty": catalyst.novelty,
            }
        return PipelineResult(categories=categories, prompt_version=PROMPT_VERSION,
                              model_name=self.s.llm_model, fallback=fallback, meta=meta)

    @staticmethod
    def _fallback_intent(group: list[IntakeQuestion], meeting_title: str = "") -> str:
        text = max((q.text for q in group), key=len)
        cleaned = re.sub(r"[?؟!]+$", "", text).strip()
        hints = concept_hints(" ".join(q.text for q in group))
        concept_labels = {
            "launch": "production launch timing", "rollback": "migration rollback and recovery",
            "compliance": "migration compliance and audit controls", "observability": "production observability and degradation detection",
            "performance": "service performance and latency targets", "resilience": "service resilience and failover recovery",
            "capacity": "system capacity and traffic limits", "customer_impact": "customer impact during rollout",
        }
        if hints:
            key = sorted(hints)[0]
            return concept_labels.get(key, cleaned[:180])
        return cleaned[:180] if len(group) == 1 else f"Shared information need: {cleaned[:120]}"

    @staticmethod
    def _label_from_intent(intent: str) -> str:
        words = intent.split()
        if len(words) <= 6:
            return intent
        return " ".join(words[:6]).rstrip(".,:;")

    @staticmethod
    def _stable_intent_key(meeting_id: str, meeting_title: str, intent: str) -> str:
        norm = re.sub(r"\W+", " ", intent.lower(), flags=re.UNICODE).strip()
        return f"{meeting_id}|{meeting_title.lower()}|{norm}"


def open_prompt(name: str) -> str:
    from pathlib import Path
    return (Path(__file__).resolve().parents[4] / "prompts" / f"{name}.txt").read_text(encoding="utf-8")
