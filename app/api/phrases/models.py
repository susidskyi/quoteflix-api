import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.movies.models import MovieModel
from app.core.models import BaseModel


class PhraseModel(BaseModel):
    __tablename__ = "phrases"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE")
    )
    full_text: Mapped[str]
    cleaned_text: Mapped[str]

    # Time are formated as %H:%M:%S:.%f
    start_in_movie: Mapped[str]
    end_in_movie: Mapped[str]
    file_s3_key: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    movie: Mapped[MovieModel] = relationship(back_populates="phrases")
