from fastapi import APIRouter
from pydantic import BaseModel

from src.infrastructure.db.leads import get_all_leads


class LeadSummary(BaseModel):
    id: int
    name: str
    company: str
    role: str
    industry: str | None
    tags: list[str] | None


router = APIRouter(tags=["leads"])


@router.get("/leads", response_model=list[LeadSummary])
async def list_leads() -> list[LeadSummary]:
    return await get_all_leads()
