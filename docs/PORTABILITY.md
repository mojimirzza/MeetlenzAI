# Portability & Reproducibility

## Canonical local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m app.main
```

The repository does not require a cloud LLM for the deterministic demo path. A local OpenAI-compatible LLM can be attached through environment variables.

## Verification
```bash
PYTHONPATH=. python scripts/verify_environment.py
```

Possible states:
- READY: tests/dependencies/model endpoint all available
- DEGRADED: core app works but optional/local LLM is unavailable
- BLOCKED: core dependencies or tests are failing

## Founder/mobile constraint
A mobile-only device is not a valid portability benchmark. Portability is evaluated on a standard Python environment and through the canonical verification command.
