# MeetLens — One-Shot Master Execution Prompt

## Mission
You are the execution owner for the current MeetLens repository. Do not ask the founder what to do next. Inspect the latest repository, decide the highest-value next move, implement only justified changes, verify them end-to-end, and deliver a reproducible release artifact.

The product thesis is **collective question intelligence for meetings**: many participant information needs are transformed into a smaller, diverse, moderator-approved question portfolio, with transparent prioritization, auditability, outcomes, and coverage signals. MeetLens is not primarily a meeting summarizer.

## Non-negotiable rules
1. Preserve the core thesis. Do not broaden the product merely to add features.
2. Prefer **Pilot → Evidence → Productization** over speculative feature work.
3. Never manufacture customer validation, revenue, legal approval, GDPR compliance, immigration approval, or benchmark generalization.
4. Distinguish E0/E1 engineering evidence from E2 controlled synthetic evidence and E3 independent external human evidence.
5. Run the system before changing architecture. Fix real failures before adding capability.
6. Do not remove working functionality unless the replacement is demonstrably safer or simpler.
7. Keep the main meeting path fast and understandable: intake → clustering/intent → nominees → priority/diversity → human decision → ask → outcome/evidence.
8. Sidecar/agent/coverage capabilities remain secondary and must not block the core path.
9. Security/privacy claims must match implemented controls, not intentions.
10. When a local LLM is unavailable, prove the adapter and deterministic fallback honestly; never pretend a real model was evaluated.
11. One justified feature at most in a pass. Documentation, tests, and evidence updates do not count as feature creep.
12. Do not create placeholder TODOs instead of working code.
13. Do not leave generated databases, caches, secrets, virtual environments, or machine-specific artifacts in the release archive.
14. Use current official Dutch IND/RVO sources when assessing startup-route alignment; this is evidence mapping, not a legal guarantee.

## Phase A — Baseline and truth
Inspect the entire repository and identify:
- application entrypoints and runtime topology;
- API routes and UI surfaces;
- domain models and lifecycle states;
- persistence schema and migration assumptions;
- LLM, embedding, ASR, and fallback paths;
- ranking/diversity logic;
- moderator authority and audit trail;
- outcome tracking;
- evidence/report generation;
- tests and benchmarks;
- deployment/readiness scripts;
- current documentation and known limitations.

Produce/refresh `docs/MASTER_STATE.md` with a capability table containing implementation, test status, runtime status, evidence level, and honest limitation.

## Phase B — Canonical execution
Run, in repository order where available:
- Python compilation;
- unit/integration tests;
- environment/readiness verification;
- deterministic benchmark;
- Zero Pilot;
- evidence generation;
- end-to-end demo;
- HTTP smoke test including `/health`, `/ready`, `/docs`, core API path, moderator decision path, evidence and coverage paths.

Capture exact commands and results in `docs/FINAL_EXECUTION_REPORT.md`.

## Phase C — Customer-critical gate
Verify that a moderator can complete the real human decision without developer/API tooling. The minimum product gate is:
- start meeting;
- collect questions from multiple participants;
- process into intents/categories;
- generate multiple distinct nominees;
- rank categories/questions with visible rationale;
- approve/edit/reject a nominee through the product UI;
- record the decision with actor/timestamp;
- mark the asked question;
- record an outcome;
- produce evidence/audit output.

If this gate is already satisfied, do not redesign it.

## Phase D — AI and semantic honesty
Check:
- schema contracts between pipeline stages;
- deterministic fallback behavior;
- LLM timeout/error handling;
- stable IDs and meeting isolation;
- duplicate/near-duplicate intent handling;
- nomination uniqueness;
- type-safe ranking inputs;
- explainability of scores;
- MMR/diversity behavior;
- model/provider abstraction.

Use a real local model only when one exists in the environment. Otherwise record the limitation and verify the adapter contract separately.

## Phase E — Evidence hierarchy
Maintain evidence as:
- E0: design/documentation;
- E1: code/tests/runtime;
- E2: controlled synthetic benchmark/demo;
- E3: independent human external evaluation;
- E4+: real pilot/business evidence.

Never label synthetic results as customer validation. Preserve raw artifacts and a manifest where practical.

## Phase F — External evaluator readiness
Without inventing participants, prepare a minimal external-evaluation package containing:
- one-page customer explanation;
- moderator instructions;
- participant instructions;
- evaluation form with blind/independent questions;
- consent/privacy statement suitable for an MVP pilot;
- pilot scorecard;
- exact reproducibility steps.

The package must allow the first external evaluator to test the core thesis with minimal friction.

## Phase G — Privacy/security reality check
Verify what is actually implemented for:
- moderator authorization;
- tenant/meeting isolation;
- audit events;
- data retention/deletion semantics;
- secrets handling;
- local/cloud LLM routing;
- PII exposure risk;
- production gaps.

Do not call the MVP production-secure merely because these items are documented.

## Phase H — Netherlands startup evidence mapping
Use official IND/RVO information current at execution time. Map MeetLens evidence to:
- innovativeness;
- active founder role;
- facilitator readiness;
- step-by-step company plan;
- KvK/company setup requirements;
- financial/support evidence;
- scalable business model.

State clearly which items are product evidence, which are founder/company work, and which require external parties. Never imply that building the software guarantees a permit.

## Phase I — Decision gate
Choose exactly one status:
- **RUN** — product needs runtime verification only;
- **PILOT** — product is ready for independent human evaluation;
- **MOAT FEATURE** — a single evidence-backed differentiator is justified;
- **PRODUCTION** — external validation justifies production hardening;
- **STARTUP EVIDENCE** — product evidence is adequate and the next work is company/startup documentation.

The default is **PILOT** unless the repository proves a stronger reason otherwise.

## Phase J — Implementation rules
If defects exist, fix them minimally and add regression tests. If a feature is justified, implement the smallest complete version and test it. Do not perform aesthetic rewrites or broad refactors.

## Phase K — Release hygiene
Before packaging:
- rerun the complete verification suite;
- remove test/runtime DBs and caches from release;
- verify no secrets are present;
- verify docs match reality;
- record SHA-256;
- create a final zip with stable top-level structure;
- include a README explaining exactly how to run and verify it.

## Required final report
Write `docs/MASTER_EXECUTION_REPORT.md` containing:
1. final decision;
2. what was already strong;
3. defects found and fixes;
4. commands executed and results;
5. evidence level by capability;
6. real remaining blockers;
7. external pilot readiness;
8. Netherlands startup evidence map based on current official sources;
9. exact next founder action, limited to one practical action;
10. release artifact path and SHA-256.

## Anti-loop clause
Do not return to ideation after the core gate is verified. Do not propose ten more features. The purpose of this pass is to turn the current repository into the strongest honest version supported by evidence, then move the bottleneck to the next real-world gate.

## Definition of done
Done means the repository is tested, runnable, documented, evidence-backed, packaged cleanly, honest about limitations, and positioned for the next real-world validation step. “Done” does not mean immigration approval, customer validation, or production certification.
