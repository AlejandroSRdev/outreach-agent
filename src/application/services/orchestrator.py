import asyncio
import logging
import uuid

from src.domain.models.lead import LeadInput
from src.domain.models.email import GeneratedEmail
from src.application.services.pipeline import OutreachPipeline
from src.infrastructure.logging.context import batch_id_var

logger = logging.getLogger(__name__)


class BatchOrchestrator:
    def __init__(self, pipeline: OutreachPipeline, semaphore: asyncio.Semaphore) -> None:
        self.pipeline = pipeline
        self.semaphore = semaphore

    async def run_batch(self, leads: list[LeadInput]) -> list[dict]:
        batch_id = str(uuid.uuid4())
        batch_id_var.set(batch_id)
        logger.info("batch_start", extra={"lead_count": len(leads)})
        batch_start_time = asyncio.get_event_loop().time()

        coroutines = [self._run_one(lead) for lead in leads]
        raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

        results = []
        for lead, outcome in zip(leads, raw_results):
            if not isinstance(outcome, Exception):
                email, lead_name = outcome
                results.append({"lead": lead_name, "status": "success", "result": email.model_dump()})
            else:
                results.append({"lead": str(lead.lead_id), "status": "failed", "error": str(outcome)})

        succeeded = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - succeeded
        duration_ms = int((asyncio.get_event_loop().time() - batch_start_time) * 1000)
        logger.info(
            "batch_complete",
            extra={
                "total": len(results),
                "succeeded": succeeded,
                "failed": failed,
                "duration_ms": duration_ms,
            },
        )
        return results

    async def _run_one(self, lead: LeadInput) -> GeneratedEmail:
        wait_start = asyncio.get_event_loop().time()
        async with self.semaphore:
            wait_ms = int((asyncio.get_event_loop().time() - wait_start) * 1000)
            logger.info(
                "semaphore_acquired",
                extra={"wait_ms": wait_ms},
            )
            return await self.pipeline.run(lead)
