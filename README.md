# Outreach Agent — AI-Powered Outreach Automation Backend

## Overview

Outreach Agent is a **production-oriented backend system** for AI-powered workflow automation, designed to generate personalized outbound emails at scale with measurable reliability.

The system processes leads from a **persistent PostgreSQL data layer** and executes a **multi-step pipeline** per lead — partially deterministic (data retrieval), partially non-deterministic (LLM inference) — with the architectural goal of keeping AI under strict system control at all times.

This project focuses on **system design, reliability, and observability**, not raw AI usage.

---

## Purpose

Most AI-based outreach tools fail due to:

* Uncontrolled outputs
* Lack of structure and validation
* Poor handling of concurrency and failures
* Over-reliance on a single model call
* Ephemeral, non-reproducible execution

Outreach Agent addresses this by:

> Treating AI as a non-deterministic external dependency that must be constrained, validated, and observed — while grounding the system in a deterministic data layer.

---

## System Design

### High-Level Flow

```
Batch Request → Orchestrator → Pipelines (per lead)
                                      ↓
                  [PostgreSQL] research → generation → refinement
                                      ↓
                               Structured Output
```

The pipeline operates on **persisted leads** retrieved from the database. This makes execution reproducible, auditable, and decoupled from ad-hoc input.

---

### Core Principles

* **Deterministic data layer, non-deterministic AI layer**
* **Separation of concerns (layered / hexagonal-inspired architecture)**
* **Failure isolation per lead**
* **Bounded concurrency**
* **Observable and measurable system behavior**

---

## Architecture

The system follows a **layered / hexagonal-inspired structure**:

* **Domain**

  * Core entities (`LeadInput`, `GeneratedEmail`)
  * No dependency on AI or infrastructure

* **Application**

  * Pipeline orchestration (`research → generation → refinement`)
  * Retry logic and validation boundaries

* **Infrastructure**

  * PostgreSQL client (Supabase)
  * LLM providers (OpenAI)
  * External integrations

---

## Data Layer

The system uses **PostgreSQL via Supabase** as its primary data store.

### Leads Table

Leads are persisted in the database and reused across pipeline executions. This replaces the previous model of static or ad-hoc input, enabling:

* **Reproducibility** — the same lead set can be reprocessed consistently
* **Real workflows** — the system operates on live datasets, not isolated test inputs
* **Non-ephemeral execution** — outputs and lead state survive across runs

### Generated Outputs

Pipeline outputs are associated with their corresponding leads, enabling downstream inspection, auditing, and iteration without re-running the full pipeline from scratch.

### Deterministic Backbone

The research stage no longer relies on LLM inference for lead data. It queries the database directly. This eliminates a major source of variance and grounds the pipeline in structured, controlled input before AI is ever invoked.

---

## Pipeline Design

Each lead goes through a **sequential pipeline**:

### 1. Research — Database-Backed

* Retrieves lead context from PostgreSQL (Supabase)
* **No LLM inference involved at this stage**
* Deterministic: same input → same output
* Grounds the pipeline before any AI is introduced

### 2. Generation — LLM-Driven

* Produces the initial email draft using enriched lead context
* Structured output enforced via validation before advancing

### 3. Refinement — LLM-Controlled

* Improves clarity, tone, and structure
* Enforces output constraints
* Final output must pass validation before being returned

---

## Concurrency Model

* **Batch-level concurrency** using `asyncio.gather`
* **Concurrency control** via `asyncio.Semaphore`
* Each lead is processed independently

This ensures:

* Parallel execution without resource exhaustion
* Predictable behavior under load
* Isolation of failures across leads

---

## Input Contract

```json
{
  "lead_ids": ["uuid", "..."]
}
```

Leads are resolved from the database by ID. The pipeline operates on structured, persisted records — not inline payload data.

---

## Output Contract

```json
{
  "lead": {...},
  "status": "success | failed",
  "result": {
    "subject": "...",
    "body": "..."
  }
}
```

* Each lead is processed and reported independently
* Failures are isolated and do not affect the rest of the batch

---

## Reliability Mechanisms

### Timeouts

* Each pipeline step is bounded (`asyncio.wait_for`)
* Prevents indefinite blocking on LLM or I/O calls

### Retry Strategy

* Retries applied selectively to LLM-related failures
* Uses context-aware correction hints on retry to improve output quality

### Validation

* Structured output is enforced at every AI step before advancing
* Invalid outputs are rejected and trigger retries or failure isolation

---

## Observability

The system is designed to be **measurable and inspectable** at every stage of execution.

### Structured Logging

Pipeline events are emitted as structured log entries:

* `batch_start`
* `pipeline_start`
* `generation_complete`
* `pipeline_retry`
* `batch_complete`

### Metrics Tracked

* Execution time per pipeline step
* Batch duration
* Success / failure ratio
* Semaphore wait time (concurrency saturation signal)

### Grafana Integration

The system is integrated with **Grafana** for metrics visualization and monitoring. This enables:

* Latency tracking across pipeline stages
* Monitoring of system behavior under real execution load
* Detection of degradation in LLM response quality or timing

Observability is not an afterthought — it is a first-class design requirement.

---

## Frontend (Minimal Interface)

A lightweight frontend is included to:

* Select leads from the persisted dataset
* Trigger batch execution
* Visualize outputs per lead
* Copy generated emails

This interface is intentionally minimal:

> It exists to expose system behavior, not to abstract it.

---

## Deployment

* **Backend:** Fly.io
* **Database:** PostgreSQL via Supabase
* **Observability:** Grafana
* **Frontend:** Vercel (optional)

The system is live and operational in a real environment.

---

## Tech Stack

* Python (`asyncio`)
* FastAPI
* PostgreSQL (Supabase)
* OpenAI API
* Fly.io
* Grafana
* Structured logging (JSON)

---

## Design Trade-offs

* **Synchronous batch response**

  * Simpler execution model
  * No queue or background workers required at current scale

* **No global distributed rate limiting**

  * Acceptable for current scope
  * Can evolve with Redis-based distributed control

* **Database-backed research, LLM-driven generation**

  * Research is now fully deterministic (replaced LLM-based enrichment)
  * Reduces variance in the most data-sensitive pipeline stage

---

## Future Improvements

* Queue-based execution (background workers)
* Distributed rate limiting
* Streaming responses
* Per-lead output versioning

---

## Key Insight

> Concurrency is introduced at the system boundary, while consistency is preserved inside each pipeline.

The data layer enforces determinism where it matters most — at the point where AI receives its input. This is the foundation that makes the rest of the system controllable.

---

## Repository Purpose

This repository demonstrates **backend engineering applied to AI systems**: how to build a workflow that incorporates non-deterministic dependencies (LLMs) without sacrificing reliability, reproducibility, or observability.

It is a working system, not a prototype. It runs on real infrastructure, against a real database, with real monitoring in place.

Emphasis: **control**, **reliability**, **scalability**, **observability**.

---

## Author

Alejandro Saavedra Ruiz
Backend Developer — AI Systems & Automation

* GitHub: https://github.com/AlejandroSRdev
* LinkedIn: https://www.linkedin.com/in/alejandrosrdev

---
