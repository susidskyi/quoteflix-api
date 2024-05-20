import os
import uuid
from typing import Sequence

from app.api.phrases.models import PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import PhraseCreateSchema, PhraseTransferSchema, PhraseUpdateSchema
from app.api.phrases.utils import normalize_phrase_text
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

    async def get_by_movie_id(self, movie_id: uuid.UUID) -> Sequence[PhraseModel]:
        phrases = await self.repository.get_by_movie_id(movie_id)
        await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")

        return phrases

    async def bulk_create(self, data: Sequence[PhraseCreateSchema]) -> Sequence[PhraseModel]:
        phrases = await self.repository.bulk_create(data)
        await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")
        return phrases

    async def get_by_search_text(self, search_text: str) -> Sequence[PhraseModel]:
        normalized_search_text = normalize_phrase_text(search_text)
        phrases = await self.repository.get_by_search_text(normalized_search_text)
        await self.presigned_url_service.update_s3_urls_for_models(phrases, "scene_s3_key")

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
