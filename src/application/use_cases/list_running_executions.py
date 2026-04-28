from src.domain.ports import ExecutionRepository
from src.domain.models.execution import RunningExecution


class ListRunningExecutionsUseCase:
    def __init__(self, execution_repo: ExecutionRepository) -> None:
        self._execution_repo = execution_repo

    async def execute(self) -> list[RunningExecution]:
        return await self._execution_repo.list_running_executions()
