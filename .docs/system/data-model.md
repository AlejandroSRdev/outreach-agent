# Data Model

5 tables. 3 domain entities + 2 operational tables.

---

## Entities

### `companies`
Pre-seeded reference data. Not managed by the pipeline.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL, UNIQUE |
| industry | VARCHAR(100) | NOT NULL |
| description | TEXT | NOT NULL |
| product | TEXT | NOT NULL |
| value_proposition | TEXT | NOT NULL |
| target_market | TEXT | NOT NULL |
| recent_activity | TEXT | NULLABLE |
| strategic_focus | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

---

### `leads`
One record per unique lead identity. Duplicate detection on `(lower(name), company_id, lower(role))`.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| company_id | UUID | FK → companies.id, NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| role | VARCHAR(100) | NOT NULL |
| context | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |

Duplicate submission → `409 Conflict`. No second run created.

---

### `generated_messages`
Valid, finalized messages only. Never written on pipeline failure.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| lead_id | UUID | FK → leads.id, NOT NULL |
| run_id | UUID | FK → outreach_runs.id, NOT NULL, UNIQUE |
| subject | VARCHAR(150) | NOT NULL |
| body | TEXT | NOT NULL |
| personalization_points | JSONB | NOT NULL |
| risk_flags | JSONB | NOT NULL |
| tone | VARCHAR(20) | NOT NULL |
| word_count | INTEGER | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## Operational Tables

### `outreach_runs`
One record per pipeline execution. Written before the pipeline starts. Updated on completion or failure.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| lead_id | UUID | FK → leads.id, NOT NULL |
| status | VARCHAR(20) | NOT NULL — `completed` / `failed` |
| failure_reason | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |
| completed_at | TIMESTAMPTZ | NULLABLE |

---

### `pipeline_stage_results`
One record per stage executed. Written after each stage regardless of outcome.

| Field | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| run_id | UUID | FK → outreach_runs.id, NOT NULL |
| stage | VARCHAR(20) | NOT NULL — `research` / `generation` / `refinement` |
| status | VARCHAR(20) | NOT NULL — `success` / `failed` |
| input_snapshot | JSONB | NOT NULL |
| output_snapshot | JSONB | NULLABLE |
| failure_reason | TEXT | NULLABLE |
| duration_ms | INTEGER | NOT NULL |
| ai_used | BOOLEAN | NOT NULL |
| tokens_used | INTEGER | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## Relationships

```
companies ──< leads ──< outreach_runs ──< pipeline_stage_results
                  └───< generated_messages
```

| Relationship | Cardinality | FK |
|---|---|---|
| Company → Leads | One-to-many | leads.company_id → companies.id |
| Lead → Messages | One-to-many | generated_messages.lead_id → leads.id |
| Lead → Runs | One-to-many | outreach_runs.lead_id → leads.id |
| Run → Message | One-to-one | generated_messages.run_id → outreach_runs.id (UNIQUE) |
| Run → Stage Results | One-to-many | pipeline_stage_results.run_id → outreach_runs.id |

---

## Deletion Behavior

| FK | On Delete |
|---|---|
| leads.company_id | RESTRICT — a company with leads cannot be deleted |
| outreach_runs.lead_id | RESTRICT — a lead with runs cannot be deleted |
| generated_messages.lead_id | RESTRICT |
| generated_messages.run_id | RESTRICT |
| pipeline_stage_results.run_id | CASCADE — stage results are owned by the run |

---

## Constraints Summary

- A company can exist without leads (allowed — pre-seeded independently)
- A lead can exist without messages (allowed — pipeline may fail)
- A message MUST belong to exactly one lead and one run
- A run MUST belong to exactly one lead
- A run produces at most one message (`run_id` UNIQUE on `generated_messages`)
- No orphan stage results — CASCADE delete follows the run

---

## Consistency Validation

- No circular dependencies
- Ownership is unambiguous at every level
- Orphan records: only `companies` and `leads` can exist without downstream records — both are valid states
- Invalid states (partial messages, unvalidated output) are never persisted
