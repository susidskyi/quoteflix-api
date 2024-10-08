import json
import uuid
from typing import Callable
from unittest import mock

import pytest
import pytest_mock
from fastapi import FastAPI, UploadFile, status
from httpx import AsyncClient

from app.api.movies.dependencies import movie_exists
from app.api.phrases.dependencies import get_scenes_upload_service, phrase_exists, phrase_issue_exists
from app.api.phrases.models import PhraseIssueModel, PhraseModel
from app.api.phrases.schemas import (
    PaginatedPhrasesBySearchTextSchema,
    PhraseCreateSchema,
    PhraseIssueCreateSchema,
    PhraseIssueSchema,
    PhraseSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.api.users.models import UserModel
from app.api.users.permissions import current_superuser


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("phrases:get-all-phrases"),
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert json.dumps(result_data[0], sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"),
            sort_keys=True,
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_all.assert_awaited_once()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for("phrases:get-all-phrases"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json=phrase_create_schema_data.model_dump(mode="json"),
        )
        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"),
            sort_keys=True,
        )
        assert result.status_code == status.HTTP_201_CREATED
        mock_phrases_service.create.assert_awaited_once_with(phrase_create_schema_data)

    async def test_create_bad_request(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json={"invalid": "value"},
        )

        assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_phrases_service.create.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for("phrases:create-phrase"),
            json=phrase_create_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(True)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase",
                phrase_id=phrase_model_data.id,
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase",
                phrase_id=phrase_model_data.id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.delete.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(True)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase",
                phrase_id=phrase_model_data.id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(True)

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase",
                phrase_id=phrase_model_data.id,
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"),
            sort_keys=True,
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.update.assert_awaited_once_with(
            phrase_model_data.id,
            phrase_update_schema_data,
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase",
                phrase_id=phrase_model_data.id,
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.update.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(True)

        result = await async_client.put(
            app_with_dependency_overrides.url_path_for(
                "phrases:update-phrase",
                phrase_id=phrase_model_data.id,
            ),
            json=phrase_update_schema_data.model_dump(mode="json"),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(True)

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrase-by-id",
                phrase_id=phrase_model_data.id,
            ),
        )

        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"),
            sort_keys=True,
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
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrase-by-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.get_by_id.assert_not_awaited()


@pytest.mark.asyncio()
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        result_data = result.json()

        assert len(result_data) == 1
        assert json.dumps(result_data[0], sort_keys=True) == json.dumps(
            phrase_schema_data.model_dump(mode="json"),
            sort_keys=True,
        )
        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id,
        )

    async def test_get_by_movie_id_not_found(
        self,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.get_by_movie_id.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestGetPhrasesBySearchText:
    async def test_get_by_search_text(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        paginated_phrases_by_search_text_schema_data: PaginatedPhrasesBySearchTextSchema,
    ):
        mock_phrases_service.get_by_search_text.return_value = paginated_phrases_by_search_text_schema_data

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-search-text",
            ),
            params={"search_text": phrase_model_data.full_text, "page": 1},
        )

        result_data = result.json()

        assert result_data == paginated_phrases_by_search_text_schema_data.model_dump(mode="json")

        assert result.status_code == status.HTTP_200_OK
        mock_phrases_service.get_by_search_text.assert_awaited_once_with(
            phrase_model_data.full_text,
            1,
        )

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_200_OK),
            ("common_user", status.HTTP_200_OK),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        user: str,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        phrase_model_data: PhraseModel,
        expected_status_code: int,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-by-search-text",
            ),
            params={"search_text": phrase_model_data.full_text, "page": 1},
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestDeletePhrasesByMovieId:
    async def test_delete_by_movie_id(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_phrases_service.delete_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id,
        )

    async def test_delete_by_movie_id_not_found(
        self,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrases-by-movie-id",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.delete_by_movie_id.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
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
        check_movie_exists: Callable[[bool], None],
        check_is_superuser: Callable[[UserModel | None], UserModel],
        user: str,
        expected_status_code: int,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrases-by-movie-id",
                movie_id=phrase_model_data.movie_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestCreatePhrasesFromMovieFiles:
    async def test_create_phrases_from_movie_files(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        random_movie_id: uuid.UUID,
        check_movie_exists: Callable[[bool], None],
        mock_scenes_upload_service: mock.AsyncMock,
        movie_file: UploadFile,
        subtitles_file: UploadFile,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)
        app_with_dependency_overrides.dependency_overrides[get_scenes_upload_service] = (
            lambda: mock_scenes_upload_service
        )

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrases-from-movie-files",
                movie_id=random_movie_id,
            ),
            files={
                "movie_file": ("movie.mp4", movie_file.file, "video/mp4"),
                "subtitles_file": ("subtitles.srt", subtitles_file.file, "text/plain"),
            },
        )

        upload_and_process_files_kwargs = mock_scenes_upload_service.upload_and_process_files.await_args_list[0].kwargs

        assert result.status_code == status.HTTP_202_ACCEPTED
        assert upload_and_process_files_kwargs["movie_id"] == random_movie_id
        assert upload_and_process_files_kwargs["movie_file"].filename == movie_file.filename
        assert upload_and_process_files_kwargs["subtitles_file"].filename == subtitles_file.filename
        assert upload_and_process_files_kwargs["start_in_movie_shift"] == 0
        assert upload_and_process_files_kwargs["end_in_movie_shift"] == 0

    async def test_create_phrases_from_movie_files_with_time_shifts(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        random_movie_id: uuid.UUID,
        check_movie_exists: Callable[[bool], None],
        mock_scenes_upload_service: mock.AsyncMock,
        movie_file: UploadFile,
        subtitles_file: UploadFile,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)
        app_with_dependency_overrides.dependency_overrides[get_scenes_upload_service] = (
            lambda: mock_scenes_upload_service
        )

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrases-from-movie-files",
                movie_id=random_movie_id,
            ),
            data={
                "start_in_movie_shift": 1,
                "end_in_movie_shift": 1,
            },
            files={
                "movie_file": ("movie.mp4", movie_file.file, "video/mp4"),
                "subtitles_file": ("subtitles.srt", subtitles_file.file, "text/plain"),
            },
        )

        upload_and_process_files_kwargs = mock_scenes_upload_service.upload_and_process_files.await_args_list[0].kwargs

        assert result.status_code == status.HTTP_202_ACCEPTED
        assert upload_and_process_files_kwargs["movie_id"] == random_movie_id
        assert upload_and_process_files_kwargs["movie_file"].filename == movie_file.filename
        assert upload_and_process_files_kwargs["subtitles_file"].filename == subtitles_file.filename
        assert upload_and_process_files_kwargs["start_in_movie_shift"] == 1
        assert upload_and_process_files_kwargs["end_in_movie_shift"] == 1

    async def test_create_phrases_from_movie_files_not_found(
        self,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        check_movie_exists: Callable[[bool], None],
        movie_file: UploadFile,
        subtitles_file: UploadFile,
        mock_scenes_upload_service: mock.AsyncMock,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)
        app_with_dependency_overrides.dependency_overrides[get_scenes_upload_service] = (
            lambda: mock_scenes_upload_service
        )

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrases-from-movie-files",
                movie_id=random_movie_id,
            ),
            files={
                "movie_file": ("movie.mp4", movie_file.file, "video/mp4"),
                "subtitles_file": ("subtitles.srt", subtitles_file.file, "text/plain"),
            },
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_202_ACCEPTED),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        random_movie_id: uuid.UUID,
        check_movie_exists: Callable[[bool], None],
        check_is_superuser: Callable[[UserModel | None], UserModel],
        user: str,
        expected_status_code: int,
        movie_file: UploadFile,
        subtitles_file: UploadFile,
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value
        )
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrases-from-movie-files",
                movie_id=random_movie_id,
            ),
            files={
                "movie_file": ("movie.mp4", movie_file.file, "video/mp4"),
                "subtitles_file": ("subtitles.srt", subtitles_file.file, "text/plain"),
            },
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestExportPhrasesToJSON:
    async def test_export_phrases_to_json_no_has_issues_provided(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_model_data: PhraseModel,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)
        mock_phrases_service.export_to_json.return_value = [phrase_model_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-phrases-to-json",
                movie_id=random_movie_id,
            ),
        )

        result_data = result.json()
        assert result.status_code == status.HTTP_200_OK
        assert result_data[0].get("id") == str(phrase_model_data.id)
        assert result_data[0].get("full_text") == phrase_model_data.full_text
        assert result_data[0].get("normalized_text") == phrase_model_data.normalized_text
        assert result_data[0].get("scene_s3_key") == phrase_model_data.scene_s3_key

        mock_phrases_service.export_to_json.assert_awaited_once_with(random_movie_id, False)

    @pytest.mark.parametrize("has_issues", [True, False])
    async def test_export_phrases_to_json_have_issues(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_model_data: PhraseModel,
        check_movie_exists: Callable[[bool], None],
        has_issues: bool,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)
        mock_phrases_service.export_to_json.return_value = [phrase_model_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-phrases-to-json",
                movie_id=random_movie_id,
            ),
            params={
                "has_issues": has_issues,
            },
        )

        result_data = result.json()
        assert result.status_code == status.HTTP_200_OK
        assert result_data[0].get("id") == str(phrase_model_data.id)
        assert result_data[0].get("full_text") == phrase_model_data.full_text
        assert result_data[0].get("normalized_text") == phrase_model_data.normalized_text
        assert result_data[0].get("scene_s3_key") == phrase_model_data.scene_s3_key

        mock_phrases_service.export_to_json.assert_awaited_once_with(random_movie_id, has_issues)

    async def test_export_phrases_to_json_movie_not_found(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        check_movie_exists: Callable[[bool], None],
        random_movie_id: uuid.UUID,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-phrases-to-json",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.export_to_json.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        request: pytest.FixtureRequest,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_transfer_schema_data: PhraseTransferSchema,
        user: str,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: True
        mock_phrases_service.export_to_json.return_value = [phrase_transfer_schema_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-phrases-to-json",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestImportPhrasesFromJSON:
    async def test_import_phrases_from_json(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_transfer_schema_data: PhraseTransferSchema,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:import-phrases-from-json",
                movie_id=random_movie_id,
            ),
            json=[phrase_transfer_schema_data.model_dump(mode="json")],
        )

        assert result.status_code == status.HTTP_202_ACCEPTED
        mock_phrases_service.import_from_json.assert_awaited_once_with(random_movie_id, [phrase_transfer_schema_data])

    async def test_import_phrases_from_json_movie_not_found(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_transfer_schema_data: PhraseTransferSchema,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:import-phrases-from-json",
                movie_id=random_movie_id,
            ),
            json=[phrase_transfer_schema_data.model_dump(mode="json")],
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.import_from_json.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_202_ACCEPTED),
        ],
    )
    async def test_permissions(
        self,
        app_with_dependency_overrides: FastAPI,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrase_transfer_schema_data: PhraseTransferSchema,
        check_movie_exists: Callable[[bool], None],
        expected_status_code: int,
        user: str,
        request: pytest.FixtureRequest,
        check_is_superuser: Callable[[UserModel | None], UserModel],
    ):
        user_fixture_value: str | None = request.getfixturevalue(user)

        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(True)

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:import-phrases-from-json",
                movie_id=random_movie_id,
            ),
            json=[phrase_transfer_schema_data.model_dump(mode="json")],
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestDeletePhraseIssue:
    async def test_delete_phrase_issue_ok(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_phrases_service: mock.AsyncMock,
        random_phrase_issue_id: uuid.UUID,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
    ):
        background_tasks_mock = mocker.patch("fastapi.BackgroundTasks.add_task")

        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_issue_exists] = lambda: True

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase-issue",
                issue_id=random_phrase_issue_id,
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        assert result.content == b""
        background_tasks_mock.assert_called_once_with(
            mock_phrases_service.delete_issue,
            random_phrase_issue_id,
        )

    async def test_delete_phrase_issue_does_not_exist(
        self,
        mocker: pytest_mock.MockerFixture,
        check_phrase_issue_exists: Callable[[bool], None],
        random_phrase_issue_id: uuid.UUID,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
    ):
        background_tasks_mock = mocker.patch("fastapi.BackgroundTasks.add_task")

        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_issue_exists] = lambda: check_phrase_issue_exists(
            False,
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase-issue",
                issue_id=random_phrase_issue_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        background_tasks_mock.assert_not_called()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_204_NO_CONTENT),
        ],
    )
    async def test_permissions(
        self,
        random_phrase_issue_id: uuid.UUID,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        request: pytest.FixtureRequest,
        user: str,
        expected_status_code: int,
    ):
        user_fixture_value = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )
        app_with_dependency_overrides.dependency_overrides[phrase_issue_exists] = lambda: True

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-phrase-issue",
                issue_id=random_phrase_issue_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestCreatePhraseIssue:
    async def test_create_phrase_issue_ok(
        self,
        mock_phrases_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        mocker: pytest_mock.MockFixture,
        random_phrase_id: uuid.UUID,
        server_ip: str,
    ):
        mock_background_tasks_app = mocker.patch("fastapi.BackgroundTasks.add_task")
        expected_phrase_issue_data = PhraseIssueCreateSchema(
            issuer_ip=server_ip,
            phrase_id=random_phrase_id,
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: True

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrase-issue",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_202_ACCEPTED

        mock_background_tasks_app.assert_called_once_with(
            mock_phrases_service.create_issue,
            expected_phrase_issue_data,
        )

    async def test_create_phrase_issue_phrase_does_not_exist(
        self,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        mocker: pytest_mock.MockFixture,
        random_phrase_id: uuid.UUID,
        check_phrase_exists: Callable[[bool], None],
    ):
        mock_background_tasks_app = mocker.patch("fastapi.BackgroundTasks.add_task")
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)

        result = await async_client.post(
            app_with_dependency_overrides.url_path_for(
                "phrases:create-phrase-issue",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND

        mock_background_tasks_app.assert_not_called()


@pytest.mark.asyncio()
class TestGetAllPhraseIssues:
    async def test_get_all_issues_ok(
        self,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        phrase_issue_model_read_data: PhraseIssueModel,
        phrase_issue_schema_data: PhraseIssueSchema,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        mock_phrases_service.get_all_issues.return_value = [phrase_issue_model_read_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-issues",
            ),
        )

        assert result.status_code == status.HTTP_200_OK
        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            [phrase_issue_schema_data.model_dump(mode="json")],
            sort_keys=True,
        )
        mock_phrases_service.get_all_issues.assert_awaited_once()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        request: pytest.FixtureRequest,
        user: str,
        expected_status_code: int,
        mock_phrases_service: mock.AsyncMock,
        phrase_issue_model_read_data: PhraseIssueModel,
    ):
        user_fixture_value = request.getfixturevalue(user)
        mock_phrases_service.get_all_issues.return_value = [phrase_issue_model_read_data]
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-phrases-issues",
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestGetIssuesByPhraseId:
    async def test_get_all_issues_ok(
        self,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        phrase_issue_model_read_data: PhraseIssueModel,
        phrase_issue_schema_data: PhraseIssueSchema,
        random_phrase_id: uuid.UUID,
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: True
        mock_phrases_service.get_issues_by_phrase_id.return_value = [phrase_issue_model_read_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_200_OK
        result_data = result.json()

        assert json.dumps(result_data, sort_keys=True) == json.dumps(
            [phrase_issue_schema_data.model_dump(mode="json")],
            sort_keys=True,
        )
        mock_phrases_service.get_issues_by_phrase_id.assert_awaited_once_with(random_phrase_id)

    async def test_get_all_issues_phrase_does_not_exist(
        self,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        phrase_issue_model_read_data: PhraseIssueModel,
        random_phrase_id: uuid.UUID,
        check_phrase_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)
        mock_phrases_service.get_issues_by_phrase_id.return_value = [phrase_issue_model_read_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.get_issues_by_phrase_id.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        request: pytest.FixtureRequest,
        user: str,
        expected_status_code: int,
        mock_phrases_service: mock.AsyncMock,
        phrase_issue_model_read_data: PhraseIssueModel,
        random_phrase_id: uuid.UUID,
    ):
        user_fixture_value = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: True
        mock_phrases_service.get_issues_by_phrase_id.return_value = [phrase_issue_model_read_data]

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:get-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestDeleteIssuesByPhraseID:
    async def test_delete_issues_by_phrase_id_ok(
        self,
        mock_phrases_service: mock.AsyncMock,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        random_phrase_id: uuid.UUID,
        mocker: pytest_mock.MockerFixture,
    ):
        background_tasks_add_task_mock = mocker.patch("fastapi.BackgroundTasks.add_task")
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: True

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_204_NO_CONTENT
        background_tasks_add_task_mock.assert_called_once_with(
            mock_phrases_service.delete_issues_by_phrase_id,
            random_phrase_id,
        )

    async def test_delete_issues_by_phrase_id_phrase_does_not_exist(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        random_phrase_id: uuid.UUID,
        mocker: pytest_mock.MockerFixture,
        check_phrase_exists: Callable[[bool], None],
    ):
        background_tasks_add_task_mock = mocker.patch("fastapi.BackgroundTasks.add_task")
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True
        app_with_dependency_overrides.dependency_overrides[phrase_exists] = lambda: check_phrase_exists(False)

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        background_tasks_add_task_mock.assert_not_called()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_204_NO_CONTENT),
        ],
    )
    async def test_permissions(
        self,
        async_client: AsyncClient,
        app_with_dependency_overrides: FastAPI,
        check_is_superuser: Callable[[UserModel | None], UserModel],
        request: pytest.FixtureRequest,
        user: str,
        expected_status_code: int,
        random_phrase_id: uuid.UUID,
    ):
        user_fixture_value = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture_value,
        )

        result = await async_client.delete(
            app_with_dependency_overrides.url_path_for(
                "phrases:delete-issues-by-phrase-id",
                phrase_id=random_phrase_id,
            ),
        )

        assert result.status_code == expected_status_code


