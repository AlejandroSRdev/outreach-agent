from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.application.use_cases.get_execution import GetExecutionUseCase, ExecutionNotFoundError


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


def get_get_execution_use_case(request: Request) -> GetExecutionUseCase:
    return request.app.state.get_execution_use_case


router = APIRouter()


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
