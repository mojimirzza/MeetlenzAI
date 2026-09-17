from __future__ import annotations

import re
from itertools import combinations

from .models import CatalystContext, CatalystGroup, CatalystInsight

_WORD_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)

_STOP = {
    "the","a","an","and","or","to","of","in","on","for","is","are","was","were","be","been","being",
    "what","why","how","when","where","who","which","can","could","would","should","will","do","does","did",
    "this","that","these","those","with","from","about","into","than","then","our","we","they","their","it","its",
    "چی","چیست","چرا","چگونه","چطور","چه","کدام","آیا","است","هست","هستند","شد","شود","می","از","به","در","با","برای","و","یا","که","این","آن","را","ما","آنها",
}
_CAUSE = {"cause","driver","because","friction","delay","blocker","problem","issue","constraint","failure","باعث","علت","دلیل","مانع","مشکل","گلوگاه","تاخیر","تأخیر","گیر"}
_OUTCOME = {"impact","result","activation","retention","adoption","churn","conversion","support","revenue","usage","drop","decline","growth","اثر","نتیجه","فعال","نگهداشت","ریزش","تبدیل","پشتیبانی","درآمد","استفاده","کاهش","رشد"}
_ACTION = {"build","add","feature","launch","invest","increase","expand","hire","ship","بساز","اضافه","ویژگی","راه‌اندازی","سرمایه","افزایش","گسترش","استخدام","عرضه"}
_USAGE = {"adopt","use","users","customer","onboarding","activation","retention","استفاده","کاربر","مشتری","ورود","فعال‌سازی","نگهداشت"}
_NEG = {"drop","decline","decrease","fall","low","down","lost","کاهش","افت","ریزش","کم","پایین","نشد","نمی"}


def tokens(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text or "") if len(w) > 1 and w.lower() not in _STOP}


def overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, min(len(a), len(b)))


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def topic_text(group: CatalystGroup) -> str:
    return " ".join([group.intent, group.label, *group.questions[:4]])


def concept_profile(text: str) -> dict[str, float]:
    t = tokens(text)
    scale = max(1, len(t))
    return {
        "cause": len(t & _CAUSE) / scale,
        "outcome": len(t & _OUTCOME) / scale,
        "action": len(t & _ACTION) / scale,
        "usage": len(t & _USAGE) / scale,
        "negative": len(t & _NEG) / scale,
    }


