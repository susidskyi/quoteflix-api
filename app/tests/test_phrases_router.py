import json
import uuid
from typing import Callable
from unittest import mock

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.api.movies.dependencies import movie_exists
from app.api.phrases.dependencies import phrase_exists
from app.api.phrases.models import PhraseModel
from app.api.phrases.schemas import PhraseCreateSchema, PhraseSchema, PhraseUpdateSchema
from app.api.users.models import UserModel
from app.api.users.permissions import current_superuser


@pytest.mark.asyncio
class TestGetAllPhrases:
    async def test_get_all(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_schema_data: PhraseSchema,
    ):
        mock_phrases_service.get_all.return_value = [phrase_model_data]
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("phrases:get-all-phrases")
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert json.dumps(result_data[0], sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_all.assert_awaited_once()

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        user: str,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        phrase_model_data: PhraseModel,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_phrases_service.get_all.return_value = [phrase_model_data]
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("phrases:get-all-phrases")
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestCreatePhrase:
    async def test_create(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_schema_data: PhraseSchema,
        phrase_create_schema_data: PhraseCreateSchema,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_service.create.return_value = phrase_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json=phrase_create_schema_data.model_dump(mode="json"),
        )
        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_201_CREATED
        mock_phrases_service.create.assert_awaited_once_with(phrase_create_schema_data)

    async def test_create_bad_request(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json={"invalid": "value"},
        )

        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_phrases_service.create.assert_not_awaited()

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_201_CREATED),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_create_schema_data: PhraseCreateSchema,
        phrase_model_data: PhraseModel,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        user: str,
        expected_status_code: int,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_phrases_service.create.return_value = phrase_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json=phrase_create_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestDeletePhrase:
    async def test_delete(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
    ):
        mock_phrases_service.delete.return_value = None
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(True)
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase", phrase_id=phrase_model_data.id
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_phrases_service.delete.assert_awaited_once_with(phrase_model_data.id)

    async def test_delete_not_found(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(False)
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase", phrase_id=phrase_model_data.id
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.delete.assert_not_awaited()

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_204_NO_CONTENT),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
        check_is_superuser: Callable[[UserModel | None], UserModel],
        user: str,
        expected_status_code: int,
    ):
        mock_phrases_service.delete.return_value = None
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(True)
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase", phrase_id=phrase_model_data.id
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestUpdatePhrase:
    async def test_update(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
        phrase_schema_data: PhraseSchema,
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        mock_phrases_service.update.return_value = phrase_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(True)
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase", phrase_id=phrase_model_data.id
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.update.assert_awaited_once_with(
            phrase_model_data.id, phrase_update_schema_data
        )

    async def test_update_not_found(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(False)
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase", phrase_id=phrase_model_data.id
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.update.assert_not_awaited()

    @pytest.mark.parametrize(
        "user,expected_status_code",
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_phrase_exists: Callable[[bool], None],
        check_is_superuser: Callable[[UserModel | None], UserModel],
        user: str,
        expected_status_code: int,
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_phrases_service.update.return_value = phrase_model_data
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(True)
        )

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase", phrase_id=phrase_model_data.id
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio
class TestGetPhraseById:
    async def test_get_by_id(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_schema_data: PhraseSchema,
        check_phrase_exists: Callable[[bool], None],
    ):
        mock_phrases_service.get_by_id.return_value = phrase_model_data
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(True)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrase-by-id", phrase_id=phrase_model_data.id
            ),
        )

        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_by_id.assert_awaited_once_with(phrase_model_data.id)

    async def test_get_by_id_not_found(
        self,
        async_client: AsyncClient,
        random_phrase_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        check_phrase_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = (
            lambda: check_phrase_exists(False)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrase-by-id", phrase_id=random_phrase_id
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
class TestGetAllPhrasesByMovieId:
    async def test_get_by_movie_id(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_schema_data: PhraseSchema,
        check_movie_exists: Callable[[bool], None],
    ):
        mock_phrases_service.get_by_movie_id.return_value = [phrase_model_data]
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(True)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert json.dumps(result_data[0], sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"), sort_keys=True
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id
        )

    async def test_get_by_movie_id_not_found(
        self,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = (
            lambda: check_movie_exists(False)
        )
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: True
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.get_by_movie_id.assert_not_awaited()

    @pytest.mark.parametrize(
        "user, expected_status_code",
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        user: str,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        phrase_model_data: PhraseModel,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        mock_phrases_service.get_by_movie_id.return_value = [phrase_model_data]
        app_with_dependency_overrides.dependency_overrides[current_superuser] = (
            lambda: check_is_superuser(user_fixture_value)
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        assert result.status_code == expected_status_code
