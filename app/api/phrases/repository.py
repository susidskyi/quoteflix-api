import uuid
from typing import Sequence

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, exists, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.phrases.models import PhraseIssueModel, PhraseModel
from app.api.phrases.schemas import (
    PhraseCreateSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.core.config import settings
from app.core.exceptions import RepositoryNotFoundError


class PhrasesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, phrase_id: uuid.UUID) -> PhraseModel:
        async with self.session as session:
            query = select(PhraseModel).where(PhraseModel.id == phrase_id)
            phrase = await session.scalar(query)

            if not phrase:
                raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

            return phrase

    async def delete(self, phrase_id: uuid.UUID) -> str | None:
        if not await self.exists(phrase_id):
            raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

        async with self.session as session:
            query = delete(PhraseModel).where(PhraseModel.id == phrase_id).returning(PhraseModel.scene_s3_key)

            result = await session.scalar(query)
            await session.commit()

            return result

    async def exists(self, phrase_id: uuid.UUID) -> bool:
        async with self.session as session:
            query = select(exists().where(PhraseModel.id == phrase_id))

            result = await session.scalar(query)

            return bool(result)

    async def get_all(self) -> Sequence[PhraseModel]:
        async with self.session as session:
            phrases = await session.scalars(select(PhraseModel))

            return phrases.all()

    async def create(self, data: PhraseCreateSchema) -> PhraseModel:
        async with self.session as session:
            phrase = PhraseModel(**data.model_dump())

            session.add(phrase)
            await session.commit()
            await session.refresh(phrase)

        return phrase

    async def update(
        self,
        phrase_id: uuid.UUID,
        data: PhraseUpdateSchema,
    ) -> PhraseModel:
        async with self.session as session:
            query = select(PhraseModel).where(PhraseModel.id == phrase_id)
            phrase = await session.scalar(query)

            if not phrase:
                raise RepositoryNotFoundError(f"Phrase not found: id={phrase_id}")

            for field, value in data.model_dump().items():
                setattr(phrase, field, value)

            await session.commit()
            await session.refresh(phrase)

        return phrase

    async def get_by_movie_id(self, movie_id: uuid.UUID) -> Sequence[PhraseModel]:
        async with self.session as session:
            query = select(PhraseModel).where(PhraseModel.movie_id == movie_id)
            phrases = await session.scalars(query)

            return phrases.all()

    async def bulk_create(
        self,
        data: Sequence[PhraseCreateSchema],
    ) -> Sequence[PhraseModel]:
        """
        If have time, I will try to optimize this.
        """
        phrases_data = [phrase.model_dump() for phrase in data]

        async with self.session as session:
            result = (
                await session.scalars(
                    insert(PhraseModel).returning(PhraseModel),
                    phrases_data,
                )
            ).all()

            await session.commit()

            for phrase in result:
                await session.refresh(phrase)

            phrases = []

            for phrase_model in result:
                phrase_obj = phrase_model.__dict__
                phrase_obj.pop("_sa_instance_state", None)
                phrases.append(PhraseModel(**phrase_obj))

        return phrases

    async def get_by_search_text(self, search_text: str, page: int = 1) -> Page[PhraseModel]:
        async with self.session as session:
            result: Page[PhraseModel] = await paginate(
                session,
                select(PhraseModel).where(
                    PhraseModel.normalized_text.icontains(search_text),
                ),
                params=Params(page=page, size=settings.phrases_page_size),
            )

            return result

    async def delete_by_movie_id(self, movie_id: uuid.UUID) -> None:
        async with self.session as session:
            query = delete(PhraseModel).where(PhraseModel.movie_id == movie_id)

            await session.execute(query)
            await session.commit()

    async def import_from_json(self, movie_id: uuid.UUID, data: Sequence[PhraseTransferSchema]) -> None:
        phrases_data = [{"movie_id": movie_id, **phrase.model_dump()} for phrase in data]

        async with self.session as session:
            await session.scalars(
                insert(PhraseModel).returning(PhraseModel.id),
                phrases_data,
            )

            await session.commit()

    async def create_issue(self, phrase_id: uuid.UUID, issuer_ip: str) -> None:
        async with self.session as session:
            issue_exists_stmt = select(
                exists().where(PhraseIssueModel.issuer_ip == issuer_ip, PhraseIssueModel.phrase_id == phrase_id),
            )
            issue_exists = await session.scalar(issue_exists_stmt)

            if not issue_exists:
                issue = PhraseIssueModel(
                    phrase_id=phrase_id,
                    issuer_ip=issuer_ip,
                )

                session.add(issue)
                await session.commit()

    async def get_issues_by_phrase_id(self, phrase_id: uuid.UUID) -> Sequence[PhraseIssueModel]:
        async with self.session as session:
            issues_stmt = (
                select(PhraseIssueModel)
                .where(PhraseIssueModel.phrase_id == phrase_id)
                .options(joinedload(PhraseIssueModel.phrase))
            )

            issues = await session.scalars(issues_stmt)

            return issues.all()

    async def get_all_issues(self) -> Sequence[PhraseIssueModel]:
        async with self.session as session:
            issues_stmt = select(PhraseIssueModel).options(joinedload(PhraseIssueModel.phrase))
            issues = await session.scalars(issues_stmt)

            return issues.all()

    async def delete_issue(self, issue_id: uuid.UUID) -> None:
        async with self.session as session:
            stmt = delete(PhraseIssueModel).where(PhraseIssueModel.id == issue_id)

            await session.execute(stmt)
            await session.commit()

    async def delete_issues_by_phrase_id(self, phrase_id: uuid.UUID) -> None:
        async with self.session as session:
            stmt = delete(PhraseIssueModel).where(PhraseIssueModel.phrase_id == phrase_id)

            await session.execute(stmt)
            await session.commit()

    async def issue_exists(self, issue_id: uuid.UUID) -> bool:
        async with self.session as session:
            stmt = select(exists().where(PhraseIssueModel.id == issue_id))

            result = await session.scalar(stmt)

            return bool(result)
