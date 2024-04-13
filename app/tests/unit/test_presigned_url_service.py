from unittest import mock

import pytest

from app.api.phrases.models import PhraseModel
from app.core.presigned_url_service import PresignedURLService


@pytest.mark.asyncio()
class TestPresignedURLService:
    async def test_update_s3_urls_for_models_key_exists(
        self,
        presigned_url_service: PresignedURLService,
        mock_s3_service: mock.AsyncMock,
        mock_presigned_url_value: str,
        phrase_model_data: PhraseModel,
        scene_s3_key: str,
    ):
        mock_s3_service.get_presigned_url.return_value = mock_presigned_url_value

        result = await presigned_url_service.update_s3_urls_for_models(
            [phrase_model_data],
            "scene_s3_key",
        )

        assert result == [phrase_model_data]
        mock_s3_service.get_presigned_url.assert_awaited_once_with(scene_s3_key)

    async def test_update_s3_urls_for_models_key_is_empty(
        self,
        presigned_url_service: PresignedURLService,
        mock_s3_service: mock.AsyncMock,
        mock_presigned_url_value: str,
        phrase_model_data: PhraseModel,
    ):
        mock_s3_service.get_presigned_url.return_value = mock_presigned_url_value
        phrase_model_data.scene_s3_key = None

        result = await presigned_url_service.update_s3_urls_for_models(
            [phrase_model_data],
            "scene_s3_key",
        )

        assert result == [phrase_model_data]
        mock_s3_service.get_presigned_url.assert_not_awaited()

    async def test_update_s3_url_for_model_key_exists(
        self,
        presigned_url_service: PresignedURLService,
        mock_s3_service: mock.AsyncMock,
        mock_presigned_url_value: str,
        phrase_model_data: PhraseModel,
        scene_s3_key: str,
    ):
        mock_s3_service.get_presigned_url.return_value = mock_presigned_url_value

        result = await presigned_url_service.update_s3_url_for_model(
            phrase_model_data,
            "scene_s3_key",
        )

        assert result == phrase_model_data
        mock_s3_service.get_presigned_url.assert_awaited_once_with(scene_s3_key)

    async def test_update_s3_url_for_model_key_is_empty(
        self,
        presigned_url_service: PresignedURLService,
        mock_s3_service: mock.AsyncMock,
        mock_presigned_url_value: str,
        phrase_model_data: PhraseModel,
    ):
        mock_s3_service.get_presigned_url.return_value = mock_presigned_url_value
        phrase_model_data.scene_s3_key = None

        result = await presigned_url_service.update_s3_url_for_model(
            phrase_model_data,
            "scene_s3_key",
        )

        assert result == phrase_model_data
        mock_s3_service.get_presigned_url.assert_not_awaited()
