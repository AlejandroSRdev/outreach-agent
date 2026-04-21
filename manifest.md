# OUTREACH AGENT — SYSTEM MANIFEST

## 1. Purpose

Outbound automation system designed to generate controlled, personalized outreach messages using AI.

The system is not a content generator.  
It is a backend system that orchestrates AI as a non-deterministic dependency under strict control.

Goal:
- Produce consistent, valid, and traceable outputs
- Maintain system observability and reliability
- Persist execution state for analysis and control


## 2. System Boundaries

### Included
- Lead input processing (structured)
- AI pipeline orchestration (multi-step)
- Output validation and control
- Persistence of executions and results
- Structured logging and metrics
- API exposure via HTTP

### Excluded
- Frontend UI (minimal or none)
- Real CRM integrations (simulated or simplified)
- Complex authentication / multi-tenant systems
- Distributed systems (queues, workers, etc.)
- Advanced cloud infrastructure


## 3. Input / Output Contract

### Input (Lead)
Structured JSON:
- lead_id

### Output (Generated Message)
Structured JSON:
- subject
- body
- personalization_points
- risk_flags
- metadata (optional: tokens, latency, etc.)

Output is never accepted as free text.
It must conform to a strict schema before persistence.


## 4. Core Architecture

Hexagonal architecture (lightweight, non-ceremonial)

### Layers

#### Domain
- Entities: Lead, OutreachRun, Message
- Value Objects: MessageContent, ExecutionStatus
- Business rules and invariants
- Domain errors
- Ports (interfaces)

#### Application
- Use cases (orchestrators)
- Pipeline coordination
- Retry policies
- Validation flow
- DTOs

#### Infrastructure
- FastAPI controllers (HTTP)
- LLM adapters
- PostgreSQL persistence
- Logging & telemetry
- Configuration


## 5. AI Pipeline

Sequential multi-step pipeline:

1. Research (context enrichment: deterministic -> database)
2. Generation (initial draft)
3. Refinement (clarity, tone, constraints)

### Rules
- Each step is isolated
- Each output is validated
- Failures stop the pipeline
- No step mutates previous state silently


## 6. Validation Strategy

- Input validation at API boundary (Pydantic)
- Internal validation between pipeline steps
- Final schema validation before persistence

Invalid outputs are rejected, not corrected silently.


## 7. Failure Model

Explicit failure points:
- Input validation failure
- LLM failure (timeout, invalid output)
- Schema validation failure
- Persistence failure

System behavior:
- Fail fast
- Do not persist invalid states
- Log all failures with context


## 8. Retry Strategy

Retries apply ONLY to:
- Transient LLM failures

Retries do NOT apply to:
- Validation errors
- Schema violations
- Business rule failures


## 9. Persistence Model (PostgreSQL)

Core entities:

- leads
- outreach_runs
- pipeline_stage_results
- generated_messages

Goals:
- Traceability of each execution
- Stage-level visibility
- Reproducibility analysis


## 10. Observability

### Logging
- Structured logs (JSON)
- Correlation via run_id / request_id
- Stage-level logging

### Metrics
- Execution latency
- Stage duration
- Failure rate
- LLM usage (optional)

### External visibility
- Logs streamed externally (e.g., Better Stack or Grafana)
- Metrics exposed for monitoring


## 11. Deployment

Initial:
- Fly.io (containerized service, Dockerfile)

Future (optional):
- AWS (App Runner or equivalent)

Focus:
- Reliable execution over infrastructure complexity


## 12. Non-Goals

- High scalability systems
- Distributed processing
- Complex orchestration frameworks
- Full production SaaS readiness

This system is designed to demonstrate:
- backend architecture clarity
- AI control and integration
- system reliability and observability


## 13. Design Principles

- AI is an external, untrusted dependency
- The backend owns all decisions
- Every boundary validates
- Invalid states are never persisted
- Simplicity over premature abstraction
- Observability is mandatory, not optional


## 14. Success Criteria

The system is considered complete when:

- One full pipeline executes end-to-end
- Output is schema-valid and persisted
- Execution is observable (logs + metrics)
- Failures are explicit and traceable
- The system can be explained clearly without code