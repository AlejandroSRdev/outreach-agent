CREATE TABLE IF NOT EXISTS executions (
    id              SERIAL PRIMARY KEY,
    campaign_id     INT NOT NULL REFERENCES campaigns(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    started_at      TIMESTAMP NOT NULL DEFAULT now(),
    finished_at     TIMESTAMP,
    total_leads     INT NOT NULL,
    completed_leads INT NOT NULL DEFAULT 0,
    failed_leads    INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS execution_leads (
    execution_id  INT NOT NULL REFERENCES executions(id),
    lead_id       INT NOT NULL REFERENCES leads(id),
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts      INT NOT NULL DEFAULT 0,
    output        JSONB,
    error         TEXT,
    cost          NUMERIC(10,6),
    latency_ms    INT,
    updated_at    TIMESTAMP DEFAULT now(),
    PRIMARY KEY (execution_id, lead_id)
);
