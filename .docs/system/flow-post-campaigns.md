# Flow: POST /campaigns

## Layers involved

| Layer | Files |
|---|---|
| Infrastructure — HTTP | `src/infrastructure/api/routers/campaigns.py` |
| Infrastructure — Wiring | `src/infrastructure/api/app.py` |
| Application — Use Case | `src/application/use_cases/create_campaign.py` |
| Domain — Validation | `src/domain/constants.py` |
| Domain — Port | `src/domain/ports/__init__.py` |
| Infrastructure — DB | `src/infrastructure/db/campaigns.py` |
| Infrastructure — Connection | `src/infrastructure/db/connection.py` |

---

## Diagram

```mermaid
flowchart TD
    A[/POST /campaigns\ncampaign_id · tags/]:::infra

    A --> B[Extract body: industry · tags\nrouters/campaigns.py]:::infra

    B --> C[Resolve use case from app.state\napp.py · Depends]:::infra

    C --> D{industry in\nALLOWED_INDUSTRIES?\ndomain/constants.py}:::domain

    D -->|No| E[/422 Unprocessable Entity\nInvalidFilterError/]:::error
    D -->|Yes| F{tags provided?}:::domain

    F -->|No| H
    F -->|Yes| G{all tags in\nALLOWED_TAGS?\ndomain/constants.py}:::domain

    G -->|No| E2[/422 Unprocessable Entity\nInvalidFilterError/]:::error
    G -->|Yes| H

    H[Open AsyncSession\ndb/connection.py · SessionLocal]:::infra

    H --> I[/SELECT id FROM leads\nWHERE industry = $1\nAND tags && $2::text[]\ndb/campaigns.py · filter_lead_ids/]:::db

    I --> J{lead_ids\nempty?}:::domain

    J -->|Yes| K[/400 Bad Request\nEmptyCampaignError/]:::error
    J -->|No| L[Build filters_dict\nuse_cases/create_campaign.py]:::app

    L --> M[Open AsyncSession + BEGIN transaction\ndb/connection.py · SessionLocal]:::infra

    M --> N[/INSERT INTO campaigns\nfilters · created_at\nRETURNING id\ndb/campaigns.py · create_campaign/]:::db

    N --> O[/Bulk INSERT INTO campaign_leads\none row per lead_id\ndb/campaigns.py · create_campaign/]:::db

    O --> P[COMMIT]:::db

    P --> Q[/201 Created\ncampaign_id · total_leads/]:::success

    classDef infra fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    classDef domain fill:#fef9c3,stroke:#ca8a04,color:#713f12
    classDef app fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef db fill:#f3e8ff,stroke:#9333ea,color:#3b0764
    classDef error fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef success fill:#d1fae5,stroke:#059669,color:#064e3b
```

---

## Notes

- **Validation is domain-owned.** `ALLOWED_INDUSTRIES` and `ALLOWED_TAGS` in `constants.py` are static lists — no runtime DB reads. The use case enforces them before any query is executed.
- **Two separate DB calls.** `filter_lead_ids` and `create_campaign` each open their own session. They are not wrapped in a shared transaction — this is intentional: lead matching is read-only and does not need to be atomic with the insert.
- **`create_campaign` is atomic.** The campaign header and all `campaign_leads` rows are written in a single transaction. Either both commit or neither does.
- **`campaign_leads` is write-once.** After campaign creation, no other part of the system ever modifies these rows. Execution logic reads them but never writes to them.
- **Dependency injection via `app.state`.** The use case instance is created once in the lifespan (`app.py`) and injected into the router via `Depends(get_create_campaign_use_case)`. The router owns no logic — it only maps HTTP to use case calls.
