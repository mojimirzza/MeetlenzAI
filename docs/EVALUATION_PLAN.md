# Evaluation Plan

## Offline metrics
- cluster purity
- duplicate suppression
- intent consistency
- nominee source fidelity
- nominee distinctiveness
- priority fairness
- participant coverage
- moderator acceptance
- moderator edit rate
- latency

## Benchmark slices
- exact duplicates
- paraphrases
- unrelated questions
- Persian/English mixed questions
- popular low-value intents
- low-frequency high-value intents
- adversarial/prompt-injection text

## Decision rule
No product change is promoted because an LLM judge likes it. A change must improve a defined metric without violating policy, privacy, or lifecycle constraints.
