import uuid
from unittest import mock

import pytest

from app.api.movies.schemas import MovieCreateSchema
from app.api.movies.service import MoviesService


@pytest.mark.asyncio
class TestMoviesService:
    @pytest.fixture
    def service(self, mock_movies_repository: mock.AsyncMock) -> MoviesService:
        return MoviesService(mock_movies_repository)

    async def test_create_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        movie_active_without_files_data: MovieCreateSchema,
    ):
        await service.create(movie_active_without_files_data)

        mock_movies_repository.create.assert_awaited_once_with(
            movie_active_without_files_data
        )

    async def test_get_all_movies(
        self, service: MoviesService, mock_movies_repository: mock.AsyncMock
    ):
        await service.get_all()

        mock_movies_repository.get_all.assert_awaited_once()

    async def test_get_movie_by_id(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        await service.get_by_id(random_movie_id)

        mock_movies_repository.get_by_id.assert_awaited_once_with(random_movie_id)

    async def test_update_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
        movie_active_without_files_data: MovieCreateSchema,
    ):
        await service.update(random_movie_id, movie_active_without_files_data)

        mock_movies_repository.update.assert_awaited_once_with(
            random_movie_id, movie_active_without_files_data
        )

    async def test_delete_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        await service.delete(random_movie_id)

        mock_movies_repository.delete.assert_awaited_once_with(random_movie_id)

    async def test_exists(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        await service.exists(random_movie_id)

        mock_movies_repository.exists.assert_awaited_once_with(random_movie_id)
