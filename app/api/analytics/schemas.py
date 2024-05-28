import datetime
import uuid

from pydantic import BaseModel


class MovieAnalyticsSchema(BaseModel):
    movie_id: uuid.UUID
    phrases_duration: datetime.timedelta
    phrases_count: int
    unique_subphrases_count: int
