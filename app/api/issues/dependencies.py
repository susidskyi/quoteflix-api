from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.api.issues.repository import IssuesRepository
from app.api.issues.service import IssuesService


async def get_issues_repository(session: AsyncSession = Depends(get_db_session)) -> IssuesRepository:
    return IssuesRepository(session=session)


async def get_issues_service(issues_repository: IssuesRepository) -> IssuesService:
    return IssuesService(issues_repository=issues_repository)
