import json
from typing import List, Optional

from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import ARRAY, TEXT, JSONB

from src.infrastructure.db.connection import SessionLocal


class PGCampaignRepository:
    async def filter_lead_ids(
        self, industry: str, tags: Optional[List[str]]
    ) -> List[int]:
        async with SessionLocal() as session:
            query = text("""
                SELECT id FROM leads
                WHERE industry = :industry
                AND (:tags IS NULL OR tags && :tags)
            """).bindparams(
                bindparam("tags", type_=ARRAY(TEXT))
            )

            result = await session.execute(
                query,
                {
                    "industry": industry,
                    "tags": tags if tags else None,
                },
            )

            rows = result.fetchall()
            return [row[0] for row in rows]

    async def create_campaign(self, filters: dict, lead_ids: List[int]) -> int:
        async with SessionLocal() as session:
            async with session.begin():
                insert_campaign_query = text("""
                    INSERT INTO campaigns (filters, created_at)
                    VALUES (:filters_json, now())
                    RETURNING id
                """).bindparams(
                    bindparam("filters_json", type_=JSONB)
                )

                result = await session.execute(
                    insert_campaign_query,
                    {"filters_json": filters},
                )

                campaign_id: int = result.scalar_one()

                insert_links_query = text("""
                    INSERT INTO campaign_leads (campaign_id, lead_id)
                    VALUES (:campaign_id, :lead_id)
                """)

                await session.execute(
                    insert_links_query,
                    [
                        {"campaign_id": campaign_id, "lead_id": lid}
                        for lid in lead_ids
                    ],
                )

            return campaign_id

    async def get_campaign_lead_ids(self, campaign_id: int) -> List[int]:
        async with SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT lead_id FROM campaign_leads
                    WHERE campaign_id = :campaign_id
                """),
                {"campaign_id": campaign_id},
            )

            rows = result.fetchall()
            return [row[0] for row in rows]

    async def campaign_exists(self, campaign_id: int) -> bool:
        async with SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT EXISTS(
                        SELECT 1 FROM campaigns WHERE id = :campaign_id
                    )
                """),
                {"campaign_id": campaign_id},
            )

            return result.scalar_one()