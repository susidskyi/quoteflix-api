import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import CoreModel, DateTimeModelMixin, IDModelMixin


class PhraseIssueReport(CoreModel, IDModelMixin, DateTimeModelMixin):
    __tablename__ = "phrase_issue_reports"

    issuer_ip = Mapped[str]
    phrase_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("phrases.id", ondelete="CASCADE"))
