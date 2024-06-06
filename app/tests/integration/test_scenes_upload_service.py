import datetime
import io
import os
import uuid
from unittest import mock

import pytest
import pytest_mock
from fastapi import UploadFile

from app.api.phrases.models import PhraseModel
from app.api.phrases.scenes_upload_service import ScenesUploadService
from app.api.phrases.schemas import PhraseCreateSchema, PhraseUpdateSchema, SubtitleItem


@pytest.mark.asyncio()
class TestScenesUploadService:
    async def test_parse_subtitles_file(
        self,
        mocker: pytest_mock.MockerFixture,
        scenes_upload_service: ScenesUploadService,
        subtitle_item: SubtitleItem,
        subtitles_file: UploadFile,
    ):
        expected_subtitle_items = [subtitle_item]
        mock_normalize_phrase_text = mocker.patch(
            "app.api.phrases.scenes_upload_service.normalize_phrase_text",
            return_value=subtitle_item.normalized_text,
        )
        result_subtitle_items = await scenes_upload_service._parse_subtitles_file(subtitles_file, 0, 0)

        assert result_subtitle_items == expected_subtitle_items

        mock_normalize_phrase_text.assert_called_once_with(subtitle_item.text)

    async def test_parse_subtitles_file_with_time_shifts(
        self,
        mocker: pytest_mock.MockerFixture,
        scenes_upload_service: ScenesUploadService,
        subtitle_item: SubtitleItem,
        subtitles_file: UploadFile,
    ):
        expected_subtitle_items = [
            SubtitleItem(
                text=subtitle_item.text,
                normalized_text=subtitle_item.normalized_text,
                start_time=subtitle_item.start_time - datetime.timedelta(seconds=10),
                end_time=subtitle_item.end_time - datetime.timedelta(seconds=10),
            ),
        ]

        mock_normalize_phrase_text = mocker.patch(
            "app.api.phrases.scenes_upload_service.normalize_phrase_text",
            return_value=subtitle_item.normalized_text,
        )
        result_subtitle_items = await scenes_upload_service._parse_subtitles_file(subtitles_file, -10, -10)

        assert result_subtitle_items == expected_subtitle_items

        mock_normalize_phrase_text.assert_called_once_with(subtitle_item.text)

    async def test_create_phrases(
        self,
        random_movie_id: uuid.UUID,
        scenes_upload_service: ScenesUploadService,
        subtitle_item: SubtitleItem,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_create_schema_data: PhraseCreateSchema,
    ):
        mock_phrases_service.bulk_create.return_value = [phrase_model_data]
        phrase_create_schema_data.is_active = False

        result = await scenes_upload_service._create_phrases(random_movie_id, [subtitle_item])

        assert result == [phrase_model_data]
        mock_phrases_service.bulk_create.assert_awaited_once_with([phrase_create_schema_data])

    async def test_get_scene_file(
        self,
        scenes_upload_service: ScenesUploadService,
        scene_file_buffered_bytes: io.BytesIO,
    ):
        result = await scenes_upload_service._get_scene_file("tests/data", "scene.mp4")

        assert result.read() == scene_file_buffered_bytes.read()

    async def test_process_subtitles_and_create_scenes(
        self,
        random_movie_id: uuid.UUID,
        scenes_upload_service: ScenesUploadService,
        subtitle_item: SubtitleItem,
        mock_phrases_service: mock.AsyncMock,
        phrase_model_data: PhraseModel,
        phrase_create_schema_data: PhraseCreateSchema,
        scene_file_buffered_bytes: io.BytesIO,
        movie_file: UploadFile,
        mocker: pytest_mock.MockerFixture,
        mock_s3_service: mock.AsyncMock,
    ):
        phrases = [phrase_model_data]
        mock_create_phrases = mocker.patch.object(ScenesUploadService, "_create_phrases", return_value=phrases)
        mock_create_scenes_files = mocker.patch.object(ScenesUploadService, "_create_scenes_files")
        mock_get_scene_file = mocker.patch.object(
            ScenesUploadService,
            "_get_scene_file",
            return_value=scene_file_buffered_bytes,
        )
        tmp_output_dir = "tests/data"
        scene_filename = f"{phrase_model_data.id}.mp4"
        scene_s3_key = os.path.join("movies", str(random_movie_id), str(scene_filename))

        await scenes_upload_service._process_subtitles_and_create_scenes(
            random_movie_id,
            movie_file,
            [subtitle_item],
            tmp_output_dir,
        )

        mock_create_phrases.assert_awaited_once_with(random_movie_id, [subtitle_item])
        mock_create_scenes_files.assert_awaited_once_with(movie_file, "movie", phrases, tmp_output_dir, ".mp4")
        assert mock_get_scene_file.await_count == len(phrases)
        assert mock_s3_service.upload_fileobj.await_count == len(phrases)
        assert mock_phrases_service.update.await_count == len(phrases)

        for phrase in phrases:
            mock_get_scene_file.assert_awaited_with(tmp_output_dir, f"{phrase.id}.mp4")
            mock_s3_service.upload_fileobj.assert_awaited_with(scene_file_buffered_bytes, scene_s3_key)
            expected_new_phrase_data = {
                **phrase.__dict__,
                "scene_s3_key": scene_s3_key,
                "is_active": True,
            }
            mock_phrases_service.update.assert_awaited_with(
                phrase.id,
                PhraseUpdateSchema(**expected_new_phrase_data),
            )
