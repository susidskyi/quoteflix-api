import os
import uuid
from typing import Sequence

from fastapi import BackgroundTasks

from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieCreateSchema, MovieUpdateSchema
from app.core.config import settings
from app.core.constants import MovieStatus
from app.s3.s3_service import S3Service


class MoviesService:
    def __init__(self, movies_repository: MoviesRepository, s3_service: S3Service) -> None:
        self.repository = movies_repository
        self.s3_service = s3_service

    async def create(self, data: MovieCreateSchema) -> MovieModel:
        return await self.repository.create(data)

    async def get_all(self) -> Sequence[MovieModel]:
        return await self.repository.get_all()

    async def update(self, movie_id: uuid.UUID, data: MovieUpdateSchema) -> MovieModel:
        return await self.repository.update(movie_id, data)

    async def get_by_id(self, movie_id: uuid.UUID) -> MovieModel:
        return await self.repository.get_by_id(movie_id)

    async def delete(self, movie_id: uuid.UUID, background_tasks: BackgroundTasks) -> None:
        await self.repository.delete(movie_id)

        movie_s3_folder_path = os.path.join(settings.movies_s3_path, str(movie_id))
        background_tasks.add_task(self.s3_service.delete_folder, movie_s3_folder_path)

    async def exists(self, movie_id: uuid.UUID) -> bool:
        return await self.repository.exists(movie_id)

    async def update_status(self, movie_id: uuid.UUID, status: MovieStatus) -> None:
        await self.repository.update_status(movie_id, status)
