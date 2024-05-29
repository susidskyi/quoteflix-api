import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.movies.dependencies import get_movies_service
from app.api.movies.service import MoviesService
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.scenes_upload_service import ScenesUploadService
from app.api.phrases.service import PhrasesService
from app.core.dependencies import get_presigned_url_service, get_s3_service
from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service


async def get_phrases_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PhrasesRepository:
    return PhrasesRepository(session)


async def get_phrases_service(
    phrases_repository: PhrasesRepository = Depends(get_phrases_repository),
    s3_service: S3Service = Depends(get_s3_service),
    presigned_url_service: PresignedURLService = Depends(get_presigned_url_service),
) -> PhrasesService:
    return PhrasesService(
        phrases_repository,
        s3_service=s3_service,
        presigned_url_service=presigned_url_service,
    )


async def get_scenes_upload_service(
    movies_service: MoviesService = Depends(get_movies_service),
    phrases_service: PhrasesService = Depends(get_phrases_service),
    s3_service: S3Service = Depends(get_s3_service),
) -> ScenesUploadService:
    return ScenesUploadService(movies_service, phrases_service, s3_service)


async def phrase_exists(
    phrase_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    if not await phrases_service.exists(phrase_id):
        raise HTTPException(status_code=404, detail="Phrase not found")


async def phrase_issue_exists(
    issue_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    if not await phrases_service.issue_exists(issue_id):
        raise HTTPException(status_code=404, detail="Phrase Issue not found")
