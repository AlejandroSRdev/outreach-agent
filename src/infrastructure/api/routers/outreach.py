from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.domain.models.lead import LeadInput
from src.application.services.orchestrator import BatchOrchestrator
from src.infrastructure.api.app import get_orchestrator


class BatchRequest(BaseModel):
    leads: list[LeadInput] = Field(min_length=1, max_length=20)


class LeadResult(BaseModel):
    lead: str
    status: Literal["success", "failed"]
    result: dict | None = None
    error: str | None = None


class BatchResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[LeadResult]


router = APIRouter(tags=["outreach"])


@router.post("/batch", response_model=BatchResponse)
async def batch_outreach(
    body: BatchRequest,
    orchestrator: BatchOrchestrator = Depends(get_orchestrator),
) -> BatchResponse:
    raw = await orchestrator.run_batch(body.leads)
    results = [LeadResult(**r) for r in raw]
    succeeded = sum(1 for r in results if r.status == "success")
    failed = len(results) - succeeded
    return BatchResponse(
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )
