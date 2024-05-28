import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.issues.models import PhraseIssueReport


class IssuesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def report_phrase_issue(self, phrase_id: uuid.UUID, issuer_ip: str) -> None:
        async with self.session as session:
            issue_exists_stmt = select(
                exists().where(PhraseIssueReport.issuer_ip == issuer_ip, PhraseIssueReport.phrase_id == phrase_id)
            )
            issue_exists = await session.scalar(issue_exists_stmt)

            if not issue_exists:
                issue = PhraseIssueReport(
                    phrase_id=phrase_id,
                    issuer_ip=issuer_ip,
                )

                session.add(issue)
                session.commit()
