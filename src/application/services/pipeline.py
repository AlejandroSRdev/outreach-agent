import asyncio
import logging
import uuid

from src.domain.models.lead import LeadInput
from src.domain.models.email import GeneratedEmail
from src.domain.ports import ResearchProvider, AIClient
from src.infrastructure.ai.retry import with_retry, is_llm_error, CORRECTION_HINT
from src.infrastructure.logging.context import request_id_var, lead_id_var

logger = logging.getLogger(__name__)


def _build_correction_hint(
    last_error: Exception | None,
    last_result: GeneratedEmail | None,
) -> str:
    if last_error is None:
        return CORRECTION_HINT
    msg = str(last_error)
    if ("too long" in msg or "at most" in msg) and last_result is not None:
        char_count = len(last_result.body.strip())
        return (
            f"CORRECTION: Your previous body had {char_count} characters. "
            f"Maximum is 1500. You MUST reduce the body length."
        )
    if ("too short" in msg or "at least" in msg) and last_result is not None:
        char_count = len(last_result.body.strip())
        return (
            f"CORRECTION: Your previous body had {char_count} characters. "
            f"Minimum is 100. You MUST expand the body."
        )
    return CORRECTION_HINT


class OutreachPipeline:
    def __init__(
        self,
        research: ResearchProvider,
        ai: AIClient,
        research_timeout_s: int = 30,
        generation_timeout_s: int = 30,
        refinement_timeout_s: int = 20,
    ) -> None:
        self.research = research
        self.ai = ai
        self.research_timeout_s = research_timeout_s
        self.generation_timeout_s = generation_timeout_s
        self.refinement_timeout_s = refinement_timeout_s

    async def run(self, lead: LeadInput) -> tuple[GeneratedEmail, str]:
        run_id = str(uuid.uuid4())
        request_id_var.set(run_id)
        lead_id_var.set(lead.lead_id)

        enriched = await asyncio.wait_for(
            self.research.enrich(lead),
            timeout=self.research_timeout_s,
        )
        logger.info("pipeline_start")
        logger.info("pipeline_step_success", extra={"step": "research"})

        last_error: Exception | None = None
        last_result: GeneratedEmail | None = None

        async def _attempt(n: int) -> GeneratedEmail:
            nonlocal last_result
            hint = _build_correction_hint(last_error, last_result) if n > 0 else None
            draft = await asyncio.wait_for(
                self.ai.generate(enriched, hint=hint),
                timeout=self.generation_timeout_s,
            )
            logger.info("pipeline_step_success", extra={"step": "generation", "attempt": n})
            result = await asyncio.wait_for(
                self.ai.refine(draft, hint=hint),
                timeout=self.refinement_timeout_s,
            )
            logger.info("pipeline_step_success", extra={"step": "refinement", "attempt": n})
            last_result = result
            return result

        def _on_retry(err: Exception, n: int) -> None:
            nonlocal last_error
            last_error = err
            logger.warning("llm_retry", extra={"attempt": n, "reason": str(err)})

        result = await with_retry(
            _attempt,
            max_retries=2,
            delay=0.5,
            should_retry=is_llm_error,
            on_retry=_on_retry,
        )

        logger.info("pipeline_complete")
        return result, enriched.name
