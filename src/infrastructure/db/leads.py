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
]

_SELECT = ", ".join(_COLUMNS)

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
