import asyncio
import logging
import re
import traceback

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.config.settings import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _mask_database_url(url: str) -> str:
    """Replace credentials in the DSN so they are never logged."""
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


async def verify_database_connection(max_attempts: int = 3, delay_s: float = 2.0) -> None:
    """
    Attempt a minimal SELECT 1 against the database.

    Retries up to `max_attempts` times with `delay_s` seconds between attempts.
    Raises the last exception if all attempts fail, so the caller can decide
    whether to abort startup or continue degraded.
    """
    masked_url = _mask_database_url(settings.database_url)
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Attempting database connection",
            extra={
                "event": "db_connection_attempt",
                "attempt": attempt,
                "max_attempts": max_attempts,
                "database_url": masked_url,
                "environment": settings.environment,
            },
        )
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info(
                "Database connection established",
                extra={
                    "event": "db_connection_success",
                    "attempt": attempt,
                    "database_url": masked_url,
                    "environment": settings.environment,
                },
            )
            return  # success — stop retrying

        except Exception as exc:
            last_exc = exc
            logger.error(
                "Database connection failed",
                extra={
                    "event": "db_connection_failure",
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                    "database_url": masked_url,
                    "environment": settings.environment,
                },
            )
            if attempt < max_attempts:
                await asyncio.sleep(delay_s)

    # All attempts exhausted — propagate so startup can fail fast.
    raise last_exc
