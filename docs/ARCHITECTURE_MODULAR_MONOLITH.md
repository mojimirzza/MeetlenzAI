# MeetLens Modular Monolith Architecture

## Decision

MeetLens remains one deployable application, but its code is organized by feature boundaries and explicit dependency seams.

We intentionally do **not** move to microservices yet.

## Boundaries

```text
app/
  features/
    meeting/
      application/      # meeting use-cases / pipeline orchestration
  catalyst/             # independent creative capability
  agents/               # policy-bounded supporting agents
  api/                  # transport adapters
  core/                 # shared contracts/config/privacy
  storage/              # persistence infrastructure
  platform/             # cross-cutting technical concerns (resilience, etc.)
  bootstrap/            # composition root / dependency wiring
  kernel/               # tiny stable ports/protocols
```

## Dependency direction

```text
API/UI → feature application → ports
                         ↘ infrastructure adapters

bootstrap → constructs concrete implementations
platform  → provides technical primitives
core/kernel → contain no feature-specific orchestration
```

The public compatibility path `app.services.pipeline` remains temporarily stable while new code moves to `app.features.meeting.application.pipeline`.

## Why this shape

- One process and one deployment keeps MVP operations simple.
- Feature ownership reduces the growing service-layer coupling.
- Constructor injection makes testing and later provider replacement cheap.
- The resilience primitive gives optional external calls timeout/circuit-breaker protection without importing a framework.
- A future extraction into a service is possible only when a real scaling/ownership boundary appears.

## What we deliberately did not add

- microservices
- message broker
- service mesh
- DI framework
- repository-wide rewrite
- new database
- new API contract

## Exit criteria for future extraction

Only extract a module into a service when at least two of these become true:

1. independent scaling requirement;
2. independent deployment cadence;
3. independent reliability/SLO requirement;
4. separate ownership/team boundary;
5. meaningful network isolation/security boundary.
