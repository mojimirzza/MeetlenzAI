# MeetLens — Master Endgame Execution Prompt

## Mission

Turn MeetLens from an MVP codebase into a technically credible, evidence-producing startup product.

The end state is **not** “AI meeting notes”. It is **collective question intelligence**:

> Given many human information needs and limited meeting time, identify a small, diverse, representative set of high-value questions, explain why they matter, and let a responsible human moderator decide what is actually asked.

The engineering objective is:

**idea → working product → measurable evidence → pilot-ready company asset**

## Non-negotiables

1. Python remains the application language.
2. LLMs are advisory; policy and authorization stay deterministic.
3. A moderator is the final gate before a question is asked.
4. Meeting content is untrusted data and must be isolated from system instructions.
5. Every AI output must be attributable to its source questions and prompt/model version.
6. No fake confidence values.
7. SQLite is for local MVP; storage interfaces must support PostgreSQL/vector infrastructure later.
8. Local-first audio/LLM/embedding execution must remain possible.
9. Every important product claim must be backed by a test, benchmark, event, or explicit roadmap item.
10. Never mark a feature DONE because a stub or interface exists.

## Required product loop

question intake
→ normalization
→ semantic representation
→ intent discovery
→ duplicate suppression
→ nominee generation
→ nominee evaluation
→ KPI priority
→ diversity-aware selection
→ moderator HITL
→ asked question
→ outcome
→ evaluation dataset
→ controlled offline improvement

## Required domain boundaries

Maintain explicit entities for:

- meeting
- participant
- question
- intent
- cluster
- nominee
- nominee evaluation
- priority decision
- moderator decision
- asked question
- outcome
- like event
- audit event
- model run
- prompt version

Never collapse these into one generic “question state”.

## Intelligence requirements

Use multilingual semantic embeddings as the primary similarity path, with deterministic lexical fallback.

Use incremental clustering architecture rather than O(N²) full recomputation on every new question.

Ranking must incorporate:

- meeting relevance
- frequency with diminishing returns
- unique participant count
- likes
- expertise fit
- novelty
- recency
- information gain
- diversity penalty

Never let duplicate popularity automatically dominate importance.

Use diversity-aware selection such as MMR so limited moderator attention covers different information needs.

## Nominee requirements

Produce up to two genuinely distinct nominees per intent.

Each nominee must be scored on source fidelity, clarity, answerability, neutrality, distinctiveness and information value.

A nominee must never introduce an unsupported fact.

## HITL requirements

Only an authorized moderator may approve/edit/reject.

Illegal lifecycle transitions must fail.

Approval of one nominee must not mark every raw question in the category as ASKED.

The resulting asked question must be a separate object.

Outcomes must be separately recorded.

## Evidence requirements

Build a benchmark set containing English and Persian scenarios for:

- paraphrase clustering
- unrelated questions
- expert vs non-expert questions
- popularity hijacking
- duplicate suppression
- nominee diversity
- moderator acceptance
- prompt injection
- local fallback

Track at minimum:

- cluster purity
- duplicate suppression rate
- nominee acceptance rate
- moderator edit rate
- moderator rejection rate
- participant coverage
- time-to-moderation
- unanswered high-priority intents
- model latency
- fallback rate

Never report a metric without stating dataset size and evaluation conditions.

## Privacy/security requirements

Treat participant text, transcripts and audio as untrusted.

Implement:

- meeting-level authorization
- moderator role checking
- strict participant privacy defaults
- retention configuration
- deletion/purge
- audit events
- prompt injection tests
- input limits
- safe serialization

Do not call the product “GDPR compliant” merely because processing is local.

## Demo requirements

The demo must visibly perform this transformation:

**many voices → fewer intents → diverse nominees → human-approved questions → outcomes**

The UI must make the product thesis understandable within 30 seconds.

## Startup evidence requirements

The repository must contain:

- product narrative
- innovation thesis
- technical differentiation
- evidence plan
- pilot plan
- benchmark runner/results
- security/privacy boundary
- 12-month roadmap
- known limitations

The startup narrative must never promise immigration approval. It must demonstrate innovation, active founder contribution, credible technology, measurable value and a path to pilots.

## Execution protocol

1. Audit the entire repository.
2. Map every requirement to a file/test/evidence artifact.
3. Fix every Critical and High issue.
4. Implement missing product-critical behavior.
5. Write regression tests before declaring completion.
6. Run tests and repair all failures.
7. Run benchmarks and report conditions.
8. Run the demo end-to-end.
9. Verify privacy and moderator boundaries.
10. Produce a final status matrix: DONE / PARTIAL / DEFERRED.
11. Do not call anything DONE without executable evidence.
12. Package the final repository without generated databases, caches or secrets.

## Definition of done

MeetLens reaches the end state only when a new engineer can clone the repository, start the app, submit multiple multilingual questions, see semantic intent consolidation, compare diverse nominees, observe explainable priority, perform an authorized human moderation decision, obtain an explicit AskedQuestion, record an outcome, inspect the audit trail, and run the evaluation suite — without relying on an external paid service.

That is the product foundation.

The final goal is not more code.

The final goal is **evidence that the product thesis works**.
