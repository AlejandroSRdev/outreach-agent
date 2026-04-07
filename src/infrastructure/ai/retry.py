import asyncio
from typing import Callable, Awaitable, TypeVar

import pydantic

T = TypeVar("T")

CORRECTION_HINT = (
    "IMPORTANT: Your previous output failed validation. "
    "Ensure strict JSON format, no extra fields, and correct structure."
)

_RETRYABLE_SUBSTRINGS = (
    "invalid JSON",
    "cannot be empty",
    "too short",
    "too long",
    "Unexpected fields",
    "placeholder content",
    "at least",
    "at most",
)


def is_llm_error(error: Exception) -> bool:
    if isinstance(error, pydantic.ValidationError):
        return True
    msg = str(error)
    return any(s in msg for s in _RETRYABLE_SUBSTRINGS)


async def with_retry(
    fn: Callable[[int], Awaitable[T]],
    max_retries: int = 2,
    delay: float = 0.5,
    should_retry: Callable[[Exception], bool] = is_llm_error,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> T:
    for attempt in range(max_retries + 1):
        try:
            return await fn(attempt)
        except Exception as err:
            if attempt == max_retries or not should_retry(err):
                raise
            if on_retry:
                on_retry(err, attempt + 1)
            await asyncio.sleep(delay)
