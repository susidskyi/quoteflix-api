import uuid

from fastapi import Depends
from fastapi.routing import APIRouter

from app.api.analytics.dependencies import get_analytics_service
from app.api.analytics.schemas import MovieAnalyticsSchema
from app.api.analytics.service import AnalyticsService
from app.api.movies.dependencies import movie_exists
from app.api.users.permissions import current_superuser

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/for-movie/{movie_id}",
    name="analytics:get-analytics-for-movie",
    response_model=MovieAnalyticsSchema,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def get_analytics_for_movie(
    movie_id: uuid.UUID,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> MovieAnalyticsSchema:
    """
    TODO: add tests
    """
    return await analytics_service.get_analytics_for_movie(movie_id)
