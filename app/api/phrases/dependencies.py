import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.service import PhrasesService


async def get_phrases_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PhrasesRepository:
    return PhrasesRepository(session)


async def get_phrases_service(
    phrases_repository: PhrasesRepository = Depends(get_phrases_repository),
) -> PhrasesService:
    return PhrasesService(phrases_repository)


async def phrase_exists(
    phrase_id: uuid.UUID,
    phrases_service: get_phrases_service = Depends(get_phrases_service),
) -> bool:
    if not await phrases_service.exists(phrase_id):
        raise HTTPException(status_code=404, detail="Phrase not found")
