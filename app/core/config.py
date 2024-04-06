from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    debug_logs: bool = False
    stage: str
    secret: str
    scenes_tmp_path: str

    # Database
    database_url: PostgresDsn
    test_database_url: PostgresDsn

    # AWS
    s3_bucket: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    movies_s3_path: str

    # Limits
    max_movie_file_size: int = 5 * 1024**3  # 5 GB
    max_subtitles_file_size: int = 10 * 1024**2  # 10 MB


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
