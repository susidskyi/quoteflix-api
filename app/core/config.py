from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: PostgresDsn
    debug_logs: bool = False
    stage: str
    secret: str
    max_movie_file_size: int = 5 * 1024**3  # 5 GB
    max_subtitles_file_size: int = 10 * 1024**2  # 10 MB


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
