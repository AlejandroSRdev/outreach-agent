from sqlalchemy import text

from src.infrastructure.db.connection import SessionLocal

_COLUMNS = [
    "name",
    "company",
    "role",
    "industry",
    "product",
    "value_proposition",
    "target_market",
    "recent_activity",
    "strategic_focus",
    "additional_context",
    "description",
    "tags",
]

_SELECT = "name, company, role, industry, product, value_proposition, target_market, recent_activity, strategic_focus, additional_context, description, tags::text[]"

_QUERY = text(
    f"SELECT {_SELECT} FROM leads WHERE id = :lead_id LIMIT 1"
)


async def get_lead_by_id(lead_id: int) -> dict | None:
    async with SessionLocal() as session:
        result = await session.execute(_QUERY, {"lead_id": lead_id})
        row = result.fetchone()

        if row is None:
            return None

        return {col: row[i] for i, col in enumerate(_COLUMNS)}


_ALL_COLUMNS = ["id", "name", "company", "role", "industry", "tags"]
_ALL_SELECT = "id, name, company, role, industry, tags::text[]"
_ALL_QUERY = text(f"SELECT {_ALL_SELECT} FROM leads ORDER BY id")


async def get_all_leads() -> list[dict]:
    async with SessionLocal() as session:
        result = await session.execute(_ALL_QUERY)
        rows = result.fetchall()

        return [{col: row[i] for i, col in enumerate(_ALL_COLUMNS)} for row in rows]
