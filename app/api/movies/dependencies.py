import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.movies.repository import MoviesRepository
from app.api.movies.service import MovieService


async def get_movie_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MoviesRepository:
    return MoviesRepository(session)


async def get_movie_service(
    movie_repository: MoviesRepository = Depends(get_movie_repository),
) -> MovieService:
    return MovieService(movie_repository)


async def movie_exists(
    movie_id: uuid.UUID, movie_service: MovieService = Depends(get_movie_service)
) -> bool:
    if not await movie_service.exists(movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")
