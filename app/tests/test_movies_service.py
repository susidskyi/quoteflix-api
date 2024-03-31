import uuid
from unittest import mock

import pytest

from app.api.movies.models import MovieModel
from app.api.movies.schemas import MovieCreateSchema, MovieUpdateSchema
from app.api.movies.service import MoviesService
from app.core.constants import MovieStatus


@pytest.mark.asyncio
class TestMoviesService:
    @pytest.fixture
    def service(self, mock_movies_repository: mock.AsyncMock) -> MoviesService:
        return MoviesService(mock_movies_repository)

    async def test_create_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        movie_create_schema_data: MovieCreateSchema,
        movie_model_data: MovieModel,
    ):
        mock_movies_repository.create.return_value = movie_model_data
        result = await service.create(movie_create_schema_data)

        assert result == movie_model_data
        mock_movies_repository.create.assert_awaited_once_with(movie_create_schema_data)

    async def test_get_all_movies(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        movie_model_data: MovieModel,
    ):
        mock_movies_repository.get_all.return_value = [movie_model_data]
        result = await service.get_all()

        assert result == [movie_model_data]
        mock_movies_repository.get_all.assert_awaited_once()

    async def test_get_movie_by_id(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
        movie_model_data: MovieModel,
    ):
        mock_movies_repository.get_by_id.return_value = movie_model_data
        result = await service.get_by_id(random_movie_id)

        assert result == movie_model_data
        mock_movies_repository.get_by_id.assert_awaited_once_with(random_movie_id)

    async def test_update_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
        movie_update_schema_data: MovieUpdateSchema,
        movie_model_data: MovieModel,
    ):
        mock_movies_repository.update.return_value = movie_model_data
        result = await service.update(random_movie_id, movie_update_schema_data)

        assert result == movie_model_data
        mock_movies_repository.update.assert_awaited_once_with(
            random_movie_id, movie_update_schema_data
        )

    async def test_delete_movie(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        mock_movies_repository.delete.return_value = None
        result = await service.delete(random_movie_id)

        assert result is None
        mock_movies_repository.delete.assert_awaited_once_with(random_movie_id)

    async def test_exists(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        mock_movies_repository.exists.return_value = True
        result = await service.exists(random_movie_id)

        assert result is True
        mock_movies_repository.exists.assert_awaited_once_with(random_movie_id)

    async def tests_does_not_exist(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        mock_movies_repository.exists.return_value = False
        result = await service.exists(random_movie_id)

        assert result is False
        mock_movies_repository.exists.assert_awaited_once_with(random_movie_id)

    async def test_update_status(
        self,
        service: MoviesService,
        mock_movies_repository: mock.AsyncMock,
        random_movie_id: uuid.UUID,
    ):
        mock_movies_repository.update_status.return_value = None
        result = await service.update_status(random_movie_id, MovieStatus.ERROR)

        assert result is None
        mock_movies_repository.update_status.assert_awaited_once_with(
            random_movie_id, MovieStatus.ERROR
        )
