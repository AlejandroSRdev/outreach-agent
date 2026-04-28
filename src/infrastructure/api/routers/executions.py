from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.application.use_cases.get_execution import GetExecutionUseCase, ExecutionNotFoundError
from src.application.use_cases.list_running_executions import ListRunningExecutionsUseCase
from src.application.use_cases.cleanup_zombie_executions import CleanupZombieExecutionsUseCase
from src.application.use_cases.get_last_executions_by_industry import GetLastExecutionsByIndustryUseCase
from src.domain.models.execution import LastExecutionByIndustry


class ExecutionLeadResponse(BaseModel):
    lead_id: int
    name: str
    email: str | None
    company: str
    industry: str
    status: str
    output: dict | None
    error: str | None


class ExecutionResponse(BaseModel):
    execution_id: int
    status: str
    total_leads: int
    completed_leads: int
    failed_leads: int
    leads: list[ExecutionLeadResponse]


class RunningExecutionResponse(BaseModel):
    id: int
    campaign_id: int
    status: str
    started_at: datetime


class CleanupResponse(BaseModel):
    cleaned_count: int
    execution_ids: list[int]


def get_get_execution_use_case(request: Request) -> GetExecutionUseCase:
    return request.app.state.get_execution_use_case


def get_list_running_executions_use_case(request: Request) -> ListRunningExecutionsUseCase:
    return request.app.state.list_running_executions_use_case


def get_cleanup_zombie_executions_use_case(request: Request) -> CleanupZombieExecutionsUseCase:
    return request.app.state.cleanup_zombie_executions_use_case


def get_get_last_executions_by_industry_use_case(request: Request) -> GetLastExecutionsByIndustryUseCase:
    return request.app.state.get_last_executions_by_industry_use_case


router = APIRouter()


@router.get("/", response_model=list[RunningExecutionResponse], status_code=200)
async def list_executions(
    status: str,
    use_case: ListRunningExecutionsUseCase = Depends(get_list_running_executions_use_case),
) -> list[RunningExecutionResponse]:
    if status != "running":
        raise HTTPException(status_code=422, detail="Only status='running' is supported.")
    results = await use_case.execute()
    return [
        RunningExecutionResponse(
            id=r.id,
            campaign_id=r.campaign_id,
            status=r.status,
            started_at=r.started_at,
        )
        for r in results
    ]


@router.post("/cleanup", response_model=CleanupResponse, status_code=200)
async def cleanup_zombie_executions(
    use_case: CleanupZombieExecutionsUseCase = Depends(get_cleanup_zombie_executions_use_case),
) -> CleanupResponse:
    result = await use_case.execute()
    return CleanupResponse(
        cleaned_count=result.cleaned_count,
        execution_ids=result.execution_ids,
    )


@router.get("/last-by-industry", response_model=list[LastExecutionByIndustry], status_code=200)
async def get_last_executions_by_industry(
    use_case: GetLastExecutionsByIndustryUseCase = Depends(get_get_last_executions_by_industry_use_case),
) -> list[LastExecutionByIndustry]:
    return await use_case.execute()


@router.get("/{execution_id}", response_model=ExecutionResponse, status_code=200)
async def get_execution(
    execution_id: int,
    use_case: GetExecutionUseCase = Depends(get_get_execution_use_case),
) -> ExecutionResponse:
    try:
        result = await use_case.execute(execution_id)
    except ExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ExecutionResponse(
        execution_id=result.execution_id,
        status=result.status,
        total_leads=result.total_leads,
        completed_leads=result.completed_leads,
        failed_leads=result.failed_leads,
        leads=[
            ExecutionLeadResponse(
                lead_id=lead.lead_id,
                name=lead.name,
                email=lead.email,
                company=lead.company,
                industry=lead.industry,
                status=lead.status,
                output=lead.output,
                error=lead.error,
            )
            for lead in result.leads
        ],
    )
