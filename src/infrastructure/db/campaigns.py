import json

from sqlalchemy import text

from src.infrastructure.db.connection import SessionLocal


class PGCampaignRepository:
    async def filter_lead_ids(self, industry: str, tags: list[str] | None) -> list[int]:
        async with SessionLocal() as session:
            if not tags:
                result = await session.execute(
                    text("SELECT id FROM leads WHERE industry = :industry"),
                    {"industry": industry},
                )
            else:
                result = await session.execute(
                    text(
                        "SELECT id FROM leads WHERE industry = :industry"
                        " AND tags && :tags::text[]"
                    ),
                    {"industry": industry, "tags": tags},
                )
            rows = result.fetchall()
            return [row[0] for row in rows]

    async def create_campaign(self, filters: dict, lead_ids: list[int]) -> int:
        async with SessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        "INSERT INTO campaigns (filters, created_at)"
                        " VALUES (:filters_json::jsonb, now()) RETURNING id"
                    ),
                    {"filters_json": json.dumps(filters)},
                )
                campaign_id: int = result.scalar_one()

                await session.execute(
                    text(
                        "INSERT INTO campaign_leads (campaign_id, lead_id)"
                        " VALUES (:campaign_id, :lead_id)"
                    ),
                    [{"campaign_id": campaign_id, "lead_id": lid} for lid in lead_ids],
                )

            return campaign_id

    async def get_campaign_lead_ids(self, campaign_id: int) -> list[int]:
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT lead_id FROM campaign_leads WHERE campaign_id = :campaign_id"),
                {"campaign_id": campaign_id},
            )
            rows = result.fetchall()
            return [row[0] for row in rows]

    async def campaign_exists(self, campaign_id: int) -> bool:
        async with SessionLocal() as session:
            result = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM campaigns WHERE id = :campaign_id)"),
                {"campaign_id": campaign_id},
            )
            return result.scalar_one()
