import asyncio
import datetime
import io
import logging
import os
import shutil
import uuid
from pathlib import Path
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
from app.api.phrases.utils import get_ffmpeg_trim_cmd_for_phrase, normalize_phrase_text
from app.core.config import settings
from app.core.constants import MovieStatus
from app.core.exceptions import SceneUploadError
from app.s3.s3_service import S3Service

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
        tmp_output_dir = Path(settings.scenes_tmp_path, "movies", str(movie_id))
        self._setup_tmp_path(tmp_output_dir)

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

        return subtitle_items[:10]

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
        tmp_output_dir: Path,
    ) -> None:
        """
        Processes subtitles and creates scenes for each phrase
        """
        phrases = await self._create_phrases(movie_id, subtitle_items)

        if movie_file.filename is None:
            raise SceneUploadError("No movie file provided")

        movie_filename = movie_file.filename
        movie_extension = Path(movie_filename).suffix

        await self._create_scenes_files(
            movie_file,
            movie_filename,
            phrases,
            tmp_output_dir,
        )

        for phrase in phrases:
            try:
                scene_filename = f"{phrase.id}{movie_extension}"
                scene_file = await self._get_scene_file(tmp_output_dir, scene_filename)
                scene_s3_key = Path("movies", str(movie_id), scene_filename).as_posix()

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
        tmp_output_dir: Path,
        scene_filename: str,
    ) -> io.BytesIO:
        phrase_file_path = Path(tmp_output_dir, scene_filename)

        async with aiofiles.open(phrase_file_path, "rb") as f:
            return io.BytesIO(await f.read())

    async def _create_scenes_files(
        self,
        movie_file: UploadFile,
        movie_filename: str,
        phrases: Sequence[PhraseModel],
        tmp_output_dir: Path,
    ) -> None:
        movie_path = Path(tmp_output_dir, movie_filename)

        async with aiofiles.open(movie_path, "wb") as f:
            while chunk := await movie_file.read(1024 * 1024 * 100):  # 100 mb
                await f.write(chunk)

        for phrase in phrases:
            cmd = get_ffmpeg_trim_cmd_for_phrase(phrase, movie_path, tmp_output_dir)

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await proc.communicate()

    def _tear_down_tmp_path(self, path: Path) -> None:
        shutil.rmtree(path, ignore_errors=True)

    def _setup_tmp_path(self, path: Path) -> None:
        self._tear_down_tmp_path(path)

        os.makedirs(path, exist_ok=True)

    async def _rollback(self, movie_id: uuid.UUID, tmp_output_dir: Path) -> None:
        await self.movies_service.update_status(movie_id, MovieStatus.ERROR)
        self._tear_down_tmp_path(tmp_output_dir)
