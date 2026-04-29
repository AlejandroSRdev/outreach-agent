from datetime import datetime

from src.domain.models.lead import LeadInput, EnrichedLead, LeadNotFoundError
from src.infrastructure.db.leads import get_lead_by_id


class DBResearchProvider:
    async def enrich(self, lead: LeadInput) -> EnrichedLead:
        data = await get_lead_by_id(lead.lead_id)
        if data is None:
            raise LeadNotFoundError(lead.lead_id)
        return EnrichedLead(
            name=data["name"],
            company=data["company"],
            role=data["role"],
            industry=data.get("industry"),
            product=data.get("product"),
            value_proposition=data.get("value_proposition"),
            target_market=data.get("target_market"),
            recent_activity=data.get("recent_activity"),
            strategic_focus=data.get("strategic_focus"),
            additional_context=data.get("additional_context"),
            assembled_at=datetime.utcnow(),
            description=data.get("description"),
            email=data.get("email"),
        )
