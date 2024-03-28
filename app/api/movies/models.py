from typing import List

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.movies.constants import Languages, MovieStatus
from app.core.models import BaseModel


class MovieModel(BaseModel):
    __tablename__ = "movies"

    title: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(SmallInteger)
    is_active: Mapped[bool] = mapped_column(default=False)
    status: Mapped[MovieStatus] = mapped_column(default=MovieStatus.PENDING)
    language: Mapped[Languages]

    phrases: Mapped[List["PhraseModel"]] = relationship(  # type: ignore # noqa: F821
        back_populates="movie"
    )
