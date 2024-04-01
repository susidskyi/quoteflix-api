import json
import uuid
from unittest import mock

import pytest

from app.api.phrases.models import PhraseModel
from app.api.phrases.schemas import PhraseCreateSchema, PhraseUpdateSchema
from app.api.phrases.service import PhrasesService
from app.api.phrases.utils import normalize_phrase_text


@pytest.mark.asyncio
class TestPhrasesService:
    async def test_create(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_create_schema_data: PhraseCreateSchema,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.create.return_value = phrase_model_data

        phrase = await phrases_service.create(phrase_create_schema_data)

        assert phrase == phrase_model_data
        mock_phrases_repository.create.assert_awaited_once_with(
            phrase_create_schema_data
        )

    async def test_get_by_id(
        self,
        phrases_service: PhrasesService,
        phrase_create_schema_data: PhraseCreateSchema,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.get_by_id.return_value = phrase_model_data

        phrase = await phrases_service.get_by_id(phrase_model_data.id)

        assert phrase == phrase_model_data
        mock_phrases_repository.get_by_id.assert_awaited_once_with(phrase_model_data.id)

    async def test_update(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        mock_phrases_repository.update.return_value = phrase_model_data

        phrase = await phrases_service.update(
            phrase_model_data.id, phrase_update_schema_data
        )

        assert phrase == phrase_model_data
        mock_phrases_repository.update.assert_awaited_once_with(
            phrase_model_data.id, phrase_update_schema_data
        )

    async def test_delete(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.delete.return_value = None

        result = await phrases_service.delete(phrase_model_data.id)

        assert result is None
        mock_phrases_repository.delete.assert_awaited_once_with(phrase_model_data.id)

    async def test_get_all(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
    ):
        mock_phrases_repository.get_all.return_value = [phrase_model_data]

        result = await phrases_service.get_all()

        assert len(result) == 1
        assert result[0] == phrase_model_data
        mock_phrases_repository.get_all.assert_awaited_once()

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
    ):
        mock_phrases_repository.get_by_movie_id.return_value = [phrase_model_data]

        result = await phrases_service.get_by_movie_id(phrase_model_data.movie_id)

        assert len(result) == 1
        assert result[0] == phrase_model_data
        mock_phrases_repository.get_by_movie_id.assert_awaited_once_with(
            phrase_model_data.movie_id
        )

    async def test_bulk_create(
        self,
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_create_schema_data: PhraseCreateSchema,
    ):
        mock_phrases_repository.bulk_create.return_value = [phrase_model_data]

        result = await phrases_service.bulk_create([phrase_create_schema_data])

        assert len(result) == 1
        assert result[0] == phrase_model_data
        mock_phrases_repository.bulk_create.assert_awaited_once_with(
            [phrase_create_schema_data]
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
        phrases_service: PhrasesService,
        mock_phrases_repository: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        search_text: str,
    ):
        mock_phrases_repository.get_by_search_text.return_value = [phrase_model_data]
        normalized_text = normalize_phrase_text(search_text)

        result = await phrases_service.get_by_search_text(search_text)

        assert len(result) == 1
        assert phrase_model_data in result

        mock_phrases_repository.get_by_search_text.assert_awaited_once_with(
            normalized_text
        )
