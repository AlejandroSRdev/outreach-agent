from src.domain.ports import ExecutionRepository
from src.domain.models.execution import LastExecutionByIndustry


class GetLastExecutionsByIndustryUseCase:
    def __init__(self, execution_repo: ExecutionRepository) -> None:
        self._execution_repo = execution_repo

    async def execute(self) -> list[LastExecutionByIndustry]:
        return await self._execution_repo.get_last_executions_by_industry()
