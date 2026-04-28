from src.domain.ports import ExecutionRepository
from src.domain.models.execution import CleanupResult
from src.domain.constants import ZOMBIE_EXECUTION_TIMEOUT_MINUTES


class CleanupZombieExecutionsUseCase:
    def __init__(self, execution_repo: ExecutionRepository) -> None:
        self._execution_repo = execution_repo

    async def execute(self) -> CleanupResult:
        return await self._execution_repo.cleanup_zombie_executions(
            timeout_minutes=ZOMBIE_EXECUTION_TIMEOUT_MINUTES
        )
