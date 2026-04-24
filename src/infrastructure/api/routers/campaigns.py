from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.application.use_cases.create_campaign import (
    CreateCampaignUseCase,
    InvalidFilterError,
    EmptyCampaignError,
)

router = APIRouter()


class CampaignRequest(BaseModel):
    industry: str
    tags: list[str] | None = None


class CampaignResponse(BaseModel):
    campaign_id: int
    total_leads: int


def get_create_campaign_use_case(request: Request) -> CreateCampaignUseCase:
    return request.app.state.create_campaign_use_case


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    body: CampaignRequest,
    use_case: CreateCampaignUseCase = Depends(get_create_campaign_use_case),
) -> CampaignResponse:
    try:
        campaign_id, total_leads = await use_case.execute(body.industry, body.tags)
        return CampaignResponse(campaign_id=campaign_id, total_leads=total_leads)
    except InvalidFilterError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except EmptyCampaignError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
