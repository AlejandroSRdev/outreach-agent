from typing import Protocol
from src.domain.models.lead import LeadInput, EnrichedLead
from src.domain.models.email import DraftEmail, GeneratedEmail
from src.domain.models.execution import ExecutionWithLeads


class ResearchProvider(Protocol):
    async def enrich(self, lead: LeadInput) -> EnrichedLead: ...


class AIClient(Protocol):
    async def generate(self, enriched: EnrichedLead, hint: str | None = None) -> DraftEmail: ...
    async def refine(self, draft: DraftEmail, hint: str | None = None) -> GeneratedEmail: ...


class CampaignRepository(Protocol):
    async def filter_lead_ids(self, industry: str, tags: list[str] | None) -> list[int]: ...
    async def create_campaign(self, filters: dict, lead_ids: list[int]) -> int: ...
    async def get_campaign_lead_ids(self, campaign_id: int) -> list[int]: ...
    async def campaign_exists(self, campaign_id: int) -> bool: ...


class ExecutionRepository(Protocol):
    async def create_execution_with_leads(self, campaign_id: int, lead_ids: list[int]) -> int: ...
    async def update_execution_lead(
        self,
        execution_id: int,
        lead_id: int,
        status: str,
        output: dict | None,
        error: str | None,
        cost: float | None,
        latency_ms: int | None,
    ) -> None: ...
    async def finalize_execution(
        self,
        execution_id: int,
        status: str,
        completed: int,
        failed: int,
    ) -> None: ...
    async def get_execution_with_leads(self, execution_id: int) -> ExecutionWithLeads | None: ...
