import datetime
import uuid

from pydantic import BaseModel, field_serializer

from app.api.phrases.utils import format_duration


class MovieAnalyticsSchema(BaseModel):
    movie_id: uuid.UUID
    phrases_duration: datetime.timedelta
    phrases_count: int
    unique_subphrases_count: int

    @field_serializer("phrases_duration", when_used="json")
    def serialize_duration(self, value: datetime.timedelta) -> str:
        return format_duration(value)
