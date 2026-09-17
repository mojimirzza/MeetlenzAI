# Production Path

## Pilot now
- FastAPI
- Gradio
- SQLite
- local OpenAI-compatible LLM or deterministic fallback
- local semantic encoder fallback
- append-only audit events

## Production next
1. PostgreSQL and pgvector/Qdrant
2. OIDC/SSO and tenant isolation
3. WebSocket/WebRTC audio path
4. distributed tracing/metrics
5. encrypted storage and secrets management
6. load/concurrency tests
7. retention/consent controls
8. deployment automation
9. security review

Production work should be evidence-driven by pilot usage rather than built speculatively.
