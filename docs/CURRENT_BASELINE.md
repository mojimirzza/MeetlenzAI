# MeetLens Current Baseline — 2026-09-09

## Verified locally

- Pytest: 15 passed after the latest semantic/fallback and coverage changes.
- Python compileall: passed after the latest changes.
- FastAPI application imports and starts under Uvicorn.
- Main API path verified in runtime: meeting → participants → questions → like → process → related → moderation → outcome → evidence.
- Coverage / Blind Spot Radar endpoint is implemented.
- Deterministic Zero Pilot executes without cloud services.

## Current evidence level

**E2 — controlled/synthetic evidence.**

This repository does not claim external customer validation.

## Latest Zero Pilot

- 36 synthetic questions
- 8 ground-truth intents
- 8 participant archetypes
- MeetLens predicted 8 intents
- cluster pair F1: 1.0000 on this controlled fixture
- semantic compression rate: 0.7778
- top-5 unique intents: 5/5
- popularity-only baseline top-5 unique intents: 1/5
- baseline top-5 intent redundancy: 0.8000

## Material remaining gaps

- External pilot data.
- Large multilingual evaluation corpus.
- Production identity/SSO and tenant isolation.
- Production PostgreSQL/vector infrastructure.
- Browser-grade WebRTC/streaming audio.
- Formal legal/privacy review and independent security review.
