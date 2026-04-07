# Outreach Agent — Concurrency & System Design Overview

## 1. Concurrency Model

### 1.1 External Concurrency (Batch Level)
- **Implementation**: `asyncio.gather`
- **Purpose**: Executes multiple pipelines concurrently, with each lead processed independently.

```python
await asyncio.gather(*coroutines, return_exceptions=True)
```

#### Key Properties:
- **Non-blocking execution**: Tasks run concurrently without blocking.
- **Failure isolation**: Failures in one pipeline do not affect others.
- **Single response**: Returns a single response when all tasks complete.

#### Concurrency Control:
- **Mechanism**: `asyncio.Semaphore`
- **Purpose**: Prevents resource exhaustion (e.g., LLM calls, memory, latency spikes).

```python
async with semaphore:
    await pipeline.run(lead)
```

#### Behavior:
- **Max N pipelines**: Limits the number of pipelines running simultaneously.
- **Backpressure**: Remaining tasks wait, ensuring predictable system behavior under load.

#### Observability:
- **Semaphore wait time**: Measured and logged for monitoring saturation.

```python
wait_ms = ...
logger.info("semaphore_acquired", ...)
```

- **Purpose**: Detect saturation and evaluate if the concurrency limit (N) is adequate.

---

## 2. Pipeline Execution Model

### 2.1 Sequential Internal Flow
- **Steps**: `research → generation → refinement`
- **Purpose**: Maintains consistency and avoids invalid intermediate states.

### 2.2 Timeouts (Failure Control)
- **Mechanism**: `asyncio.wait_for`
- **Purpose**: Prevents indefinite blocking and controls unreliable external dependencies (e.g., LLMs).

```python
await asyncio.wait_for(step(), timeout=...)
```

---

## 3. Retry Strategy

### 3.1 Controlled Retry Mechanism
- **Implementation**: `with_retry`
- **Purpose**: Retries only on specific errors (e.g., `is_llm_error`).

```python
await with_retry(...)
```

### 3.2 Context-Aware Retry
- **Mechanism**: Uses dynamic correction hints based on previous failures.

```python
_build_correction_hint(...)
```

- **Purpose**: Improves output quality and avoids blind retries.

---

## 4. Failure Isolation
- **Mechanism**: `asyncio.gather(..., return_exceptions=True)`
- **Purpose**: Ensures that each pipeline failure does not affect others.

#### Result Structure:
```json
{
  "lead": "...",
  "status": "success | failed",
  "result | error": ...
}
```

---

## 5. Observability

### 5.1 Structured Logging
- **Key Events**:
  - `batch_start`
  - `pipeline_start`
  - `generation_complete`
  - `pipeline_retry`
  - `batch_complete`

### 5.2 Metrics Captured:
- Batch duration
- Pipeline duration
- Semaphore wait time
- Success/failure counts

### 5.3 Goal:
- Trace execution
- Diagnose performance issues
- Understand system behavior under load

---

## 6. System Architecture

### 6.1 Separation of Responsibilities
- **Orchestrator**:
  - Handles concurrency
  - Manages batch execution
  - Applies system-level controls (semaphore, gather)
- **Pipeline**:
  - Handles business logic
  - Executes steps sequentially
  - Manages retries and validation

---

## 7. System Characteristics

### 7.1 Current Design Scope
- Single-process, single-event-loop system
- I/O-bound workload (LLM calls)
- Bounded batch size
- Controlled concurrency

### 7.2 Strengths
- Predictable execution under load
- Controlled use of external resources
- Failure isolation
- Clear observability
- Clean architectural separation

### 7.3 Known Limitations
- No global rate limiting across instances
- No request-level queue
- No background job processing
- Synchronous request/response model (waits for full batch)

---

## 8. Scaling Path (Future)

### When Needed, the System Can Evolve To:
- Queue-based architecture (background jobs)
- Distributed rate limiting (e.g., Redis)
- Worker-based execution model
- Streaming or polling response patterns

---

## 9. Key Insight
Concurrency is introduced at the system boundary (between pipelines), while consistency is preserved within each pipeline.

### This Ensures:
- **Parallelism without loss of control**
- **Scalability without breaking correctness**