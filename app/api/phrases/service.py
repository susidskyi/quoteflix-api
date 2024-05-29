import os
import uuid
from typing import Sequence

from app.api.phrases.models import PhraseIssueModel, PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import (
    PaginatedPhrasesBySearchTextSchema,
    PhraseBySearchTextSchema,
    PhraseCreateSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.api.phrases.utils import get_matched_phrase, normalize_phrase_text
from app.core.config import settings
from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service


class PhrasesService:
    def __init__(
        self,
        repository: PhrasesRepository,
        s3_service: S3Service,
        presigned_url_service: PresignedURLService,
    ) -> None:
        self.repository = repository
        self.s3_service = s3_service
        self.presigned_url_service = presigned_url_service

    async def get_all(self) -> Sequence[PhraseModel]:
        phrases = await self.repository.get_all()
        await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")

        return phrases

    async def get_by_id(self, phrase_id: uuid.UUID) -> PhraseModel:
        phrase = await self.repository.get_by_id(phrase_id)
        await self.presigned_url_service.update_s3_url_for_model(phrase, "scene_s3_key")

        return phrase

    async def delete(self, phrase_id: uuid.UUID) -> None:
        scene_s3_key = await self.repository.delete(phrase_id)

        if scene_s3_key:
            await self.s3_service.delete_object(scene_s3_key)

    async def exists(self, phrase_id: uuid.UUID) -> bool:
        return await self.repository.exists(phrase_id)

    async def create(self, data: PhraseCreateSchema) -> PhraseModel:
        phrase = await self.repository.create(data)
        await self.presigned_url_service.update_s3_url_for_model(phrase, "scene_s3_key")

        return phrase

    async def update(self, phrase_id: uuid.UUID, data: PhraseUpdateSchema) -> PhraseModel:
        phrase = await self.repository.update(phrase_id, data)
        await self.presigned_url_service.update_s3_url_for_model(phrase, "scene_s3_key")

        return phrase

    async def get_by_movie_id(self, movie_id: uuid.UUID, presign_urls: bool = True) -> Sequence[PhraseModel]:
        phrases = await self.repository.get_by_movie_id(movie_id)

        if presign_urls:
            await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")

        return phrases

    async def bulk_create(self, data: Sequence[PhraseCreateSchema]) -> Sequence[PhraseModel]:
        phrases = await self.repository.bulk_create(data)
        await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")
        return phrases

    async def get_by_search_text(self, search_text: str, page: int) -> PaginatedPhrasesBySearchTextSchema:
        normalized_search_text = normalize_phrase_text(search_text)
        phrases_from_db = await self.repository.get_by_search_text(normalized_search_text, page)

        # TODO: rewrite when match is implemented
        phrases = PaginatedPhrasesBySearchTextSchema(
            items=[
                PhraseBySearchTextSchema(
                    **phrase.__dict__,
                    matched_phrase=get_matched_phrase(phrase.full_text, normalized_search_text),
                )
                for phrase in phrases_from_db.items
            ],
            total=phrases_from_db.total,
            page=phrases_from_db.page,
            size=phrases_from_db.size,
            pages=phrases_from_db.pages,
        )

        await self.presigned_url_service.update_s3_urls_for_models(phrases.items, "scene_s3_key")
        return phrases

    async def delete_by_movie_id(self, movie_id: uuid.UUID) -> None:
        await self.repository.delete_by_movie_id(movie_id)

        movie_s3_path = os.path.join(settings.movies_s3_path, str(movie_id))

        await self.s3_service.delete_folder(movie_s3_path)

    async def export_to_json(self, movie_id: uuid.UUID) -> Sequence[PhraseTransferSchema]:
        phrases = await self.repository.get_by_movie_id(movie_id)

        return [PhraseTransferSchema(**phrase.__dict__) for phrase in phrases]

    async def import_from_json(self, movie_id: uuid.UUID, data: Sequence[PhraseTransferSchema]) -> None:
        await self.repository.import_from_json(movie_id, data)

    async def issue_exists(self, issue_id: uuid.UUID) -> bool:
        return await self.repository.issue_exists(issue_id)

    async def get_all_issues(self) -> Sequence[PhraseIssueModel]:
        return await self.repository.get_all_issues()

    async def delete_issue(self, issue_id: uuid.UUID) -> None:
        await self.repository.delete_issue(issue_id)

    async def create_issue(self, phrase_id: uuid.UUID, issuer_ip: str) -> None:
        await self.repository.create_issue(phrase_id, issuer_ip)

    async def get_issues_by_phrase_id(self, phrase_id: uuid.UUID) -> Sequence[PhraseIssueModel]:
        return await self.repository.get_issues_by_phrase_id(phrase_id)

    async def delete_issues_by_phrase_id(self, phrase_id: uuid.UUID) -> None:
        await self.repository.delete_issues_by_phrase_id(phrase_id)
