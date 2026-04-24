import asyncio

from src.domain.models.lead import LeadInput
from src.domain.ports import CampaignRepository, ExecutionRepository
from src.application.services.orchestrator import BatchOrchestrator


class CampaignNotFoundError(Exception):
    pass


class StartExecutionUseCase:
    def __init__(
        self,
        campaign_repo: CampaignRepository,
        execution_repo: ExecutionRepository,
        orchestrator: BatchOrchestrator,
    ) -> None:
        self._campaign_repo = campaign_repo
        self._execution_repo = execution_repo
        self._orchestrator = orchestrator

    async def execute(self, campaign_id: int) -> tuple[int, int]:
        if not await self._campaign_repo.campaign_exists(campaign_id):
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found.")

        lead_ids = await self._campaign_repo.get_campaign_lead_ids(campaign_id)

        execution_id = await self._execution_repo.create_execution_with_leads(
            campaign_id=campaign_id,
            lead_ids=lead_ids,
        )

        leads = [LeadInput(lead_id=lid) for lid in lead_ids]

        asyncio.create_task(
            self._orchestrator.run_campaign_execution(execution_id, leads, self._execution_repo)
        )

        return execution_id, len(leads)
