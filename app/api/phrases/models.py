import datetime
import typing
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.movies.models import MovieModel
from app.core.models import CoreModel, DateTimeModelMixin, IDModelMixin


class PhraseModel(CoreModel, IDModelMixin, DateTimeModelMixin):
    __tablename__ = "phrases"

    movie_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
    )
    full_text: Mapped[str]
    normalized_text: Mapped[str]

    start_in_movie: Mapped[datetime.timedelta]
    end_in_movie: Mapped[datetime.timedelta]
    scene_s3_key: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    movie: Mapped[MovieModel] = relationship(back_populates="phrases")
    issues: Mapped[typing.List["PhraseIssueModel"]] = relationship(
        back_populates="phrase",
    )

    @property
    def duration(self) -> datetime.timedelta:
        """
        TODO: add test ad return in miliseconds
        """
        return self.end_in_movie - self.start_in_movie


class PhraseIssueModel(CoreModel, IDModelMixin, DateTimeModelMixin):
    __tablename__ = "phrases_issues"

    issuer_ip: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    phrase_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("phrases.id", ondelete="CASCADE"))

    phrase: Mapped[PhraseModel] = relationship(back_populates="issues")
