import uuid
from typing import Sequence

from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieCreateSchema, MovieUpdateSchema


class MoviesService:
    def __init__(self, movie_repository: MoviesRepository) -> None:
        self.repository = movie_repository

    async def create(self, data: MovieCreateSchema) -> MovieModel:
        movie = await self.repository.create(data)

        return movie

    async def get_all(self, *args, **kwargs) -> Sequence[MovieModel]:
        movies = await self.repository.get_all()

        return movies

    async def update(self, movie_id: uuid.UUID, data: MovieUpdateSchema) -> MovieModel:
        movie = await self.repository.update(movie_id, data)

        return movie

    async def get_by_id(self, movie_id: uuid.UUID) -> MovieModel:
        movie = await self.repository.get_by_id(movie_id)

        return movie

    async def delete(self, movie_id: uuid.UUID) -> None:
        await self.repository.delete(movie_id)

    async def exists(self, movie_id: uuid.UUID) -> bool:
        return await self.repository.exists(movie_id)
