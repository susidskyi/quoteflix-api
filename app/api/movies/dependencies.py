import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.movies.repository import MoviesRepository
from app.api.movies.service import MoviesService
from app.core.s3_service import S3Service


async def get_movies_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MoviesRepository:
    return MoviesRepository(session)


async def get_s3_service() -> S3Service:
    return S3Service()


async def get_movies_service(
    movie_repository: MoviesRepository = Depends(get_movies_repository),
    s3_service: S3Service = Depends(get_s3_service),
) -> MoviesService:
    return MoviesService(movie_repository, s3_service)


async def movie_exists(
    movie_id: uuid.UUID, movies_service: MoviesService = Depends(get_movies_service)
) -> bool:
    if not await movies_service.exists(movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )
