from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    debug_logs: bool = False
    environment: str
    secret: str
    scenes_tmp_path: str

    # Database
    database_url: PostgresDsn
    test_database_url: PostgresDsn

    # AWS | CloudFlare
    s3_bucket: str
    s3_endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    movies_s3_path: str

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
