import json
import uuid
from typing import Callable
from unittest import mock

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.api.movies.dependencies import movie_exists
from app.api.movies.models import MovieModel
from app.api.movies.schemas import MovieCreateSchema, MovieSchema, MovieUpdateSchema
from app.api.users.models import UserModel
from app.api.users.permissions import current_superuser


@pytest.mark.asyncio
class TestGetAllMoviesRoute:
    async def test_ok(
        self,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        async_client: AsyncClient,
        movie_schema_data: MovieSchema,
    ):
        mock_movies_service.get_all.return_value = [movie_model_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("movies:get-all-movies")
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert json.dumps(result_data[0], sort_keys=True) == json.dumps(
            movie_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result_data[0]["id"] == str(random_movie_id)
        assert result.status_code == status.HTTP_200_OK
        mock_movies_service.get_all.assert_awaited_once()


@pytest.mark.asyncio
class TestCreateMovieRoute:
    async def test_ok(
        self,
        movie_create_schema_data: MovieCreateSchema,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        movie_schema_data: MovieSchema,
        async_client: AsyncClient,
    ):
        mock_movies_service.create.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("movies:create-movie"),
            json=movie_create_schema_data.model_dump(mode="json"),
        )

        result_data = result.json()

        assert result.status_code == status.HTTP_201_CREATED
        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            movie_schema_data.model_dump(mode="json"), sort_keys=True
        )
        mock_movies_service.create.assert_awaited_once_with(movie_create_schema_data)

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
            json={"title": None},
        )

        assert mock_movies_service.create.assert_not_awaited
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
        request: pytest.FixtureRequest,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
        movie_create_schema_data: MovieCreateSchema,
        user: str,
        movie_model_data: MovieModel,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_movies_service.create.return_value = movie_model_data

        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("movies:create-movie"),
            json=movie_create_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestGetMovieByIdRoute:
    async def test_ok(
        self,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        movie_schema_data: MovieSchema,
    ):
        mock_movies_service.get_by_id.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "movies:get-movie-by-id", movie_id=random_movie_id
            )
        )

        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            movie_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_movies_service.get_by_id.assert_awaited_once_with(random_movie_id)

    async def test_movie_not_found(
        self,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        mock_movies_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "movies:get-movie-by-id", movie_id=random_movie_id
            ),
        )

        mock_movies_service.get_by_id.assert_not_awaited()
        assert result.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestUpdateMovieRoute:
    async def test_ok(
        self,
        random_movie_id: uuid.UUID,
        movie_model_data: MovieModel,
        movie_update_schema_data: MovieUpdateSchema,
        mock_movies_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        movie_schema_data: MovieSchema,
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
                "movies:update-movie", movie_id=random_movie_id
            ),
            json=movie_update_schema_data.model_dump(mode="json"),
        )

        result_json = result.json()

        assert json.dumps(result_json, sort_keys=True) == json.dumps(
            movie_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_movies_service.update.assert_awaited_once_with(
            random_movie_id, movie_update_schema_data
        )

    async def test_movie_not_found(
        self,
        random_movie_id: uuid.UUID,
        async_client: AsyncClient,
        movie_create_schema_data: MovieCreateSchema,
        check_movie_exists: Callable[[bool], None],
        app_with_dependency_overrides: FastAPI,
        mock_movies_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "movies:update-movie", movie_id=random_movie_id
            ),
            json=movie_create_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_movies_service.update.assert_not_awaited()

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
        random_movie_id: uuid.UUID,
        async_client: AsyncClient,
        movie_update_schema_data: MovieUpdateSchema,
        check_movie_exists: Callable[[bool], None],
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        mock_movies_service: mock.AsyncMock,
        movie_model_data: MovieModel,
        user: str,
        expected_status_code: int,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_movies_service.update.return_value = movie_model_data
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "movies:update-movie", movie_id=random_movie_id
            ),
            json=movie_update_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestDeleteMovieRoute:
    async def test_ok(
        self,
        random_movie_id: uuid.UUID,
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
                "movies:delete-movie", movie_id=random_movie_id
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_movies_service.delete.assert_awaited_once_with(random_movie_id)

    async def test_movie_not_found(
        self,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        mock_movies_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "movies:delete-movie", movie_id=random_movie_id
            ),
        )
        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_movies_service.delete.assert_not_awaited()

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
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        expected_status_code: int,
        user: str,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )
        mock_movies_service.delete.return_value = None

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "movies:delete-movie", movie_id=random_movie_id
            )
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestUpdateMovieStatusRoute:
    async def test_ok(
        self,
        random_movie_id: uuid.UUID,
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
        mock_movies_service.update_status.return_value = None

        result = await async_client.patch(
            app_with_dependency_overrides.url_path_for(
                "movies:update-status", movie_id=random_movie_id
            ),
            json={"status": "processed"},
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_movies_service.update_status.assert_awaited_once_with(
            random_movie_id, "processed"
        )

    async def test_movie_not_found(
        self,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        mock_movies_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.patch(
            app_with_dependency_overrides.url_path_for(
                "movies:update-status", movie_id=random_movie_id
            ),
            json={"status": "processed"},
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_movies_service.update_status.assert_not_awaited()

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
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        mock_movies_service: mock.AsyncMock,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        expected_status_code: int,
        user: str,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )
        mock_movies_service.update_status.return_value = None

        result = await async_client.patch(
            app_with_dependency_overrides.url_path_for(
                "movies:update-status", movie_id=random_movie_id
            ),
            json={"status": "processed"},
        )

        assert result.status_code == expected_status_code
