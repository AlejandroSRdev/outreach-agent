# 📄 Outreach Agent — Contracts

## 1. External Contracts

### LeadInput

```python
class LeadInput(BaseModel):
    name: str
    company: str
```

---

### GeneratedEmail

```python
class GeneratedEmail(BaseModel):
    subject: str
    body: str
```

**Constraints:**

* subject: 5–150 characters
* body: 100–1500 characters

---

## 2. Internal Contracts

### EnrichedLead

```python
class EnrichedLead(BaseModel):
    name: str
    company: str

    role: Optional[str]
    additional_context: Optional[str]

    industry: Optional[str]
    description: Optional[str]
    product: Optional[str]
    value_proposition: Optional[str]
    target_market: Optional[str]
    recent_activity: Optional[str]
    strategic_focus: Optional[str]

    assembled_at: datetime
```

---

### DraftEmail

```python
class DraftEmail(BaseModel):
    subject: str
    body: str
```

---

### GenerationMetadata (optional)

```python
class GenerationMetadata(BaseModel):
    word_count: int
    warnings: list[str] = []
```

---

## 3. HTTP API Contracts

### POST /campaigns

**File:** `src/infrastructure/api/routers/campaigns.py`

**Purpose:** Create a campaign by selecting leads that match the given filters. Returns the campaign ID and the number of matched leads.

---

#### Request

```json
{
  "industry": "Fintech",
  "tags": ["B2B", "SaaS"]
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `industry` | `string` | Yes | Must be a value from `ALLOWED_INDUSTRIES` (`domain/constants.py`) |
| `tags` | `list[string]` | No | If provided, every element must be a value from `ALLOWED_TAGS` (`domain/constants.py`) |

---

#### Response — 201 Created

```json
{
  "campaign_id": 7,
  "total_leads": 12
}
```

| Field | Type | Description |
|---|---|---|
| `campaign_id` | `int` | ID of the created campaign in the `campaigns` table |
| `total_leads` | `int` | Number of leads matched and linked to the campaign |

---

#### Error Responses

| Status | Condition | Body |
|---|---|---|
| `422 Unprocessable Entity` | `industry` not in `ALLOWED_INDUSTRIES` | `{ "detail": "Invalid industry: <value>" }` |
| `422 Unprocessable Entity` | One or more `tags` not in `ALLOWED_TAGS` | `{ "detail": "Invalid tags: [<values>]" }` |
| `400 Bad Request` | No leads match the given filters | `{ "detail": "No leads match the given filters." }` |

---

#### Invariants

- A campaign is never created if zero leads match — the DB write is never reached.
- Campaign creation is atomic: the `campaigns` row and all `campaign_leads` rows are written in a single transaction. Either both commit or neither does.
- `campaign_leads` is write-once. No other operation modifies these rows after creation.
- Validation is enforced by the domain (use case) before any DB interaction.
