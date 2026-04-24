import json

from sqlalchemy import text

from src.infrastructure.db.connection import SessionLocal


class PGExecutionRepository:
    async def create_execution_with_leads(self, campaign_id: int, lead_ids: list[int]) -> int:
        async with SessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        "INSERT INTO executions (campaign_id, status, started_at, total_leads)"
                        " VALUES (:campaign_id, 'running', now(), :total) RETURNING id"
                    ),
                    {"campaign_id": campaign_id, "total": len(lead_ids)},
                )
                execution_id: int = result.scalar_one()

                await session.execute(
                    text(
                        "INSERT INTO execution_leads (execution_id, lead_id, status)"
                        " VALUES (:execution_id, :lead_id, 'pending')"
                    ),
                    [{"execution_id": execution_id, "lead_id": lid} for lid in lead_ids],
                )

            return execution_id

    async def update_execution_lead(
        self,
        execution_id: int,
        lead_id: int,
        status: str,
        output: dict | None,
        error: str | None,
        cost: float | None,
        latency_ms: int | None,
    ) -> None:
        output_json = json.dumps(output) if output is not None else None
        async with SessionLocal() as session:
            await session.execute(
                text(
                    "UPDATE execution_leads"
                    " SET status = :status,"
                    "     output = :output::jsonb,"
                    "     error = :error,"
                    "     cost = :cost,"
                    "     latency_ms = :latency_ms,"
                    "     attempts = attempts + 1,"
                    "     updated_at = now()"
                    " WHERE execution_id = :execution_id AND lead_id = :lead_id"
                ),
                {
                    "status": status,
                    "output": output_json,
                    "error": error,
                    "cost": cost,
                    "latency_ms": latency_ms,
                    "execution_id": execution_id,
                    "lead_id": lead_id,
                },
            )
            await session.commit()

    async def finalize_execution(
        self,
        execution_id: int,
        status: str,
        completed: int,
        failed: int,
    ) -> None:
        async with SessionLocal() as session:
            await session.execute(
                text(
                    "UPDATE executions"
                    " SET status = :status,"
                    "     finished_at = now(),"
                    "     completed_leads = :completed,"
                    "     failed_leads = :failed"
                    " WHERE id = :execution_id"
                ),
                {
                    "status": status,
                    "completed": completed,
                    "failed": failed,
                    "execution_id": execution_id,
                },
            )
            await session.commit()
