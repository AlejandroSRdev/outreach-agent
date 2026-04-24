from src.domain.constants import ALLOWED_INDUSTRIES, ALLOWED_TAGS
from src.domain.ports import CampaignRepository


class InvalidFilterError(Exception):
    pass


class EmptyCampaignError(Exception):
    pass


class CreateCampaignUseCase:
    def __init__(self, campaign_repo: CampaignRepository) -> None:
        self._repo = campaign_repo

    async def execute(self, industry: str, tags: list[str] | None) -> tuple[int, list[int]]:
        if industry not in ALLOWED_INDUSTRIES:
            raise InvalidFilterError(f"Invalid industry: {industry}")

        if tags:
            invalid = [t for t in tags if t not in ALLOWED_TAGS]
            if invalid:
                raise InvalidFilterError(f"Invalid tags: {invalid}")

        lead_ids = await self._repo.filter_lead_ids(industry, tags or None)

        if not lead_ids:
            raise EmptyCampaignError("No leads match the given filters.")

        filters_dict = {"industry": industry, "tags": tags or []}
        campaign_id = await self._repo.create_campaign(filters_dict, lead_ids)

        return campaign_id, lead_ids
