from typing import Sequence
import uuid
from app.api.movies.repository import MovieRepository
from app.api.movies.models import MovieModel


class MovieService:
    def __init__(self, movie_repository: MovieRepository) -> None:
        self.repository = movie_repository

    async def create(self, data: MovieModel.Create) -> MovieModel:
        movie = await self.repository.create(data)

        return movie

    async def list(self) -> Sequence[MovieModel]:
        movies = await self.repository.list()

        return movies

    async def update(self, movie_id: uuid.UUID, data: MovieModel.Update) -> MovieModel:
        movie = await self.repository.update(movie_id, data)

        return movie
