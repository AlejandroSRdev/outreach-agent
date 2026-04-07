# Pipeline

Sequential, 3-stage execution. Each stage is isolated. Failures stop the pipeline.

---

## Flow

```
research → generation → refinement
```

No stage mutates the output of a previous stage silently.
Each stage output is validated before the next stage begins.

---

## Stage 1: Research

**AI used:** No — fully deterministic.

**Input:**
- Lead record (name, role, context)
- Company record (industry, description, product, value_proposition, target_market, recent_activity, strategic_focus)

**Operation:**
- Read lead from `leads` table
- Lookup company from `companies` table by normalized name match
- Assemble `EnrichedContext`

**Output — `EnrichedContext`:**
- lead_id, name, company, role, context
- industry, description, product, value_proposition, target_market, recent_activity, strategic_focus
- assembled_at

**Validation:**
- All required company fields must be present (non-null)
- `recent_activity` is the only nullable field

**Failure conditions:**
- Company not found in `companies` table → hard fail, no retry
- DB error → hard fail, no retry

---

## Stage 2: Generation

**AI used:** Yes.

**Input:** `EnrichedContext`

**Operation:**
- Construct prompt from enriched context
- Call AI adapter
- Parse response as JSON
- Validate against `FinalMessage` schema
- Compute `word_count` from body (system-computed, not AI-supplied)

**Output — `FinalMessage` (draft):**
- subject: str [5–150 chars]
- body: str [100–1500 chars]
- personalization_points: list[str] [min 1 item]
- risk_flags: list[str] [0–N items]
- tone: enum { professional } [hardcoded, system-enforced]
- word_count: int [computed]

**Validation:**
- Full schema check against `FinalMessage`
- `tone` must match `professional`
- `subject` and `body` non-empty
- `personalization_points` min 1 item

**Failure conditions:**
- AI timeout → fail, retry eligible
- AI returns unparseable JSON → fail, retry eligible
- Schema validation fails → fail, retry eligible
- Max retries exceeded → hard fail

---

## Stage 3: Refinement

**AI used:** Yes.

**Input:** Draft `FinalMessage` + `EnrichedContext`

**Operation:**
- Construct prompt from draft message + original context
- Call AI adapter
- Parse response as JSON
- Validate against `FinalMessage` schema
- Recompute `word_count`

**Output:** Final `FinalMessage` (same schema as Generation output)

**Validation:** Identical to Generation stage.

**Failure conditions:** Identical to Generation stage.

**Note:** Refinement improves tone, clarity, and constraint adherence. It does not regenerate from scratch.

---

## Retry Strategy

| Applies to | Does not apply to |
|---|---|
| Transient AI failures (timeout, invalid JSON, schema violation) | Data failures (company not found) |
| Generation stage | Research stage |
| Refinement stage | DB errors |

- Max retries per stage: **2** (3 total attempts)
- Backoff: fixed 1s between attempts
- Prompt is identical on retry
- Each attempt is logged individually
- Only final result (success or last failure) is persisted to `pipeline_stage_results`

---

## Failure Propagation

1. Stage fails → stage result persisted → pipeline halts
2. `outreach_runs` status set to `failed` with `failure_reason`
3. No message is written to `generated_messages`
4. `ExecutionResult` returned with `status: failed`
