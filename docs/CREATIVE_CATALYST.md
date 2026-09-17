# MeetLens Creative Catalyst — Question Behind the Questions

## Purpose

Creative Catalyst is a small, self-contained mid-pipeline intelligence module. It observes already-formed semantic groups and, at most, produces one source-grounded cross-group insight. It then hands that insight to the existing nominee-generation stage and owns no downstream decision.

```text
semantic groups + intents
        ↓
Creative Catalyst
        ↓  optional insight
existing nominee generator
        ↓
existing evaluation / ranking
        ↓
existing moderator
```

## Why this insertion point

The Catalyst runs after grouping/intent formation and before nominee generation. This gives it a complete view of the current question landscape without moving any business authority out of the existing pipeline.

## Non-goals

- no new database
- no new framework or queue
- no ranking changes
- no moderator bypass
- no new LLM/provider abstraction
- no required external service

## Failure behavior

Catalyst failure is isolated. A malformed result, exception, or unavailable LLM must not prevent the normal MeetLens pipeline from producing nominees. The current implementation is deterministic and does not require a live LLM call.

## Output

A successful insight contains:

- insight kind
- source group indexes
- source question IDs
- grounded insight text
- candidate angle
- confidence
- novelty

Only one insight is emitted per processing cycle. Silence is preferred to weak or duplicate creativity.

## Current implementation

- Module: `app/services/creative_catalyst.py`
- Integration: `app/services/pipeline.py`
- Tests: `tests/test_creative_catalyst.py`

## Disablement

The module can be bypassed at the pipeline integration point without changing the downstream nominee, ranking, moderation, persistence, or evidence contracts.
