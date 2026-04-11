# Project Technical Review for Senior Python / Systems Roles

---

## 1. System Overview

An AI-powered outreach email generation backend. Given a list of leads (name, company, role), the system:

1. Enriches each lead via LLM-based research inference.
2. Generates a personalized email draft.
3. Refines and validates that draft against hard structural constraints.
4. Returns structured results for an entire batch with per-lead success/failure tracking.

The system is designed to run multiple leads concurrently while protecting downstream rate-limited external APIs (OpenAI). Every stage is async, bounded, and retriable.

---

## 2. Architecture Overview

```
src/
├── domain/          → Entities, value objects, abstract interfaces (Protocols)
├── application/     → Orchestration, use cases, business rules
├── infrastructure/  → Adapters: FastAPI, OpenAI, SQLAlchemy
└── config/          → Environment-driven configuration (Pydantic BaseSettings)
```

### Layer responsibilities

| Layer | Responsibility | External dependencies |
|---|---|---|
| `domain` | Business rules, data contracts, port interfaces | None |
| `application` | Pipeline sequencing, retry logic, batch orchestration | Ports only (abstractions) |
| `infrastructure` | I/O, HTTP, LLM calls, DB | OpenAI SDK, FastAPI, SQLAlchemy |
| `config` | Runtime config from environment | Pydantic BaseSettings |

### Why structured this way

The dependency rule flows inward: `infrastructure` depends on `application`, `application` depends on `domain`, `domain` depends on nothing. This is not cosmetic clean architecture — it has a concrete technical consequence: the core pipeline (`OutreachPipeline`) is testable without a real OpenAI client, without an HTTP server, and without environment setup. You inject any object that satisfies the `ResearchProvider` or `AIClient` Protocol.

---

## 3. Async / Concurrency Model

### 3.1 Single-lead pipeline — `asyncio` with timeouts

**What:** `OutreachPipeline.run()` is a coroutine that chains three async operations: research, generation, refinement.

**Why async:** All three stages make network I/O calls (OpenAI API). Running them synchronously would block the event loop for the entire duration of each call. Async allows the event loop to handle other coroutines (other leads in the batch) while waiting on I/O.

**Timeout enforcement per stage:**
```python
await asyncio.wait_for(self.research.enrich(lead), timeout=self.research_timeout_s)
await asyncio.wait_for(self.ai.generate(enriched, hint), timeout=self.generation_timeout_s)
await asyncio.wait_for(self.ai.refine(draft, hint), timeout=self.refinement_timeout_s)
```

Each stage has an independent timeout (30s research, 30s generation, 20s refinement). This is not a single global pipeline timeout — each boundary is isolated. Trade-off: a pathological case where every stage takes 29s would still consume 89s total. A global deadline would prevent that, but adds coordination complexity.

**Why `asyncio.wait_for` and not a decorator:** `wait_for` operates at the coroutine call site, not at the function definition. This means the timeout is enforced at the boundary where the caller has context — not hidden inside the callee. This matters when you want stage-specific timeouts rather than uniform ones.

### 3.2 Batch orchestration — `asyncio.gather` + `asyncio.Semaphore`

**What:** `BatchOrchestrator.run_batch()` processes a list of leads concurrently.

```python
results = await asyncio.gather(
    *[self._run_one(lead) for lead in leads],
    return_exceptions=True
)
```

**Why `gather` with `return_exceptions=True`:** Without this flag, a single failed lead cancels the entire batch — unacceptable for a batch job. With `return_exceptions=True`, exceptions are captured as values. Each lead gets an independent result. The orchestrator then classifies each result as `success` or `failed` post-gather.

**Why `Semaphore` for bounded concurrency:**
```python
async with self.semaphore:
    result = await self.pipeline.run(lead)
```

`asyncio.gather` without a semaphore launches all coroutines immediately. For a batch of 20 leads, that means up to 20 concurrent OpenAI calls. Problems: API rate limits, memory pressure, and amplified failure blast radius. The semaphore enforces a ceiling (configured via `max_concurrent_pipelines`, default 10). Coroutines that can't acquire the semaphore block at the `async with` line — they're suspended, not queued on OS threads. This is cooperative backpressure.

