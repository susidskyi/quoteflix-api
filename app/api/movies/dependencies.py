from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.movies.repository import MovieRepository
from app.api.dependencies import get_db_session
from app.api.movies.service import MovieService


def get_movie_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MovieRepository:
    return MovieRepository(session)


def get_movie_service(
    movie_repository: MovieRepository = Depends(get_movie_repository),
) -> MovieService:
    return MovieService(movie_repository)
