import asyncio
import logging
from typing import Any

from src.domain.models.lead import LeadInput
from src.domain.models.email import GeneratedEmail
from src.application.services.pipeline import OutreachPipeline
from src.infrastructure.delivery.rules import should_deliver
from src.infrastructure.delivery.resend import send_email
from src.config.settings import settings

logger = logging.getLogger(__name__)


class BatchOrchestrator:
    def __init__(self, pipeline: OutreachPipeline, semaphore: asyncio.Semaphore) -> None:
        self.pipeline = pipeline
        self.semaphore = semaphore

    async def _run_one(self, lead: LeadInput) -> GeneratedEmail:
        wait_start = asyncio.get_event_loop().time()
        async with self.semaphore:
            wait_ms = int((asyncio.get_event_loop().time() - wait_start) * 1000)
            logger.info(
                "semaphore_acquired",
                extra={"wait_ms": wait_ms},
            )
            return await self.pipeline.run(lead)

    async def run_campaign_execution(
        self,
        execution_id: int,
        leads: list[LeadInput],
        execution_repo: Any,
    ) -> None:
        import time
        completed = 0
        failed = 0

        async def _run_one_tracked(lead: LeadInput) -> None:
            nonlocal completed, failed
            start = time.monotonic()
            async with self.semaphore:
                try:
                    result, enriched = await self.pipeline.run(lead)
                    latency_ms = int((time.monotonic() - start) * 1000)
                    await execution_repo.update_execution_lead(
                        execution_id=execution_id,
                        lead_id=lead.lead_id,
                        status="completed",
                        output=result.model_dump(),
                        error=None,
                        cost=None,
                        latency_ms=latency_ms,
                    )
                    completed += 1
                    should = should_deliver(
                        mode=settings.mode,
                        lead_id=lead.lead_id,
                        industry=enriched.industry,
                        email=enriched.email,
                    )
                    logger.info(
                        "delivery_decision",
                        extra={
                            "lead_id": lead.lead_id,
                            "email": enriched.email,
                            "industry": enriched.industry,
                            "decision": should,
                        },
                    )
                    if should and settings.resend_key:
                        try:
                            await send_email(
                                resend_key=settings.resend_key,
                                to=enriched.email,
                                subject=result.subject,
                                html=result.body,
                            )
                            logger.info("delivery_sent", extra={"lead_id": lead.lead_id})
                        except Exception as exc:
                            logger.warning("delivery_failed", extra={"lead_id": lead.lead_id, "error": str(exc)})
                    elif should and not settings.resend_key:
                        logger.warning("delivery_skipped_no_key", extra={"lead_id": lead.lead_id})
                except Exception as exc:
                    latency_ms = int((time.monotonic() - start) * 1000)
                    await execution_repo.update_execution_lead(
                        execution_id=execution_id,
                        lead_id=lead.lead_id,
                        status="failed",
                        output=None,
                        error=str(exc),
                        cost=None,
                        latency_ms=latency_ms,
                    )
                    failed += 1

        await asyncio.gather(*[_run_one_tracked(lead) for lead in leads])

        if failed == 0:
            final_status = "completed"
        elif completed == 0:
            final_status = "failed"
        else:
            final_status = "partial"

        await execution_repo.finalize_execution(
            execution_id=execution_id,
            status=final_status,
            completed=completed,
            failed=failed,
        )
