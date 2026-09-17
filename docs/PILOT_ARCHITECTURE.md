# MeetLens Pilot Architecture

## Selected strategy
Pilot -> Evidence -> Productization.

## Vertical
Technical architecture/design reviews, especially software and fintech teams.

## Live path
Question intake -> normalization -> semantic representation -> intent clustering -> nominee generation -> nominee evaluation -> priority -> diversity-aware ordering -> moderator HITL -> asked question -> outcome.

## Offline path
Audit events -> evidence export -> benchmark/evaluation -> experiment -> reviewed change -> deployment.

## Pilot constraints
SQLite, local deterministic fallback, optional local OpenAI-compatible LLM, FastAPI + Gradio. Production infrastructure is deliberately deferred.

## Evidence artifact
`GET /api/meetings/{meeting_id}/evidence` returns a reproducible meeting evidence report generated from stored questions, decisions, outcomes and audit events.