@pytest.mark.asyncio()
class TestExportToSrt:
    async def test_ok(
        self,
        mock_phrases_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrases_srt_file_content: str,
    ):
        mock_phrases_service.generate_srt.return_value = phrases_srt_file_content
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: True

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-to-srt",
                movie_id=random_movie_id,
            ),
        )

        mock_phrases_service.generate_srt.assert_awaited_once_with(random_movie_id)
        assert result.status_code == status.HTTP_200_OK
        assert result.content == phrases_srt_file_content.encode()

    async def test_movie_does_not_exist(
        self,
        mock_phrases_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        check_movie_exists: Callable[[bool], None],
    ):
        app_with_dependency_overrides.dependency_overrides[movie_exists] = lambda: check_movie_exists(False)

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-to-srt",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == status.HTTP_404_NOT_FOUND
        mock_phrases_service.generate_srt.assert_not_awaited()

    @pytest.mark.parametrize(
        ("user", "expected_status_code"),
        [
            ("anonymous_user", status.HTTP_401_UNAUTHORIZED),
            ("common_user", status.HTTP_403_FORBIDDEN),
            ("admin_user", status.HTTP_200_OK),
        ],
    )
    async def test_permissions(
        self,
        mock_phrases_service: mock.AsyncMock,
        app_with_dependency_overrides: FastAPI,
        async_client: AsyncClient,
        random_movie_id: uuid.UUID,
        phrases_srt_file_content: str,
        request: pytest.FixtureRequest,
        user: str,
        expected_status_code: int,
        check_is_superuser: Callable[[UserModel | None], UserModel],
    ):
        user_fixture = request.getfixturevalue(user)
        app_with_dependency_overrides.dependency_overrides[current_superuser] = lambda: check_is_superuser(
            user_fixture,
        )
        mock_phrases_service.generate_srt.return_value = phrases_srt_file_content

        result = await async_client.get(
            app_with_dependency_overrides.url_path_for(
                "phrases:export-to-srt",
                movie_id=random_movie_id,
            ),
        )

        assert result.status_code == expected_status_code
