# Production notes

1. Replace SQLite with PostgreSQL.
2. Add pgvector or Qdrant for dense+sparse retrieval. pgvector supports HNSW and PostgreSQL full-text hybrid search; Qdrant supports dense/sparse hybrid search and RRF/DBSF fusion.
3. Use WebRTC/browser audio for real-time capture; keep audio chunks local where possible.
4. Put authentication and per-meeting authorization in front of every endpoint.
5. Store moderator decisions as immutable audit events.
6. Add consent, retention, export, deletion, and data-residency controls before enterprise pilots.
7. Instrument: transcription WER, cluster purity, duplicate rate, nomination acceptance rate, moderator edits, time-to-question, and post-meeting usefulness.
8. Build an eval set of real questions by language/domain before changing prompts or models.
9. Never let the LLM directly execute irreversible actions; HITL remains mandatory.
10. Treat prompt injection in meeting transcripts as untrusted input.
