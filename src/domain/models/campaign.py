from pydantic import BaseModel
from datetime import datetime


class CampaignFilters(BaseModel):
    industry: str
    tags: list[str]


class Campaign(BaseModel):
    id: int
    filters: CampaignFilters
    created_at: datetime
