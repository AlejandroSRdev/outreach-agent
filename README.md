# Outreach Agent — AI-Powered Batch Outreach System

## Overview

Outreach Agent is a backend system designed to generate **high-quality, personalized outbound emails at scale**, using controlled AI pipelines.

The system processes structured lead input and executes a **multi-step pipeline** per lead, ensuring that AI remains a **governed dependency**, not a source of uncontrolled behavior.

This project focuses on **system design, reliability, and observability**, rather than raw AI usage.

---

## Purpose

Most AI-based outreach tools fail due to:

* Uncontrolled outputs
* Lack of structure and validation
* Poor handling of concurrency and failures
* Over-reliance on a single model call

Outreach Agent addresses this by:

> Treating AI as a non-deterministic external system that must be constrained, validated, and observed.

---

## System Design

### High-Level Flow

```
Batch Request → Orchestrator → Pipelines (per lead)
                                ↓
                     research → generation → refinement
                                ↓
                           Structured Output
```

---

### Core Principles

* **Deterministic control over non-deterministic AI**
* **Separation of concerns (architecture-driven)**
* **Failure isolation per lead**
* **Controlled concurrency**
* **Observable system behavior**

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

  * LLM providers
  * External integrations

---

## Concurrency Model

* **Batch-level concurrency** using `asyncio.gather`
* **Concurrency control** via `asyncio.Semaphore`
* Each lead is processed independently

This ensures:

* Parallel execution without resource exhaustion
* Predictable behavior under load
* Isolation of failures

---

## Pipeline Design

Each lead goes through a **sequential pipeline**:

### 1. Research (LLM-assisted)

* Enriches company context
* Does NOT infer primary input data (e.g. role)

### 2. Generation (LLM)

* Produces initial email draft

### 3. Refinement (LLM)

* Improves clarity, tone, and structure
* Enforces output constraints

---

## Input Contract

```json
{
  "name": "string",
  "company": "string",
  "role": "string"
}
```

* Fully deterministic
* No inference of primary data
* Validated before pipeline execution

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

* Each lead is processed independently
* Failures do not affect the batch

---

## Reliability Mechanisms

### Timeouts

* Each step is bounded (`asyncio.wait_for`)
* Prevents indefinite blocking

### Retry Strategy

* Retries only for LLM-related failures
* Uses context-aware correction hints

### Validation

* Structured output enforced before returning results
* Invalid outputs are rejected

---

## Observability

The system includes structured logging:

* `batch_start`
* `pipeline_start`
* `generation_complete`
* `pipeline_retry`
* `batch_complete`

Tracked metrics:

* Execution time per pipeline
* Batch duration
* Success / failure ratio
* Semaphore wait time (saturation signal)

---

## Frontend (Minimal Interface)

A lightweight frontend is included to:

* Select up to 20 leads from a predefined list
* Trigger batch execution
* Visualize outputs per lead
* Copy generated emails

This interface is intentionally minimal:

> It exists to expose system behavior, not to abstract it.

---

## Deployment

* Backend: Render
* Frontend: Vercel (optional)
* No database required (static lead input)

---

## Tech Stack

* Python (asyncio)
* FastAPI
* LLM APIs (OpenAI)
* Structured logging
* JSON-based contracts

---

## Design Trade-offs

* **Synchronous batch response**

  * Simpler system
  * No queue or background workers

* **No global rate limiting**

  * Acceptable for current scope
  * Can evolve with Redis / distributed control

* **LLM-based research**

  * Flexible but less deterministic
  * Future improvement: replace with DB or API sources

---

## Future Improvements

* Queue-based execution (background workers)
* Distributed rate limiting
* Persistent lead storage
* Streaming responses
* Hybrid research (LLM + structured data)

---

## Key Insight

> Concurrency is introduced at the system boundary, while consistency is preserved inside each pipeline.

This allows:

* Parallel execution
* Without sacrificing correctness

---

## Repository Purpose

This project is not intended as a finished product.

It is a **demonstration of backend system design applied to AI workflows**, focusing on:

* Control
* Reliability
* Scalability
* Observability

---

## Author

Alejandro Saavedra Ruiz
Backend Developer — AI Systems & Automation

* GitHub: https://github.com/AlejandroSRdev
* LinkedIn: https://www.linkedin.com/in/alejandrosrdev

---