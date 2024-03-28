import abc
import datetime
import uuid

from pydantic import BaseModel, field_validator, model_validator


class PhraseSchema(BaseModel):
    movie_id: uuid.UUID
    full_text: str
    file_s3_key: str


class PhraseCreateUpdateSchema(BaseModel, abc.ABC):
    movie_id: uuid.UUID
    full_text: str
    cleaned_text: str
    start_in_movie: str
    end_in_movie: str
    is_active: bool = True

    @field_validator("start_in_movie", "end_in_movie")
    @classmethod
    def validate_time(cls, value: str) -> str:
        """
        Check the time format should be %H:%M:%S:%.%f
        Example: 00:00:00:00.000000
        """
        time_format = "%H:%M:%S.%f"

        try:
            datetime.datetime.strptime(value, time_format)
        except ValueError as e:
            raise ValueError(f"Time must be in format {time_format}") from e

        return value

    @model_validator(mode="after")
    def validate_start_time_less_than_end(self) -> "PhraseCreateUpdateSchema":
        start_in_movie_time = datetime.datetime.strptime(
            self.start_in_movie, "%H:%M:%S.%f"
        )
        end_in_movie_time = datetime.datetime.strptime(self.end_in_movie, "%H:%M:%S.%f")

        if start_in_movie_time >= end_in_movie_time:
            raise ValueError("Start time must be less than end time")

        return self


class PhraseCreateSchema(PhraseCreateUpdateSchema):
    pass


class PhraseUpdateSchema(PhraseCreateUpdateSchema):
    file_s3_key: str
