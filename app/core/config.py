from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: PostgresDsn
    debug_logs: bool = False
    stage: str
    secret: str


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
