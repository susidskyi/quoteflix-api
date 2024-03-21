from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import SmallInteger, String
from app.core.models import BaseModel
from app.api.movies.constants import MovieStatus, Languages
from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import FileType


class Movie(BaseModel):
    __tablename__ = "movies"

    title: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(SmallInteger)
    is_active: Mapped[bool] = mapped_column(default=False)
    status: Mapped[MovieStatus] = mapped_column(default=MovieStatus.PENDING)
    file: Mapped[FileType] = mapped_column(
        FileType(FileSystemStorage(path="movies/")), nullable=True
    )
    subtitles_file: Mapped[FileType] = mapped_column(
        FileType(FileSystemStorage(path="subtitles/")), nullable=True
    )
    language: Mapped[Languages]
