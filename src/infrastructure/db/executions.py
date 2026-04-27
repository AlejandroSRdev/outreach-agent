import json

from sqlalchemy import text

from src.infrastructure.db.connection import SessionLocal, engine
from src.domain.models.execution import ExecutionLeadResult, ExecutionWithLeads


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
        async with engine.connect() as conn:
            raw = await conn.get_raw_connection()
            await raw.driver_connection.execute(
                "UPDATE execution_leads"
                " SET"
                "     status = $1,"
                "     output = $2::jsonb,"
                "     error = $3,"
                "     cost = $4,"
                "     latency_ms = $5,"
                "     attempts = attempts + 1,"
                "     updated_at = now()"
                " WHERE execution_id = $6 AND lead_id = $7",
                status, output_json, error, cost, latency_ms, execution_id, lead_id,
            )
            await conn.commit()

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

    async def get_execution_with_leads(self, execution_id: int) -> ExecutionWithLeads | None:
        async with SessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT e.id, e.status, e.total_leads, e.completed_leads, e.failed_leads,"
                    "       el.lead_id, el.status AS lead_status, el.output, el.error,"
                    "       l.name, l.company, l.industry"
                    " FROM executions e"
                    " LEFT JOIN execution_leads el ON el.execution_id = e.id"
                    " LEFT JOIN leads l ON l.id = el.lead_id"
                    " WHERE e.id = :execution_id"
                ),
                {"execution_id": execution_id},
            )
            rows = result.mappings().all()

        if not rows:
            return None

        first = rows[0]
        leads = [
            ExecutionLeadResult(
                lead_id=row["lead_id"],
                name=row["name"],
                company=row["company"],
                industry=row["industry"],
                status=row["lead_status"],
                output=row["output"],
                error=row["error"],
            )
            for row in rows
            if row["lead_id"] is not None
        ]

        return ExecutionWithLeads(
            execution_id=first["id"],
            status=first["status"],
            total_leads=first["total_leads"],
            completed_leads=first["completed_leads"],
            failed_leads=first["failed_leads"],
            leads=leads,
        )
