import datetime
import uuid

from fastapi import UploadFile
from pydantic import BaseModel

from app.api.movies.constants import Languages, MovieStatus


class MovieSchema(BaseModel):
    id: uuid.UUID
    title: str
    year: int
    status: MovieStatus
    language: Languages
    created_at: datetime.datetime
    updated_at: datetime.datetime
