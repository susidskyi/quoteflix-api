import uuid
from typing import Sequence

from sqlalchemy import delete, exists, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.phrases.models import PhraseModel
from app.api.phrases.schemas import PhraseCreateSchema, PhraseUpdateSchema
from app.core.exceptions import RepositoryNotFoundError


class PhrasesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, phrase_id: uuid.UUID) -> PhraseModel:
        query = select(PhraseModel).where(PhraseModel.id == phrase_id)
        phrase = await self.session.scalar(query)

        if not phrase:
            raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

        return phrase

    async def delete(self, phrase_id: uuid.UUID) -> None:
        if not await self.exists(phrase_id):
            raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

        query = delete(PhraseModel).where(PhraseModel.id == phrase_id)

        await self.session.execute(query)
        await self.session.commit()

    async def exists(self, phrase_id: uuid.UUID) -> bool:
        query = select(exists().where(PhraseModel.id == phrase_id))

        return await self.session.scalar(query)

    async def get_all(self) -> Sequence[PhraseModel]:
        phrases = await self.session.scalars(select(PhraseModel))

        return phrases.all()

    async def create(self, data: PhraseCreateSchema) -> PhraseModel:
        phrase = PhraseModel(**data.model_dump())

        self.session.add(phrase)
        await self.session.commit()
        await self.session.refresh(phrase)

        return phrase

    async def update(
        self, phrase_id: uuid.UUID, data: PhraseUpdateSchema
    ) -> PhraseModel:
        query = select(PhraseModel).where(PhraseModel.id == phrase_id)
        phrase = await self.session.scalar(query)

        if not phrase:
            raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

        for field, value in data.model_dump().items():
            setattr(phrase, field, value)

        await self.session.commit()
        await self.session.refresh(phrase)

        return phrase

    async def get_by_movie_id(self, movie_id: uuid.UUID) -> Sequence[PhraseModel]:
        query = select(PhraseModel).where(PhraseModel.movie_id == movie_id)
        phrases = await self.session.scalars(query)

        return phrases.all()

    async def bulk_create(
        self, data: Sequence[PhraseCreateSchema]
    ) -> Sequence[PhraseModel]:
        result = (
            await self.session.scalars(insert(PhraseModel).returning(PhraseModel), data)
        ).all()

        await self.session.commit()

        for phrase in result:
            await self.session.refresh(phrase)

        phrases = []

        for phrase_model in result:
            phrase_obj = phrase_model.__dict__
            phrase_obj.pop("_sa_instance_state", None)
            phrases.append(PhraseModel(**phrase_obj))

        return phrases

    async def get_by_search_text(self, search_text: str) -> Sequence[PhraseModel]:
        query = select(PhraseModel).where(
            PhraseModel.normalized_text.icontains(search_text)
        )

        phrases = await self.session.scalars(query)

        return phrases.all()

    async def delete_by_movie_id(self, movie_id: uuid.UUID) -> None:
        query = delete(PhraseModel).where(PhraseModel.movie_id == movie_id)

        await self.session.execute(query)
        await self.session.commit()
