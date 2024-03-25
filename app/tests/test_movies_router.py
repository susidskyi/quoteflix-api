import datetime
import uuid
from typing import Callable
from unittest import mock

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient

from app.api.movies.dependencies import get_movie_service, movie_exists
from app.api.movies.models import MovieModel
from app.api.movies.schemas import MovieCreateSchema, MovieUpdateSchema
from app.api.users.models import UserModel
from app.api.users.permissions import current_superuser


@pytest.fixture
def movie_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def check_movie_exists() -> Callable[[bool], None]:
    def _raise_exception(exists: bool):
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return _raise_exception


@pytest.fixture
def movie_model_data(
    movie_active_without_files_data: MovieCreateSchema, movie_id: uuid.UUID
) -> MovieModel:
    return MovieModel(
        **{
            **movie_active_without_files_data.model_dump(),
            "id": movie_id,
            "created_at": str(datetime.datetime.now(tz=datetime.timezone.utc)),
            "updated_at": str(datetime.datetime.now(tz=datetime.timezone.utc)),
        }
    )


@pytest.fixture
def app_with_dependency_overrides(
    app: FastAPI,
    mock_movies_service: mock.AsyncMock,
) -> FastAPI:
    app.dependency_overrides = {}
    app.dependency_overrides[get_movie_service] = lambda: mock_movies_service

    return app


@pytest.mark.asyncio
class TestGetAllMoviesRoute:
    async def test_ok(
        self,
        movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        async_client: AsyncClient,
    ):
        mock_movies_service.get_all.return_value = [movie_model_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("movies:get-all-movies")
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert result_data[0]["id"] == str(movie_id)
        assert result.status_code == status.HTTP_200_OK
        mock_movies_service.get_all.assert_awaited_once()


@pytest.mark.asyncio
class TestCreateMovieRoute:
    async def test_ok(
        self,
        movie_id: uuid.UUID,
        movie_active_without_files_data: MovieCreateSchema,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        async_client: AsyncClient,
    ):
        mock_movies_service.create.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("movies:create-movie"),
            data=movie_active_without_files_data.model_dump(mode="json"),
        )

        result_data = result.json()
        assert result.status_code == status.HTTP_201_CREATED
        assert result_data["id"] == str(movie_id)
        mock_movies_service.create.assert_awaited_once_with(
            movie_active_without_files_data
        )

    async def test_bad_request(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("movies:create-movie"),
            data={"title": None},
        )

        assert mock_movies_service.assert_not_awaited
        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("admin_user", status.HTTP_201_CREATED),
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
        ],
    )
    async def test_permissions(
        self,
        request,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
        movie_active_without_files_data: MovieCreateSchema,
        user: str | None,
        movie_model_data: MovieModel,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
    ):
        user = request.getfixturevalue(user)
        mock_movies_service.create.return_value = movie_model_data

        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user)
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("movies:create-movie"),
            data=movie_active_without_files_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestGetMovieByIdRoute:
    async def test_ok(
        self,
        movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
    ):
        mock_movies_service.get_by_id.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "movies:get-movie-by-id", movie_id=movie_id
            )
        )

        result_data = result.json()
        assert result.status_code == status.HTTP_200_OK
        assert result_data["id"] == str(movie_id)
        mock_movies_service.get_by_id.assert_awaited_once_with(movie_id)

    async def test_movie_not_found(
        self,
        movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "movies:get-movie-by-id", movie_id=movie_id
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestUpdateMovieRoute:
    async def test_ok(
        self,
        movie_id: uuid.UUID,
        movie_model_data: MovieModel,
        movie_active_without_files_data: MovieCreateSchema,
        mock_movies_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        mock_movies_service.update.return_value = movie_model_data
        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "movies:update-movie", movie_id=movie_id
            ),
            data=movie_active_without_files_data.model_dump(mode="json"),
        )

        result_json = result.json()

        assert result.status_code == status.HTTP_200_OK
        assert result_json["id"] == str(movie_id)
        mock_movies_service.update.assert_awaited_once_with(
            movie_id, MovieUpdateSchema(**movie_active_without_files_data.model_dump())
        )

    async def test_movie_not_found(
        self,
        movie_id: uuid.UUID,
        async_client: AsyncClient,
        movie_active_without_files_data: MovieCreateSchema,
        check_movie_exists: Callable[[bool], None],
        app_with_dependency_overrides: FastAPI,
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "movies:update-movie", movie_id=movie_id
            ),
            data=movie_active_without_files_data.model_dump(mode="json"),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("admin_user", status.HTTP_200_OK),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        movie_id: uuid.UUID,
        async_client: AsyncClient,
        movie_active_without_files_data: MovieCreateSchema,
        check_movie_exists: Callable[[bool], None],
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        user: str | None,
        expected_status_code: int,
    ):
        user = request.getfixturevalue(user)
        mock_movies_service.update.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user)
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "movies:update-movie", movie_id=movie_id
            ),
            data=movie_active_without_files_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestDeleteMovieRoute:
    async def test_ok(
        self,
        movie_id: uuid.UUID,
        mock_movies_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        mock_movies_service.delete.return_value = None

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "movies:delete-movie", movie_id=movie_id
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_movies_service.delete.assert_awaited_once_with(movie_id)

    async def test_movie_not_found(
        self,
        movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "movies:delete-movie", movie_id=movie_id
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("admin_user", status.HTTP_204_NO_CONTENT),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        expected_status_code: int,
        user: str | None,
    ):
        user = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user)
        )
        mock_movies_service.delete.return_value = None

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "movies:delete-movie", movie_id=movie_id
            )
        )

        assert result.status_code == expected_status_code