**Trade-off:** The semaphore ceiling is static. Under high load (e.g., 100 leads), the effective throughput is `min(semaphore_limit, API_rate_limit) / avg_pipeline_duration`. You can't increase throughput beyond what the downstream API allows — the semaphore just controls local resource pressure, not end-to-end latency.

### 3.3 FastAPI + Uvicorn event loop

**What:** FastAPI is an ASGI framework. Uvicorn runs a single event loop per worker process. All async route handlers share this loop.

**Why this matters:** A blocking call inside any async handler (e.g., `time.sleep`, synchronous file I/O, a blocking HTTP client) would stall the entire server — not just the current request. The system avoids this by using `AsyncOpenAI` (async OpenAI SDK) and `AsyncSession` (SQLAlchemy async engine). There are no `requests.get()` calls, no synchronous waits.

**Startup via `lifespan`:** The AsyncOpenAI client, semaphore, and orchestrator are created once during app startup in the lifespan context manager and stored in `app.state`. This is correct — you do not create a new AsyncOpenAI client per request, which would be wasteful and incorrect (clients hold connection pools).

---

## 4. Reliability / Fault Tolerance

### 4.1 Retry logic

**Location:** `infrastructure/ai/retry.py` + `application/services/pipeline.py`

**Mechanism:** `with_retry()` is a generic async utility:
```python
async def with_retry(fn, max_retries=2, delay=0.5, should_retry=None, on_retry=None)
```

The callable `fn` receives the attempt number. This is deliberate — it allows the caller to change behavior on retry (pass a corrective hint to the LLM on attempt 2+).

**Retry predicate — `is_llm_error`:** Not all errors are retryable. Network errors, auth failures, or hard domain errors should not be retried blindly. The predicate checks for `ValidationError` or known retryable substrings (`"too short"`, `"too long"`, `"invalid JSON"`). Retrying on hard failures (auth, quota exhausted) would waste time and add latency without benefit.

**Adaptive correction hints:** On retry, the pipeline doesn't just retry the same prompt:
```python
if "too long" in str(last_error):
    hint = f"Body is too long ({len(last_result.body)} chars). Cut to under 1500."
```

This is key: the retry is not blind. It passes contextual feedback to the LLM about exactly what constraint was violated. This improves convergence probability significantly versus retrying with the same prompt.

**Max retries = 2:** Low ceiling by design. LLM-based retries are expensive (latency + token cost). If the model can't correct in 3 attempts, it's more likely a prompt/context issue than a transient failure.

### 4.2 Timeout handling

Three independent timeouts. If `asyncio.wait_for` raises `asyncio.TimeoutError`, it propagates up through the pipeline and is caught by the orchestrator's `return_exceptions=True` — the lead is marked `failed` with the timeout error. No global state is corrupted. Other leads continue processing.

**What's missing:** There's no circuit breaker. If the OpenAI API is degraded and all requests time out, the system will run every lead to timeout before failing. A circuit breaker would short-circuit after N consecutive failures and fail fast for subsequent requests.

### 4.3 Validation as a reliability mechanism

`GeneratedEmail` has Pydantic field constraints (subject 5-150 chars, body 100-1500 chars). These are enforced at the infrastructure boundary — the LLM's response is not trusted. If the model returns an email that violates these constraints, a `ValidationError` is raised, which triggers the retry logic. The domain model defines correctness; the infrastructure adapter is responsible for satisfying it.

This is the correct model: domain defines the contract, infrastructure adapts to it. Not the reverse.

### 4.4 Exception isolation

`asyncio.gather(return_exceptions=True)` is the top-level exception boundary for batches. Individual lead failures do not propagate. The orchestrator maps exception objects to structured `{"status": "failed", "error": str(e)}` entries. The HTTP response always returns 200 with per-lead status — the batch never fails at the HTTP layer due to individual lead errors.

**Trade-off:** This can be confusing. A caller receiving HTTP 200 must inspect individual results to know what actually failed. A partial-success response code (207 Multi-Status) would be more semantically precise, but adds client-side handling complexity.

