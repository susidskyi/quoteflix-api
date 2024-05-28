import functools
import operator
import uuid

from app.api.analytics.schemas import MovieAnalyticsSchema
from app.api.analytics.utils import get_all_subphrases_from_normalized_text
from app.api.phrases.service import PhrasesService


class AnalyticsService:
    def __init__(self, phrases_service: PhrasesService) -> None:
        self.phrases_service = phrases_service

    async def get_analytics_for_movie(self, movie_id: uuid.UUID) -> MovieAnalyticsSchema:
        """
        TODO: rewrite, optimize and add tests
        """
        phrases = await self.phrases_service.get_by_movie_id(movie_id=movie_id, presign_urls=False)
        phrases_duration = functools.reduce(operator.add, [phrase.duration for phrase in phrases])
        phrases_count = len(phrases)
        unique_subphrases = set()

        for phrase in phrases:
            unique_subphrases.update(get_all_subphrases_from_normalized_text(phrase.normalized_text))

        return MovieAnalyticsSchema(
            movie_id=movie_id,
            phrases_duration=phrases_duration,
            phrases_count=phrases_count,
            unique_subphrases_count=len(unique_subphrases),
        )
