import json
from datetime import datetime

from openai import AsyncOpenAI

from src.domain.models.lead import LeadInput, EnrichedLead
from src.infrastructure.ai.config import StageConfig
from src.infrastructure.ai.prompts.research import build_research_prompt


class LLMResearchProvider:
    def __init__(self, client: AsyncOpenAI, config: StageConfig) -> None:
        self.client = client
        self.config = config

    async def enrich(self, lead: LeadInput) -> EnrichedLead:
        prompt = build_research_prompt(lead)
        response = await self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Research returned invalid JSON")
        return EnrichedLead(
            name=lead.name,
            company=lead.company,
            role=lead.role,  # role comes from input, not inferred
            industry=data.get("industry"),
            description=data.get("description"),
            product=data.get("product"),
            value_proposition=data.get("value_proposition"),
            target_market=data.get("target_market"),
            recent_activity=data.get("recent_activity"),
            strategic_focus=data.get("strategic_focus"),
            additional_context=data.get("additional_context"),
            assembled_at=datetime.utcnow(),
        )
