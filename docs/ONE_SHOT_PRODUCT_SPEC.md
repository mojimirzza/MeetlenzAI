# MeetLens — One-shot product definition

## Name

**MeetLens**

Working tagline: **Ask less. Surface better.**

Category: **Meeting Question Intelligence & Moderation Platform**

## Core problem

During important meetings, many people ask overlapping or low-signal questions. The moderator either chooses manually, ignores duplicates, or lets the loudest participant dominate. This wastes time and hides the collective information need.

## Product promise

MeetLens captures questions, infers their underlying intents, collapses duplicates, creates two high-quality representative nominees per intent, ranks intents with explainable KPIs, and gives a moderator a one-click human approval gate before a question is asked.

## Golden flow

1. Create a meeting.
2. Enter meeting title, agenda, domain, moderator and optional participant expertise.
3. Participants submit questions by text or local speech-to-text.
4. The pipeline normalizes and clusters by semantic intent.
5. Each cluster gets a canonical intent and two nominees.
6. The Priority Agent ranks the categories.
7. Moderator sees the top nominee pair and chooses: approve, edit, or reject.
8. Only approved/edited questions reach the ASKED state.
9. Participant clients can retrieve questions most related to their own submitted questions, subject to privacy policy.
10. All decisions can later feed an offline evaluation/training set.

## Why this is not just an AI meeting summarizer

- The atomic object is a **question**, not a transcript summary.
- The system optimizes **information diversity** and **coverage** rather than compression alone.
- It separates **model suggestions** from **human authority**.
- Ranking is explainable and policy controlled.
- The product can work local-first in sensitive environments.

## KPI model

Default score:

`0.30 meeting relevance + 0.22 frequency + 0.18 likes + 0.12 expertise fit + 0.10 novelty + 0.08 recency`

Recommended production KPIs:

- duplicate suppression rate
- category purity
- moderator acceptance rate
- moderator edit distance
- time from question intake to approval
- question coverage across participant groups
- unanswered high-priority intent count
- post-meeting usefulness rating

## Guardrails

- LLM cannot directly ask, publish, send, or execute an irreversible action.
- Moderator is the authority at the final gate.
- Meeting transcript/audio is untrusted input and may contain prompt injection.
- Participant identity should not be exposed by default.
- Data retention must be configurable per tenant and meeting.
- Every model output is traceable to source question IDs.

## Local-first architecture

- App runtime: Python + FastAPI + Gradio MVP.
- LLM: OpenAI-compatible local endpoint; DeepSeek-V4-Flash recommended where hardware allows.
- ASR: faster-whisper.
- Optional diarization: pyannote Community-1.
- MVP persistence: SQLite.
- Production persistence: PostgreSQL + pgvector or Qdrant.
- Agent orchestration: narrow typed state machine; LangGraph can be added for durable interrupt/resume when multi-step workflows grow.

## Monetization wedge

Phase 1: free/local developer edition.

Phase 2: enterprise pilot with local/on-prem deployment, SSO, audit, retention policies, multilingual meetings and domain packs.

Phase 3: regulated-industry platform with governance, analytics and meeting intelligence APIs.

## Initial market wedge

Start with high-stakes expert meetings where question quality is economically valuable:

- executive and board meetings
- public consultations / town halls
- product discovery and customer councils
- technical architecture reviews
- financial / regulated-industry meetings
- expert panels

## Netherlands startup narrative

The innovation story should not be “another meeting AI.” It should be:

**Privacy-preserving, real-time question intelligence that converts distributed human curiosity into a small, auditable and moderator-approved set of high-value questions.**

This creates a clear combination of innovative workflow, local AI deployment, multilingual European use cases and measurable productivity outcomes.

This is a product-positioning aid, not legal or immigration advice. Check the current IND/RVO requirements for your personal case.
