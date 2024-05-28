from fastapi import Depends

from app.api.analytics.service import AnalyticsService
from app.api.phrases.dependencies import get_phrases_service
from app.api.phrases.service import PhrasesService


async def get_analytics_service(phrases_service: PhrasesService = Depends(get_phrases_service)) -> AnalyticsService:
    return AnalyticsService(phrases_service=phrases_service)
