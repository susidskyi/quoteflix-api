import abc
import datetime
import uuid

from fastapi import File, Form, HTTPException, UploadFile
from fastapi import status as fastapi_status
from fastapi_storages.base import StorageFile
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.functional_validators import field_validator

from app.api.movies.constants import (
    SUPPORTED_SUBTITLES_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    Languages,
    MovieStatus,
)
from app.core.config import settings
from app.core.validators import FileValidator


class MovieSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    title: str
    year: int
    status: MovieStatus
    language: Languages
    is_active: bool
    file: StorageFile | None
    subtitles_file: StorageFile | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MovieCreateUpdateBase(BaseModel, abc.ABC):

    @field_validator("subtitles_file", check_fields=False)
    @classmethod
    def validatate_subtitles_file(cls, value: UploadFile | None) -> UploadFile | None:
        if value is None:
            return None

        FileValidator.validate_file_size(value, settings.max_subtitles_file_size)
        FileValidator.validate_file_type(value, SUPPORTED_SUBTITLES_EXTENSIONS)

        return value

    @field_validator("file", check_fields=False)
    @classmethod
    def validatate_movie_file(cls, value: UploadFile | None) -> UploadFile | None:
        if value is None:
            return None

        FileValidator.validate_file_size(value, settings.max_movie_file_size)
        FileValidator.validate_file_type(value, SUPPORTED_VIDEO_EXTENSIONS)

        return value


class MovieCreateSchema(MovieCreateUpdateBase):
    title: str
    year: int
    language: Languages
    file: UploadFile | None
    subtitles_file: UploadFile | None
    is_active: bool = False
    status: MovieStatus = MovieStatus.PENDING

    @classmethod
    async def depends(
        cls,
        title: str = Form(),
        year: int = Form(),
        language: Languages = Form(),
        is_active: bool = Form(default=False),
        status: MovieStatus = Form(default=MovieStatus.PENDING),
        file: UploadFile | None = File(default=None),
        subtitles_file: UploadFile | None = File(default=None),
    ):
        try:
            return cls(
                title=title,
                year=year,
                language=language,
                is_active=is_active,
                status=status,
                file=file,
                subtitles_file=subtitles_file,
            )
        except ValidationError as e:
            for error in e.errors():
                error["loc"] = ["query"] + list(error["loc"])
            raise HTTPException(
                status_code=fastapi_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors(),
            )


class MovieUpdateSchema(MovieCreateSchema):
    pass
