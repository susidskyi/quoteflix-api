import os
import uuid
from unittest import mock

import pytest
import pytest_mock
from fastapi_pagination import Page

from app.api.phrases.models import PhraseModel
from app.api.phrases.schemas import (
    PaginatedPhrasesBySearchTextSchema,
    PhraseBySearchTextSchema,
    PhraseCreateSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.api.phrases.service import PhrasesService
from app.api.phrases.utils import normalize_phrase_text
from app.core.config import settings


@pytest.mark.asyncio()
class TestPhrasesService:
    async def test_create(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_create_schema_data: PhraseCreateSchema,
        phrase_model_data: PhraseModel,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_phrases_repository.create.return_value = phrase_model_data
        mock_presigned_url_service.update_s3_url_for_model.return_value = phrase_model_data
        phrase = await phrases_service.create(phrase_create_schema_data)

        assert phrase == phrase_model_data
        mock_phrases_repository.create.assert_awaited_once_with(
            phrase_create_schema_data,
        )
        mock_presigned_url_service.update_s3_url_for_model.assert_awaited_once_with(
            phrase_model_data,
            "scene_s3_key",
        )

    async def test_get_by_id(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        mocker: pytest_mock.MockerFixture,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_presigned_url_service.update_s3_url_for_model.return_value = phrase_model_data
        mock_phrases_repository.get_by_id.return_value = phrase_model_data
        phrase = await phrases_service.get_by_id(phrase_model_data.id)

        assert phrase == phrase_model_data
        mock_phrases_repository.get_by_id.assert_awaited_once_with(phrase_model_data.id)
        mock_presigned_url_service.update_s3_url_for_model.assert_awaited_once_with(
            phrase_model_data,
            "scene_s3_key",
        )

    async def test_update(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_update_schema_data: PhraseUpdateSchema,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_phrases_repository.update.return_value = phrase_model_data
        mock_presigned_url_service.update_s3_url_for_model.return_value = phrase_model_data
        phrase = await phrases_service.update(
            phrase_model_data.id,
            phrase_update_schema_data,
        )

        assert phrase == phrase_model_data
        mock_phrases_repository.update.assert_awaited_once_with(
            phrase_model_data.id,
            phrase_update_schema_data,
        )
        mock_presigned_url_service.update_s3_url_for_model.assert_awaited_once_with(
            phrase_model_data,
            "scene_s3_key",
        )

    async def test_delete(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        mock_s3_service: mock.AsyncMock,
    ):
        mock_phrases_repository.delete.return_value = phrase_model_data.scene_s3_key

        result = await phrases_service.delete(phrase_model_data.id)

        assert result is None
        mock_phrases_repository.delete.assert_awaited_once_with(phrase_model_data.id)
        mock_s3_service.delete_object.assert_awaited_once_with(
            phrase_model_data.scene_s3_key,
        )

    async def test_get_all(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_phrases_repository.get_all.return_value = [phrase_model_data]
        mock_presigned_url_service.update_s3_urls_for_models.return_value = [
            phrase_model_data,
        ]

        result = await phrases_service.get_all()

        assert len(result) == 1
        assert phrase_model_data in result
        mock_phrases_repository.get_all.assert_awaited_once()
        mock_presigned_url_service.update_s3_urls_for_models.assert_awaited_once_with(
            [phrase_model_data],
            "scene_s3_key",
        )

    async def test_exists(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.exists.return_value = True

        result = await phrases_service.exists(phrase_model_data.id)

        assert result is True
        mock_phrases_repository.exists.assert_awaited_once_with(phrase_model_data.id)

    async def test_does_not_exist(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.exists.return_value = False

        result = await phrases_service.exists(phrase_model_data.id)

        assert result is False
        mock_phrases_repository.exists.assert_awaited_once_with(phrase_model_data.id)

    async def test_get_by_movie_id(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_phrases_repository.get_by_movie_id.return_value = [phrase_model_data]
        mock_presigned_url_service.update_s3_urls_for_models.return_value = [
            [phrase_model_data],
        ]
        result = await phrases_service.get_by_movie_id(phrase_model_data.movie_id)

        assert len(result) == 1
        assert result[0] == phrase_model_data
        mock_phrases_repository.get_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id,
        )
        mock_presigned_url_service.update_s3_urls_for_models.assert_awaited_once_with(
            [phrase_model_data],
            "scene_s3_key",
        )

    async def test_bulk_create(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_create_schema_data: PhraseCreateSchema,
        mock_presigned_url_service: mock.AsyncMock,
    ):
        mock_presigned_url_service.update_s3_urls_for_models.return_value = [
            [phrase_model_data],
        ]
        mock_phrases_repository.bulk_create.return_value = [phrase_model_data]

        result = await phrases_service.bulk_create([phrase_create_schema_data])

        assert len(result) == 1
        assert result[0] == phrase_model_data
        mock_phrases_repository.bulk_create.assert_awaited_once_with(
            [phrase_create_schema_data],
        )
        mock_presigned_url_service.update_s3_urls_for_models.assert_called_once_with(
            [phrase_model_data],
            "scene_s3_key",
        )

    @pytest.mark.parametrize(
        "search_text",
        [
            "fruits: apples, bananas and oranges",
            "bananas",
            "fru'its .....::,,",
        ],
    )
    async def test_get_by_text(
        self,
        mock_presigned_url_service: mock.AsyncMock,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_by_search_text_schema_data: PhraseBySearchTextSchema,
        paginated_phrases_by_search_text_schema_data: PaginatedPhrasesBySearchTextSchema,
        search_text: str,
    ):
        mock_phrases_repository.get_by_search_text.return_value = Page(
            items=[phrase_model_data],
            total=1,
            page=1,
            size=3,
            pages=1,
        )

        result = await phrases_service.get_by_search_text(search_text, 1)

        assert result == paginated_phrases_by_search_text_schema_data

        mock_phrases_repository.get_by_search_text.assert_awaited_once_with(
            normalize_phrase_text(search_text),
            1,
        )
        mock_presigned_url_service.update_s3_urls_for_models.assert_awaited_once_with(
            [phrase_by_search_text_schema_data],
            "scene_s3_key",
        )

    async def test_delete_by_movie_id(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        mock_s3_service: mock.AsyncMock,
    ):
        mock_phrases_repository.delete_by_movie_id.return_value = [
            phrase_model_data.scene_s3_key,
        ]
        movie_s3_path = os.path.join(
            settings.movies_s3_path,
            str(phrase_model_data.movie_id),
        )

        result = await phrases_service.delete_by_movie_id(phrase_model_data.movie_id)

        assert result is None
        mock_phrases_repository.delete_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id,
        )
        mock_s3_service.delete_folder.assert_awaited_once_with(movie_s3_path)

    async def test_import_from_json(
        self,
        mock_phrases_repository: mock.AsyncMock,
        phrases_service: PhrasesService,
        phrase_transfer_schema_data: PhraseTransferSchema,
        random_movie_id: uuid.UUID,
    ):
        result = await phrases_service.import_from_json(movie_id=random_movie_id, data=[phrase_transfer_schema_data])

        assert result is None
        mock_phrases_repository.import_from_json.assert_awaited_once_with(
            random_movie_id,
            [phrase_transfer_schema_data],
        )

    async def test_export_to_json(
        self,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrases_service: PhrasesService,
        random_movie_id: uuid.UUID,
        phrase_transfer_schema_data: PhraseTransferSchema,
    ):
        mock_phrases_repository.get_by_movie_id.return_value = [phrase_model_data]

        result = await phrases_service.export_to_json(movie_id=random_movie_id)

        assert len(result) == 1
        assert result == [phrase_transfer_schema_data]
        mock_phrases_repository.get_by_movie_id.assert_awaited_once_with(random_movie_id)
