import uuid
from app.core.models import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from app.api.movies.models import MovieModel
import datetime


class PhraseModel(BaseModel):
    __tablename__ = "phrases"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE")
    )
    full_text: Mapped[str]
    cleaned_text: Mapped[str]
    start_in_movie: Mapped[datetime.time]
    end_in_movie: Mapped[datetime.time]
    file_s3_key: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    movie: Mapped["MovieModel"] = relationship("movie_id")
