import abc
import datetime
import uuid

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.config import settings
from app.core.constants import SUPPORTED_SUBTITLES_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS
from app.core.validators import FileValidator


class PhraseSchema(BaseModel):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
    movie_id: uuid.UUID
    full_text: str
    scene_s3_key: str | None


class PhraseCreateUpdateSchema(BaseModel, abc.ABC):
    movie_id: uuid.UUID
    full_text: str
    normalized_text: str
    start_in_movie: datetime.timedelta
    end_in_movie: datetime.timedelta
    is_active: bool = True

    @model_validator(mode="after")
    def validate_start_time_less_than_end(self) -> "PhraseCreateUpdateSchema":
        if self.start_in_movie >= self.end_in_movie:
            raise ValueError("Start time must be less than end time")

        return self


class PhraseCreateSchema(PhraseCreateUpdateSchema):
    pass


class PhraseUpdateSchema(PhraseCreateUpdateSchema):
    scene_s3_key: str


class PhraseCreateFromMovieFilesSchema(BaseModel):
    movie_file: UploadFile
    subtitles_file: UploadFile

    @field_validator("movie_file")
    @classmethod
    def validate_movie_file(cls, value: UploadFile) -> UploadFile:
        FileValidator.validate_file_type(file=value, supported_extensions=SUPPORTED_VIDEO_EXTENSIONS)
        FileValidator.validate_file_size(file=value, max_size=settings.max_movie_file_size)
        FileValidator.validate_file_name(file=value)

        return value

    @field_validator("subtitles_file")
    @classmethod
    def validate_subtitles_file(cls, value: UploadFile) -> UploadFile:
        FileValidator.validate_file_type(file=value, supported_extensions=SUPPORTED_SUBTITLES_EXTENSIONS)
        FileValidator.validate_file_size(file=value, max_size=settings.max_subtitles_file_size)
        FileValidator.validate_file_name(file=value)

        return value

    @classmethod
    async def depends(
        cls,
        subtitles_file: UploadFile,
        movie_file: UploadFile,
    ) -> "PhraseCreateFromMovieFilesSchema":
        return cls(movie_file=movie_file, subtitles_file=subtitles_file)


class SubtitleItem(BaseModel):
    start_time: datetime.timedelta
    end_time: datetime.timedelta
    text: str
    normalized_text: str

    @model_validator(mode="after")
    def validate_start_time_less_than_end(self) -> "SubtitleItem":
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be less than end time")

        return self


class PhraseTransferSchema(BaseModel):
    full_text: str
    normalized_text: str
    start_in_movie: datetime.timedelta
    end_in_movie: datetime.timedelta
    scene_s3_key: str
