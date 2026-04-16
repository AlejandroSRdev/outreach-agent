import json
import logging

from openai import AsyncOpenAI

from src.infrastructure.ai.cost import compute_cost

logger = logging.getLogger(__name__)

from src.domain.models.lead import EnrichedLead
from src.domain.models.email import DraftEmail, GeneratedEmail
from src.infrastructure.ai.config import StageConfig
from src.infrastructure.ai.prompts.generation import build_generation_prompt
from src.infrastructure.ai.prompts.refinement import build_refinement_prompt


class OpenAIClient:
    def __init__(
        self,
        client: AsyncOpenAI,
        generation_config: StageConfig,
        refinement_config: StageConfig,
    ) -> None:
        self.client = client
        self.generation_config = generation_config
        self.refinement_config = refinement_config

    async def generate(self, enriched: EnrichedLead, hint: str | None = None) -> DraftEmail:
        prompt = build_generation_prompt(enriched, hint=hint)
        response = await self.client.chat.completions.create(
            model=self.generation_config.model,
            temperature=self.generation_config.temperature,
            max_tokens=self.generation_config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = response.usage
        input_tokens  = usage.prompt_tokens     if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = compute_cost(self.generation_config.model, input_tokens, output_tokens)
        logger.info("llm_call_success", extra={
            "step":          "generation",
            "model":         self.generation_config.model,
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "cost_usd":      round(cost, 8),
        })
        raw = response.choices[0].message.content.strip()
        first_line = raw.split("\n")[0] if "\n" in raw else raw
        if first_line.lower().startswith("subject:"):
            subject = first_line[len("subject:"):].strip()
            body = raw[len(first_line):].strip()
        else:
            subject = ""
            body = raw
        return DraftEmail(subject=subject, body=body)

    async def refine(self, draft: DraftEmail, hint: str | None = None) -> GeneratedEmail:
        prompt = build_refinement_prompt(draft, hint=hint)
        response = await self.client.chat.completions.create(
            model=self.refinement_config.model,
            temperature=self.refinement_config.temperature,
            max_tokens=self.refinement_config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = response.usage
        input_tokens  = usage.prompt_tokens     if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = compute_cost(self.refinement_config.model, input_tokens, output_tokens)
        logger.info("llm_call_success", extra={
            "step":          "refinement",
            "model":         self.refinement_config.model,
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "cost_usd":      round(cost, 8),
        })
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fence if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Remove first line (```json or ```) and last line (```)
            raw = "\n".join(lines[1:-1]).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Refinement returned invalid JSON")
        return GeneratedEmail(subject=data["subject"], body=data["body"])
