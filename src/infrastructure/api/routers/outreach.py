from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.application.use_cases.start_execution import (
    StartExecutionUseCase,
    CampaignNotFoundError,
)

router = APIRouter()


class ExecutionRequest(BaseModel):
    campaign_id: int


class ExecutionStartedResponse(BaseModel):
    execution_id: int
    status: str
    total_leads: int


def get_start_execution_use_case(request: Request) -> StartExecutionUseCase:
    return request.app.state.start_execution_use_case


@router.post("/batch", response_model=ExecutionStartedResponse, status_code=202)
async def batch_outreach(
    body: ExecutionRequest,
    use_case: StartExecutionUseCase = Depends(get_start_execution_use_case),
) -> ExecutionStartedResponse:
    try:
        execution_id, total_leads = await use_case.execute(body.campaign_id)
        return ExecutionStartedResponse(
            execution_id=execution_id,
            status="started",
            total_leads=total_leads,
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
