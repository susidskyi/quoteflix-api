import uuid

from app.api.issues.repository import IssuesRepository


class IssuesService:
    def __init__(self, issues_repository: IssuesRepository) -> None:
        self.repository = issues_repository

    async def report_phrase_issue(self, phrase_id: uuid.UUID, issuer_ip: str) -> None:
        await self.repository.report_phrase_issue(phrase_id, issuer_ip)
