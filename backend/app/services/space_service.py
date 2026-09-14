from uuid import UUID

from app.core.errors import SpaceNotFoundError
from app.domain.entities import CreateSpaceCommand, LearningSpace
from app.domain.ports import LearningRepositoryPort


class SpaceService:
    def __init__(self, repository: LearningRepositoryPort):
        self.repository = repository

    async def create(self, command: CreateSpaceCommand) -> LearningSpace:
        return await self.repository.create_space(command)

    async def get_complete(self, space_id: UUID, client_id: str) -> dict:
        result = await self.repository.get_complete_space(space_id, client_id)
        if result is None:
            raise SpaceNotFoundError()
        return result

