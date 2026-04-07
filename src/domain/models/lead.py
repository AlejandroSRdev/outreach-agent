from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LeadInput(BaseModel):
    name: str
    company: str
    role: str


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
