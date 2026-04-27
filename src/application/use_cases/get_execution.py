from src.domain.ports import ExecutionRepository
from src.domain.models.execution import ExecutionWithLeads


class ExecutionNotFoundError(Exception):
    pass


class GetExecutionUseCase:
    def __init__(self, execution_repo: ExecutionRepository) -> None:
        self._execution_repo = execution_repo

    async def execute(self, execution_id: int) -> ExecutionWithLeads:
        result = await self._execution_repo.get_execution_with_leads(execution_id)
        if result is None:
            raise ExecutionNotFoundError(f"Execution {execution_id} not found.")
        return result
