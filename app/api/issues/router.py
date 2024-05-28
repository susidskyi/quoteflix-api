import uuid

from fastapi import BackgroundTasks, Depends, Request, status
from fastapi.routing import APIRouter

from app.api.issues.dependencies import get_issues_service
from app.api.issues.service import IssuesService
from app.api.phrases.dependencies import phrase_exists

router = APIRouter(prefix="/issues", tags=["issues"])


@router.post(
    "/report-phrase-issue/{phrase_id}",
    name="phrases:report-phrase-issue",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(phrase_exists)],
)
async def report_phrase_issue(
    request: Request,
    phrase_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    issues_service: IssuesService = Depends(get_issues_service),
) -> None:
    issuer_id = request.client.host
    background_tasks.add_task(issues_service.report_phrase_issue, phrase_id, issuer_id)