---

## 5. Scalability / Performance Considerations

### Current bottlenecks

1. **Semaphore is process-local.** The concurrency ceiling (`max_concurrent_pipelines=10`) is per-process. If you run 4 Uvicorn workers, you have 4 independent semaphores — no coordination. You could have 40 concurrent OpenAI calls instead of 10. At scale, you'd need a distributed rate limiter (Redis-backed token bucket or sliding window).

2. **Single event loop per worker.** Python's GIL is irrelevant for I/O-bound async work, but a single event loop still serializes CPU work (JSON parsing, Pydantic validation, prompt building). These are fast, but under extreme concurrency they accumulate.

3. **No request queuing.** If 100 requests arrive simultaneously, 100 `asyncio.gather` coroutines are created. The semaphore bounds concurrent pipeline execution, but the coroutines themselves are all alive, holding memory and event loop scheduling slots. A proper queue (e.g., Celery, ARQ, Redis Streams) would decouple HTTP acceptance from processing.

4. **Three sequential LLM calls per lead.** Research → Generate → Refine is a serial chain. Each call is ~2-5s. A single lead takes 6-15s minimum. With semaphore=10 and batch=20, tail latency for the full batch is (20/10) * ~15s = ~30s. This is a fundamental constraint of the LLM dependency, not an implementation bug.

5. **No caching.** Research enrichment for the same company is repeated on every request. LLM inference cost and latency for "what does Stripe do?" is identical on the 1st and 100th call. A cache keyed on `(company, role)` with TTL could eliminate redundant research calls.

### What would need to change for larger scale

| Scale target | Required change |
|---|---|
| Multiple workers | Distributed rate limiter (Redis) to replace per-process semaphore |
| High request volume | Async task queue (ARQ/Celery) to decouple HTTP from pipeline execution |
| Cost optimization | Research result caching by `(company, role)` |
| Latency reduction | Parallelize research + generation stages where possible (research is prerequisite, but generation and refinement could overlap with other leads) |
| Reliability at scale | Circuit breaker on OpenAI client, dead-letter queue for failed leads |

---

## 6. Senior-Level Engineering Decisions

### 6.1 Protocols over ABC for dependency inversion

Using `typing.Protocol` instead of `ABC` means implementations don't need to import or inherit from anything in the domain layer. A third-party library or a mock in a test satisfies the protocol as long as it has the right method signatures. This is structural subtyping — the interface is defined by shape, not hierarchy.

**Why it matters:** It eliminates coupling at the import level. `infrastructure` implements `domain` protocols without importing them. This is a critical distinction when thinking about module boundaries and circular import prevention.

### 6.2 Semaphore created in `lifespan`, not in the route handler

Creating a new `asyncio.Semaphore` per request would be useless — each request would have its own unbounded semaphore. The semaphore must be shared across all concurrent requests. Creating it in `lifespan` and storing it in `app.state` makes it a process-level resource, correctly shared across all requests on that worker.

### 6.3 Stage-specific LLM configs (temperature, max_tokens)

Research uses `temperature=0.2` (deterministic inference), generation uses `temperature=0.7` (creative), refinement uses `temperature=0.3` (conservative editing). These are not arbitrary — they map to the cognitive nature of each task. High temperature for validation and editing produces nondeterministic corrections, which is exactly what you don't want when enforcing hard constraints.

**Implication for reliability:** Lower temperature on refinement means the model's corrections are more consistent and predictable. This reduces the variance of retry failures.

### 6.4 `return_exceptions=True` as architectural decision

This is not just a Python detail — it reflects a deliberate system design choice: **individual lead failures are not system failures**. The batch job has a defined success model (per-item status reporting) rather than all-or-nothing semantics. The choice of `return_exceptions=True` encodes this invariant.

### 6.5 Adaptive hints as a feedback loop

Rather than generic retry, the pipeline closes a feedback loop between the validator and the generator. The error message from Pydantic (`"body too long: 1623 chars"`) is transformed into a corrective instruction to the LLM. This is a lightweight form of self-correcting prompt chain — the system is its own critic within bounds.

