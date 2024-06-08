import abc
import datetime
import uuid
from typing import Sequence

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator, model_validator

from app.api.movies.schemas import MovieInSearchByPhraseTextSchema
from app.api.phrases.utils import format_duration
from app.core.config import settings
from app.core.constants import SUPPORTED_SUBTITLES_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS
from app.core.validators import FileValidator


class PhraseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    movie_id: uuid.UUID
    full_text: str
    normalized_text: str
    start_in_movie: datetime.timedelta
    end_in_movie: datetime.timedelta
    scene_s3_key: str | None

    @field_serializer("start_in_movie", "end_in_movie", when_used="json")
    def serialize_duration(self, value: datetime.timedelta) -> str:
        return format_duration(value)


class PhraseBySearchTextSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_text: str
    scene_s3_key: str | None
    matched_phrase: str
    start_in_movie: datetime.timedelta
    movie: MovieInSearchByPhraseTextSchema

    @field_serializer("start_in_movie", when_used="json")
    def serialize_duration(self, value: datetime.timedelta) -> str:
        return format_duration(value)


class PaginatedPhrasesBySearchTextSchema(BaseModel):
    items: Sequence[PhraseBySearchTextSchema]
    total: int
    page: int
    size: int
    pages: int


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

    @field_serializer("start_in_movie", "end_in_movie", when_used="json")
    def serialize_duration(self, value: datetime.timedelta) -> str:
        return format_duration(value)


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
    id: uuid.UUID
    full_text: str
    normalized_text: str
    start_in_movie: datetime.timedelta
    end_in_movie: datetime.timedelta
    scene_s3_key: str

    @field_serializer("start_in_movie", "end_in_movie", when_used="json")
    def serialize_duration(self, value: datetime.timedelta) -> str:
        return format_duration(value)


class PhraseIssueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issuer_ip: str
    phrase: PhraseSchema
    created_at: datetime.datetime


class PhraseIssueCreateSchema(BaseModel):
    issuer_ip: str
    phrase_id: uuid.UUID
