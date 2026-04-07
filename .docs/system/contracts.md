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
