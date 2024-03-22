from fastapi import UploadFile
from fastapi_storages import FileSystemStorage
from fastapi_storages.integrations.sqlalchemy import FileType
from pydantic import BaseModel as PydanticBaseModel
from pydantic import PositiveInt
from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.api.movies.constants import Languages, MovieStatus
from app.core.models import BaseModel


class MovieModel(BaseModel):
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

    class Create(PydanticBaseModel):
        title: str
        year: PositiveInt
        language: Languages
        file: UploadFile | None
        subtitles_file: UploadFile | None
        is_active: bool = False
        status: MovieStatus = MovieStatus.PENDING

    class Update(Create):
        pass