### 6.6 Per-stage timeouts, not a global pipeline timeout

Each stage has a timeout that reflects its expected duration independently. This prevents a slow research call from consuming the entire pipeline budget and leaving zero time for generation. It also makes timeout attribution precise: you know *which stage* timed out from the exception trace, which is critical for debugging and monitoring.

---

## 7. Potential Interview Talking Points

**On async/concurrency:**
> "The batch orchestrator uses `asyncio.gather` with `return_exceptions=True` to run all leads concurrently, but constrains parallelism with a shared semaphore. The key insight is that the semaphore is a process-level resource created at startup — not per-request — and it acts as cooperative backpressure against the downstream LLM API."

**On retry design:**
> "Retries aren't blind. On each retry, the pipeline passes a corrective hint derived from the previous failure's error message — character counts, constraint violations. So the LLM on attempt 2 has more context than on attempt 1. This dramatically improves convergence compared to static retries."

**On fault isolation:**
> "`gather(return_exceptions=True)` is the exception boundary. A lead that times out, fails validation, or hits a JSON parse error is isolated. The orchestrator maps these to structured failures in the response. The HTTP layer always returns 200 — the semantics of batch partial-failure are expressed in the payload, not the status code."

**On architecture:**
> "The domain layer defines correctness — field length constraints, data contracts, port interfaces. The infrastructure layer is responsible for satisfying those contracts. If the LLM returns an invalid response, that's an infrastructure failure, not a domain error. The retry logic lives at the application layer because it's an orchestration concern — not inside the OpenAI adapter."

**On performance:**
> "The main bottleneck is the serial LLM chain per lead — three synchronous calls, each 2-5 seconds. The semaphore controls local resource pressure, but doesn't change the fundamental latency. At scale, you'd decouple HTTP acceptance from pipeline execution using a task queue, and add a distributed rate limiter to replace the per-process semaphore."

**On scaling limits:**
> "The semaphore is per-process. With multiple Uvicorn workers, you lose coordination — each worker has its own semaphore. To enforce a global ceiling across workers, you'd need a distributed counter — Redis with SETNX or a token bucket implementation."

**On observability:**
> "Every significant state transition emits a structured log event with a unique run ID and batch ID. This means you can reconstruct the full execution trace of any lead from logs alone — which stage failed, what the retry reason was, how long the semaphore wait was. That's the minimum you need to debug a production incident without a debugger."

---

## 8. Weaknesses / Honest Limitations

| Area | Limitation |
|---|---|
| **No circuit breaker** | If OpenAI is degraded, every lead in the batch will run to timeout before failing. A circuit breaker would fail-fast after N consecutive failures. |
| **Per-process semaphore** | Doesn't coordinate across workers. Not suitable for multi-process or multi-instance deployments without a distributed rate limiter. |
| **No queue / backpressure at HTTP layer** | Under high traffic, large numbers of coroutines are created immediately. No admission control beyond `max_batch_size=20` per request. |
| **No idempotency** | Calling the endpoint twice with the same leads produces two independent results. There's no deduplication or lead-level state persistence. |
| **Research is stateless and uncached** | The same company is re-researched on every call. At scale, this is redundant cost and latency. |
| **No dead-letter / retry queue** | Failed leads are reported in the response but not re-queued for later processing. A production system would persist failures and allow replay. |
| **No observability instrumentation** | Structured logs are present, but there's no metrics emission (request counts, latency histograms, retry rates). Without metrics, you can't set alerts or build dashboards. |
| **Global pipeline timeout is absent** | Three independent timeouts exist, but no hard deadline for the entire pipeline. A degenerate case where each stage takes 29s would still complete after 89s. |
| **Prompt coupling to LLM behavior** | The retry/hint logic depends on specific error message substrings (`"too short"`, `"too long"`). If Pydantic's error message format changes, the retry predicate silently breaks. Should assert on structured error fields, not string matching. |
| **Single model dependency** | Everything runs on `gpt-4o-mini`. There's no fallback model if that model is unavailable. A provider abstraction exists (Protocol), but no alternative implementation is registered. |
