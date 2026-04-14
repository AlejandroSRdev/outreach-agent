from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LeadInput(BaseModel):
    lead_id: int


class EnrichedLead(BaseModel):
    name: str
    company: str
    role: str

    additional_context: Optional[str]

    industry: Optional[str]
    description: Optional[str]
    product: Optional[str]
    value_proposition: Optional[str]
    target_market: Optional[str]
    recent_activity: Optional[str]
    strategic_focus: Optional[str]

    assembled_at: datetime


class LeadNotFoundError(Exception):
    def __init__(self, lead_id: int) -> None:
        super().__init__(f"Lead not found: id={lead_id}")
        self.lead_id = lead_id
