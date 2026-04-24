from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class ExecutionStatus(str, Enum):
    running = "running"
    completed = "completed"
    partial = "partial"
    failed = "failed"


class ExecutionLeadStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Execution(BaseModel):
    id: int
    campaign_id: int
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime | None
    total_leads: int
    completed_leads: int
    failed_leads: int
