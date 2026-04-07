# Architecture

Hexagonal architecture — lightweight, non-ceremonial.

---

## Layers

### Domain
- Core business entities: `Lead`, `Company`, `Message`
- Operational entities: `OutreachRun`, `PipelineStageResult`
- Value objects: `MessageContent`, `ExecutionStatus`, `EnrichedContext`
- Business rules and invariants
- Domain errors
- Ports (interfaces to external systems)

### Application
- Use case: `execute_outreach` — single orchestrator for the full pipeline
- Pipeline coordination (research → generation → refinement)
- Retry policy enforcement
- Validation flow between stages
- DTOs for input/output transport

### Infrastructure
- **FastAPI** — HTTP controllers, request/response handling
- **LLM adapters** — AI provider integration (generation + refinement stages)
- **PostgreSQL** — persistence for all entities and execution traces
- **Logging** — structured JSON logs with `run_id` / `request_id` correlation
- **Configuration** — environment-based

---

## Responsibilities Per Layer

| Layer | Owns | Does NOT own |
|---|---|---|
| Domain | Business rules, entity validity | Persistence, HTTP, AI calls |
| Application | Orchestration, pipeline flow, retries | Transport format, DB queries |
| Infrastructure | I/O with external systems | Business logic |

---

## Key Principles

- AI is an external, untrusted dependency — governed by the application layer
- The backend owns all decisions — AI owns generation only
- Every boundary validates — invalid outputs are rejected, not corrected
- Invalid states are never persisted
