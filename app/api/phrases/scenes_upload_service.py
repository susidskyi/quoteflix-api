import asyncio
import datetime
import io
import itertools
import logging
import os
import shutil
import uuid
from typing import Sequence

import aiofiles
import srt
from fastapi import UploadFile

from app.api.movies.service import MoviesService
from app.api.phrases.models import PhraseModel
from app.api.phrases.schemas import (
    PhraseCreateSchema,
    PhraseUpdateSchema,
    SubtitleItem,
)
from app.api.phrases.service import PhrasesService
from app.api.phrases.utils import ffmpeg_output_arg_from_phrase, normalize_phrase_text
from app.core.config import settings
from app.core.constants import MovieStatus
from app.core.exceptions import SceneUploadError
from app.core.s3_service import S3Service

logger = logging.getLogger("multipart")
logger.setLevel(logging.INFO)


class ScenesUploadService:
    """
    Some day I'll use celery for this
    """

    def __init__(
        self,
        movies_service: MoviesService,
        phrases_service: PhrasesService,
        s3_service: S3Service,
    ) -> None:
        self.movies_service = movies_service
        self.phrases_service = phrases_service
        self.s3_service = s3_service

    async def upload_and_process_files(
        self,
        movie_id: uuid.UUID,
        movie_file: UploadFile,
        subtitles_file: UploadFile,
        start_in_movie_shift: float,
        end_in_movie_shift: float,
    ) -> None:
        """
        Uploads movie file and subtitle file to s3 and creates scenes for each phrase
        """
        tmp_output_dir = os.path.join(settings.scenes_tmp_path, "movies", str(movie_id))

        try:
            await self.movies_service.update_status(movie_id, MovieStatus.PROCESSING)

            subtitle_items = await self._parse_subtitles_file(
                subtitles_file,
                start_in_movie_shift,
                end_in_movie_shift,
            )
            await self._process_subtitles_and_create_scenes(
                movie_id,
                movie_file,
                subtitle_items,
                tmp_output_dir,
            )

            self._tear_down_tmp_path(tmp_output_dir)
            await self.movies_service.update_status(movie_id, MovieStatus.PROCESSED)
        except Exception as e:
            await self._rollback(movie_id, tmp_output_dir)
            raise SceneUploadError("Failed to upload scenes") from e

    async def _parse_subtitles_file(
        self,
        subtitles_file: UploadFile,
        start_in_movie_shift: float,
        end_in_movie_shift: float,
    ) -> Sequence[SubtitleItem]:
        """
        Parses subtitles file and returns list of SubtitleItems
        """
        subtitle_items = []

        contents = await subtitles_file.read()

        for sub in srt.parse(contents.decode("utf-8")):
            if start_in_movie_shift != 0:
                delta = datetime.timedelta(seconds=abs(start_in_movie_shift))
                if start_in_movie_shift > 0:
                    sub.start += delta
                else:
                    sub.start -= delta

            if end_in_movie_shift != 0:
                delta = datetime.timedelta(seconds=abs(end_in_movie_shift))
                if end_in_movie_shift > 0:
                    sub.end += delta
                else:
                    sub.end -= delta

            subtitle_items.append(
                SubtitleItem(
                    start_time=sub.start,
                    end_time=sub.end,
                    text=sub.content,
                    normalized_text=normalize_phrase_text(sub.content),
                ),
            )

        return subtitle_items[:50]

    async def _create_phrases(
        self,
        movie_id: uuid.UUID,
        subtitle_items: Sequence[SubtitleItem],
    ) -> Sequence[PhraseModel]:
        """
        Creates PhraseModel objects from list of SubtitleItems
        """
        phrase_objects = [
            PhraseCreateSchema(
                movie_id=movie_id,
                full_text=item.text,
                normalized_text=item.normalized_text,
                start_in_movie=item.start_time,
                end_in_movie=item.end_time,
                is_active=False,
            )
            for item in subtitle_items
        ]

        return await self.phrases_service.bulk_create(phrase_objects)

    async def _process_subtitles_and_create_scenes(
        self,
        movie_id: uuid.UUID,
        movie_file: UploadFile,
        subtitle_items: Sequence[SubtitleItem],
        tmp_output_dir: str,
    ) -> None:
        """
        Processes subtitles and creates scenes for each phrase
        """
        phrases = await self._create_phrases(movie_id, subtitle_items)

        if movie_file.filename is None:
            raise SceneUploadError("No movie file provided")

        movie_filename, video_extension = os.path.splitext(movie_file.filename)

        await self._create_scenes_files(
            movie_file,
            movie_filename,
            phrases,
            tmp_output_dir,
            video_extension,
        )

        for phrase in phrases:
            try:
                scene_filename = f"{phrase.id}{video_extension}"

                scene_file = await self._get_scene_file(tmp_output_dir, scene_filename)
                scene_s3_key = os.path.join("movies", str(movie_id), scene_filename)

                await self.s3_service.upload_fileobj(scene_file, scene_s3_key)

                new_phrase_data = {
                    **phrase.__dict__,
                    "scene_s3_key": scene_s3_key,
                    "is_active": True,
                }

                await self.phrases_service.update(
                    phrase.id,
                    PhraseUpdateSchema(**new_phrase_data),
                )

            except Exception as e:
                raise SceneUploadError() from e

    async def _get_scene_file(
        self,
        tmp_output_dir: str,
        scene_filename: str,
    ) -> io.BytesIO:
        phrase_file_path = os.path.join(tmp_output_dir, scene_filename)

        async with aiofiles.open(phrase_file_path, "rb") as f:
            return io.BytesIO(await f.read())

    async def _create_scenes_files(
        self,
        movie_file: UploadFile,
        movie_filename: str,
        phrases: Sequence[PhraseModel],
        tmp_output_dir: str,
        video_extension: str,
    ) -> None:
        self._setup_tmp_path(tmp_output_dir)

        movie_tmp_path = os.path.join(tmp_output_dir, movie_filename)

        async with aiofiles.open(movie_tmp_path, "wb") as f:
            while chunk := await movie_file.read(1024 * 1024 * 100):
                await f.write(chunk)

        cmd_scenes_output_args = [
            ffmpeg_output_arg_from_phrase(phrase, tmp_output_dir, video_extension) for phrase in phrases
        ]

        base_ffmpeg_command = f"ffmpeg -y -i {movie_tmp_path}"

        for phrases_args in itertools.batched(cmd_scenes_output_args, settings.max_ffmpeg_workers):
            output_args = " ".join(phrases_args)
            cmd = f"{base_ffmpeg_command} {output_args}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await proc.communicate()

    def _tear_down_tmp_path(self, path: str) -> None:
        shutil.rmtree(path, ignore_errors=True)

    def _setup_tmp_path(self, path: str) -> None:
        self._tear_down_tmp_path(path)

        os.makedirs(path, exist_ok=True)

    async def _rollback(self, movie_id: uuid.UUID, tmp_output_dir: str) -> None:
        await self.movies_service.update_status(movie_id, MovieStatus.ERROR)
        self._tear_down_tmp_path(tmp_output_dir)