class CreativeCatalystEngine:
    """Independent, fast, removable discovery engine.

    It owns discovery, novelty gating, evidence traceability and handoff formatting.
    It knows nothing about MeetLens ranking, moderation, persistence or business policy.
    """

    MIN_GROUPS = 2
    MIN_CONFIDENCE = 0.60
    MIN_NOVELTY = 0.28
    MAX_GROUPS_FOR_SEARCH = 12

    def analyze(self, context: CatalystContext) -> CatalystInsight | None:
        groups = context.groups[: self.MAX_GROUPS_FOR_SEARCH]
        if len(groups) < self.MIN_GROUPS:
            return None

        candidates: list[tuple[float, float, str, tuple[int, ...], tuple[str, ...], str, str, tuple[str, ...]]] = []
        for left, right in combinations(groups, 2):
            candidates.extend(self._pair_candidates(left, right))
        if len(groups) >= 3:
            candidates.extend(self._triad_candidates(groups))
        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        confidence, novelty, kind, source_groups, source_questions, insight, angle, evidence = candidates[0]
        if confidence < self.MIN_CONFIDENCE or novelty < self.MIN_NOVELTY:
            return None

        source_text = " ".join(
            question
            for group in groups
            if group.index in source_groups
            for question in group.questions[:2]
        )
        if self._near_duplicate(angle, source_text):
            return None

        return CatalystInsight(
            kind=kind,
            source_group_indexes=source_groups,
            source_question_ids=source_questions,
            insight=insight,
            candidate_angle=angle,
            confidence=round(min(0.96, confidence), 2),
            novelty=round(min(0.96, novelty), 2),
            evidence=evidence,
            handoff_payload=self._handoff(kind, insight, angle, source_groups, evidence),
        )

    def _pair_candidates(self, left: CatalystGroup, right: CatalystGroup):
        left_text = topic_text(left)
        right_text = topic_text(right)
        lt = tokens(left_text)
        rt = tokens(right_text)
        lp = concept_profile(left_text)
        rp = concept_profile(right_text)
        semantic_bridge = overlap(lt, rt)
        distinctiveness = 1.0 - jaccard(lt, rt)
        shared_bonus = min(0.22, len(lt & rt) * 0.035)
        question_ids = tuple(dict.fromkeys((*left.question_ids, *right.question_ids)))
        evidence = (
            f"group {left.index}: {left.intent or left.label}",
            f"group {right.index}: {right.intent or right.label}",
        )

        causal = min(
            1.0,
            0.55 * lp["cause"] + 0.45 * rp["outcome"] +
            0.55 * rp["cause"] + 0.45 * lp["outcome"],
        )
        if causal > 0.06 and distinctiveness > 0.45:
            confidence = 0.54 + 0.30 * causal + shared_bonus
            novelty = 0.48 + 0.40 * distinctiveness
            a, b = self._topics(left, right)
            yield (
                confidence,
                novelty,
                "causal_bridge",
                (left.index, right.index),
                question_ids,
                f"The concerns around '{a}' and '{b}' may be two sides of the same underlying cause-and-effect problem.",
                f"Could the issue behind '{a}' be contributing to '{b}'?",
                evidence,
            )

        tension = min(1.0, lp["action"] + rp["usage"] + rp["negative"] + lp["negative"])
        if lp["action"] > 0.03 and (rp["usage"] > 0.03 or rp["negative"] > 0.02):
            confidence = 0.55 + 0.28 * tension + shared_bonus
            novelty = 0.56 + 0.30 * distinctiveness
            a, b = self._topics(left, right)
            yield (
                confidence,
                novelty,
                "productive_tension",
                (left.index, right.index),
                question_ids,
                "One cluster is pushing toward action while another points to an adoption or usage problem; the latter may be the deeper bottleneck.",
                f"Are we solving '{a}' when the more fundamental issue may be '{b}'?",
                evidence,
            )

        if 0.08 <= semantic_bridge <= 0.48 and distinctiveness > 0.52:
            confidence = 0.52 + 0.28 * (semantic_bridge + shared_bonus)
            novelty = 0.58 + 0.32 * distinctiveness
            a, b = self._topics(left, right)
            yield (
                confidence,
                novelty,
                "cross_cluster_connection",
                (left.index, right.index),
                question_ids,
                f"'{a}' and '{b}' share just enough context to suggest a hidden bridge without being duplicates.",
                f"What shared constraint could connect '{a}' with '{b}'?",
                evidence,
            )

    def _triad_candidates(self, groups: tuple[CatalystGroup, ...]):
        for combo in combinations(groups, 3):
            profiles = [concept_profile(topic_text(group)) for group in combo]
            cause_index = max(range(3), key=lambda i: profiles[i]["cause"] + profiles[i]["action"])
            outcome_index = max(range(3), key=lambda i: profiles[i]["outcome"] + profiles[i]["negative"])
            if cause_index == outcome_index:
                continue
            middle_index = next(i for i in range(3) if i not in {cause_index, outcome_index})
            strength = (
                profiles[cause_index]["cause"] + profiles[cause_index]["action"] +
                profiles[middle_index]["usage"] + profiles[middle_index]["negative"] +
                profiles[outcome_index]["outcome"] + profiles[outcome_index]["negative"]
            )
            distinctiveness = 1.0 - jaccard(
                tokens(topic_text(combo[cause_index])),
                tokens(topic_text(combo[outcome_index])),
            )
            if strength < 0.12 or distinctiveness < 0.60:
                continue
            cause = self._topic(combo[cause_index])
            middle = self._topic(combo[middle_index])
            outcome = self._topic(combo[outcome_index])
            evidence = tuple(f"group {group.index}: {group.intent or group.label}" for group in combo)
            question_ids = tuple(dict.fromkeys(qid for group in combo for qid in group.question_ids))
            yield (
                min(0.94, 0.58 + 0.26 * min(1.0, strength * 3.2)),
                min(0.95, 0.62 + 0.28 * distinctiveness),
                "three_cluster_chain",
                tuple(group.index for group in combo),
                question_ids,
                f"Three clusters may form a hidden chain: '{cause}' → '{middle}' → '{outcome}'.",
                f"Could '{cause}' be influencing '{outcome}' through the problem surfaced in '{middle}'?",
                evidence,
            )

    def _topics(self, left: CatalystGroup, right: CatalystGroup) -> tuple[str, str]:
        return self._topic(left), self._topic(right)

    def _topic(self, group: CatalystGroup) -> str:
        source = (group.intent or group.label or (group.questions[0] if group.questions else "")).strip()
        words = [word for word in _WORD_RE.findall(source) if word.lower() not in _STOP]
        return " ".join(words[-7:])[:100] or "this concern"

    @staticmethod
    def _near_duplicate(angle: str, source: str) -> bool:
        return jaccard(tokens(angle), tokens(source)) > 0.72

    @staticmethod
    def _handoff(kind: str, insight: str, angle: str, source_groups: tuple[int, ...], evidence: tuple[str, ...]) -> str:
        return (
            "CREATIVE_CATALYST_HANDOFF\n"
            f"kind={kind}\n"
            f"groups={','.join(map(str, source_groups))}\n"
            f"insight={insight}\n"
            f"candidate_angle={angle}\n"
            f"evidence={' | '.join(evidence)}\n"
            "authority=existing_nominee_generator"
        )
