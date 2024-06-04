import abc
import datetime
import uuid

from pydantic import BaseModel, ConfigDict

from app.core.constants import (
    Languages,
    MovieStatus,
)


class MovieSchema(BaseModel):
    id: uuid.UUID
    title: str
    year: int
    status: MovieStatus
    language: Languages
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MovieCreateUpdateBase(BaseModel, abc.ABC):
    title: str
    year: int
    language: Languages


class MovieCreateSchema(MovieCreateUpdateBase):
    is_active: bool = False
    status: MovieStatus = MovieStatus.PENDING


class MovieUpdateSchema(MovieCreateUpdateBase):
    is_active: bool
    status: MovieStatus


class MovieUpdateStatusSchema(BaseModel):
    status: MovieStatus


class MovieInSearchByPhraseTextSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    year: int
