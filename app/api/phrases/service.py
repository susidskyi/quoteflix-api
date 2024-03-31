import uuid
from typing import Sequence

from app.api.phrases.models import PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import PhraseCreateSchema, PhraseUpdateSchema


class PhrasesService:
    def __init__(self, repository: PhrasesRepository) -> None:
        self.repository = repository

    async def get_all(self) -> Sequence[PhraseModel]:
        phrases = await self.repository.get_all()

        return phrases

    async def get_by_id(self, phrase_id: uuid.UUID) -> PhraseModel:
        phrase = await self.repository.get_by_id(phrase_id)

        return phrase

    async def delete(self, phrase_id: uuid.UUID) -> None:
        await self.repository.delete(phrase_id)

    async def exists(self, phrase_id: uuid.UUID) -> bool:
        return await self.repository.exists(phrase_id)

    async def create(self, data: PhraseCreateSchema) -> PhraseModel:
        phrase = await self.repository.create(data)

        return phrase

    async def update(
        self, phrase_id: uuid.UUID, data: PhraseUpdateSchema
    ) -> PhraseModel:
        phrase = await self.repository.update(phrase_id, data)

        return phrase

    async def get_by_movie_id(self, movie_id: uuid.UUID) -> Sequence[PhraseModel]:
        return await self.repository.get_by_movie_id(movie_id)

    async def bulk_create(
        self, data: Sequence[PhraseCreateSchema]
    ) -> Sequence[PhraseModel]:
        return await self.repository.bulk_create(data)
