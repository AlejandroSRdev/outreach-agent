from typing import Protocol
from src.domain.models.lead import LeadInput, EnrichedLead
from src.domain.models.email import DraftEmail, GeneratedEmail


class ResearchProvider(Protocol):
    async def enrich(self, lead: LeadInput) -> EnrichedLead: ...


class AIClient(Protocol):
    async def generate(self, enriched: EnrichedLead, hint: str | None = None) -> DraftEmail: ...
    async def refine(self, draft: DraftEmail, hint: str | None = None) -> GeneratedEmail: ...
