from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    debug_logs: bool = False
    environment: str
    secret: str
    scenes_tmp_path: str
    phrases_page_size: int = 3

    # Database
    database_url: PostgresDsn
    test_database_url: PostgresDsn

    # S3
    s3_bucket: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_region_name: str
    movies_s3_path: str

    # Redis
    redis_api_cache_url: RedisDsn

    # Logfire
    logfire_token: str

    # Limits
    max_movie_file_size: int = 5 * 1024**3  # 5 GB
    max_subtitles_file_size: int = 10 * 1024**2  # 10 MB
    max_ffmpeg_workers: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
