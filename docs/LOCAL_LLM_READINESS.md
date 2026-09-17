# Local LLM Readiness

MeetLens uses an OpenAI-compatible HTTP abstraction. Domain logic is not tied to a specific model vendor.

## Expected runtime contract
- `POST /v1/chat/completions` for structured generation
- `GET /v1/models` for readiness probing

## Current state
- Provider abstraction: implemented
- Structured JSON validation: implemented
- Timeout: configured
- Fallback without LLM: implemented
- Model endpoint probe: implemented
- Actual DeepSeek inference in this repository run: not claimed unless a compatible local endpoint is available

## DeepSeek
The configured default model is `deepseek-ai/DeepSeek-V4-Flash`. Actual inference requires a compatible local serving environment and model availability on the host.

## Important distinction
A missing model endpoint is classified as `DEGRADED`, not as a product failure. Model quality remains an external benchmark that must be measured when the endpoint is available.
