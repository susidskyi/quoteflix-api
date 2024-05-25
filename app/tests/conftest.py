import datetime
import io
import os
import uuid
from typing import AsyncGenerator, AsyncIterator, Callable
from unittest import mock

import aioboto3
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, UploadFile, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.movies.dependencies import get_movies_service
from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieCreateSchema, MovieSchema, MovieUpdateSchema
from app.api.movies.service import MoviesService
from app.api.phrases.dependencies import get_phrases_service
from app.api.phrases.models import PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.scenes_upload_service import ScenesUploadService
from app.api.phrases.schemas import (
    PhraseBySearchTextSchema,
    PhraseCreateSchema,
    PhraseSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
    SubtitleItem,
)
from app.api.phrases.service import PhrasesService
from app.api.users.models import UserModel
from app.core.config import settings
from app.core.constants import Languages, MovieStatus
from app.core.models import CoreModel
from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service
from app.main import app as main_app

"""
###############################################################################
[START] Core fixtures
###############################################################################
"""


@pytest.fixture()
def engine() -> AsyncEngine:
    return create_async_engine(str(settings.test_database_url))


@pytest.fixture()
def session_local(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine)


@pytest_asyncio.fixture
async def db(
    engine: AsyncEngine,
    session_local: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(CoreModel.metadata.drop_all)
        await conn.run_sync(CoreModel.metadata.create_all)

    db = session_local()

    try:
        yield db
    finally:
        await db.close()


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver.tst",
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return main_app


@pytest.fixture()
def app_with_dependency_overrides(
    app: FastAPI,
    mock_movies_service: mock.AsyncMock,
    mock_phrases_service: mock.AsyncMock,
) -> FastAPI:
    app.dependency_overrides = {}
    app.dependency_overrides[get_movies_service] = lambda: mock_movies_service
    app.dependency_overrides[get_phrases_service] = lambda: mock_phrases_service

    return app


"""
###############################################################################
[END] Core fixtures
###############################################################################
"""


"""
###############################################################################
[START] Users-app fixtures
###############################################################################
"""


@pytest.fixture()
def admin_user():
    return UserModel(
        id="00000000-0000-0000-0000-000000000001",
        first_name="Admin",
        last_name="User",
        email="admin@admin.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )


@pytest.fixture()
def anonymous_user():
    return None


@pytest.fixture()
def common_user():
    return UserModel(
        id="00000000-0000-0000-0000-000000000002",
        first_name="Common",
        last_name="User",
        email="common@common.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )


@pytest.fixture()
def check_is_superuser():
    def _check_permissions(user: UserModel | None) -> UserModel:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if user.is_superuser is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return user

    return _check_permissions


"""
###############################################################################
[END] Users-app fixtures
###############################################################################
"""

"""
###############################################################################
[START] Movie-app fixtures
###############################################################################
"""


@pytest.fixture()
def movies_repository(db: AsyncSession) -> MoviesRepository:
    return MoviesRepository(db)


@pytest.fixture()
def mock_movies_repository() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def movies_service(
    mock_movies_repository: mock.AsyncMock,
    mock_s3_service: mock.AsyncMock,
) -> MoviesService:
    return MoviesService(mock_movies_repository, mock_s3_service)


@pytest.fixture()
def mock_movies_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def random_movie_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def create_movie(db: AsyncSession) -> Callable[[MovieModel], MovieModel]:
    async def _create_movie(movie: MovieModel) -> MovieModel:
        db.add(movie)
        await db.commit()
        await db.refresh(movie)

        return movie

    return _create_movie


@pytest.fixture()
def movie_create_schema_data() -> MovieCreateSchema:
    return MovieCreateSchema(
        title="Test",
        year=2000,
        status=MovieStatus.PENDING,
        language=Languages.EN,
    )


@pytest.fixture()
def movie_update_schema_data(
    movie_create_schema_data: MovieCreateSchema,
) -> MovieUpdateSchema:
    return MovieUpdateSchema(**movie_create_schema_data.model_dump())


@pytest.fixture()
def movie_model_data(
    movie_create_schema_data: MovieCreateSchema,
    random_movie_id: uuid.UUID,
) -> MovieModel:
    return MovieModel(
        **movie_create_schema_data.model_dump(),
        id=random_movie_id,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


@pytest_asyncio.fixture
async def movie_fixture(
    create_movie: Callable[[MovieModel], MovieModel],
    movie_model_data: MovieModel,
) -> MovieModel:
    return await create_movie(movie_model_data)


@pytest.fixture()
def movie_schema_data(
    movie_model_data: MovieModel,
) -> MovieSchema:
    return MovieSchema(**movie_model_data.__dict__)


@pytest.fixture()
def check_movie_exists() -> Callable[[bool], None]:
    def _raise_exception(exists: bool) -> None:
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return _raise_exception


"""
###############################################################################
[END] Movie-app fixtures
"""

"""
###############################################################################
[START] Phrases-app fixtures
###############################################################################
"""


@pytest.fixture()
def phrases_repository(db: AsyncSession) -> PhrasesRepository:
    return PhrasesRepository(db)


@pytest.fixture()
def mock_phrases_repository() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def phrases_service(
    mock_phrases_repository: mock.AsyncMock,
    mock_s3_service: mock.AsyncMock,
    mock_presigned_url_service: mock.AsyncMock,
) -> PhrasesService:
    return PhrasesService(
        mock_phrases_repository,
        mock_s3_service,
        mock_presigned_url_service,
    )


@pytest.fixture()
def mock_phrases_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def random_phrase_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def create_phrase(db: AsyncSession) -> Callable[[PhraseModel], PhraseModel]:
    async def _create_phrase(phrase: PhraseModel) -> PhraseModel:
        db.add(phrase)
        await db.commit()
        await db.refresh(phrase)

        return phrase

    return _create_phrase


@pytest.fixture()
def phrase_create_schema_data(random_movie_id: uuid.UUID) -> PhraseCreateSchema:
    return PhraseCreateSchema(
        movie_id=random_movie_id,
        full_text="fruits: apples, bananas and oranges",
        normalized_text="fruits apples bananas and oranges",
        start_in_movie="00:00:30.000",
        end_in_movie="00:00:40.00000",
    )


@pytest.fixture()
def scene_s3_key() -> str:
    return "test/movies/test.mp4"


@pytest.fixture()
def phrase_update_schema_data(
    phrase_create_schema_data: PhraseCreateSchema,
    scene_s3_key: str,
) -> PhraseUpdateSchema:
    return PhraseUpdateSchema(
        **phrase_create_schema_data.model_dump(),
        scene_s3_key=scene_s3_key,
    )


@pytest.fixture()
def phrase_model_data(
    phrase_update_schema_data: PhraseUpdateSchema,
    random_phrase_id: uuid.UUID,
) -> PhraseModel:
    return PhraseModel(
        **phrase_update_schema_data.model_dump(),
        id=random_phrase_id,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


@pytest_asyncio.fixture
async def phrase_fixture(
    create_phrase: Callable[[PhraseCreateSchema], PhraseModel],
    phrase_model_data: PhraseModel,
    movie_fixture: MovieModel,
) -> PhraseModel:
    return await create_phrase(phrase_model_data)


@pytest.fixture()
def phrase_schema_data(
    phrase_fixture: PhraseModel,
) -> PhraseSchema:
    return PhraseSchema(**phrase_fixture.__dict__)


@pytest.fixture()
def phrase_by_search_text_schema_data(
    phrase_model_data: PhraseModel,
) -> PhraseBySearchTextSchema:
    """
    TODO: Update matched_phrase field when search text is added
    """
    return PhraseBySearchTextSchema(**phrase_model_data.__dict__, matched_phrase="")


@pytest.fixture()
def phrase_transfer_schema_data(
    phrase_model_data: PhraseModel,
) -> PhraseTransferSchema:
    return PhraseTransferSchema(**phrase_model_data.__dict__)


@pytest.fixture()
def check_phrase_exists() -> Callable[[bool], None]:
    def _raise_exception(exists: bool) -> None:
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return _raise_exception


"""
###############################################################################
[END] Phrases-app fixtures
###############################################################################
"""


"""
#############################################################################
[START] S3Service fixtures
#############################################################################
"""


@pytest.fixture()
def aws_region() -> str:
    return "eu-central-1"


@pytest.fixture()
def _setup_aws_credentials(aws_region: str) -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_ENDPOINT_URL"] = "http://motoserver:5000"
    os.environ["AWS_DEFAULT_REGION"] = aws_region


@pytest.fixture()
def s3_session(_setup_aws_credentials: None) -> aioboto3.Session:
    return aioboto3.Session()


@pytest.fixture()
def bucket_test_name() -> str:
    return settings.s3_bucket


@pytest_asyncio.fixture()
async def _setup_bucket(s3_session: aioboto3.Session, bucket_test_name: str, aws_region: str) -> None:
    """
    Delete the bucket if it alread exists and create fresh bucket for tests
    """

    async with s3_session.client("s3") as s3_client:
        try:
            list_objects = await s3_client.list_objects_v2(Bucket=bucket_test_name)
            list_objects_keys = []

            if "Contents" in list_objects:
                list_objects_keys = [{"Key": x["Key"]} for x in list_objects["Contents"]]

            if list_objects_keys:
                await s3_client.delete_objects(
                    Bucket=bucket_test_name,
                    Delete={"Objects": list_objects_keys},
                )

            await s3_client.delete_bucket(Bucket=bucket_test_name)
        except s3_client.exceptions.NoSuchBucket:
            pass

        location = {"LocationConstraint": aws_region}
        await s3_client.create_bucket(
            Bucket=bucket_test_name,
            CreateBucketConfiguration=location,
        )


@pytest_asyncio.fixture()
async def s3_service(s3_session: aioboto3.Session, _setup_bucket: None) -> S3Service:
    return S3Service(s3_session=s3_session)


@pytest.fixture()
def mock_s3_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def movie_in_s3_prefix(
    random_movie_id: uuid.UUID,
) -> str:
    return os.path.join(settings.movies_s3_path, str(random_movie_id))


@pytest.fixture()
def file_in_s3_key(movie_in_s3_prefix: str, random_phrase_id: uuid.UUID) -> str:
    return os.path.join(movie_in_s3_prefix, f"{random_phrase_id}.mp4")


@pytest_asyncio.fixture
async def created_file_in_s3(
    s3_session: aioboto3.Session,
    bucket_test_name: str,
    file_in_s3_key: str,
    scene_file_buffered_bytes: io.BytesIO,
):
    async with s3_session.client("s3") as s3_client:
        await s3_client.upload_fileobj(
            scene_file_buffered_bytes,
            bucket_test_name,
            file_in_s3_key,
        )


"""
###############################################################################
[END]
#############################################################################
"""

"""
###############################################################################
[START] Scenes-upload-service fixtures
###############################################################################
"""


@pytest.fixture()
def scenes_upload_service(
    mock_phrases_service: mock.AsyncMock,
    mock_movies_service: mock.AsyncMock,
    mock_s3_service: mock.AsyncMock,
) -> ScenesUploadService:
    return ScenesUploadService(
        movies_service=mock_movies_service,
        phrases_service=mock_phrases_service,
        s3_service=mock_s3_service,
    )


@pytest.fixture()
def mock_scenes_upload_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def subtitle_file() -> UploadFile:
    with open("tests/data/subtitles.srt", "rb") as f:
        return UploadFile(
            file=io.BytesIO(f.read()),
            filename="subtitles.srt",
            size=69,
            headers={"Content-Type": "text/plain"},
        )


@pytest.fixture()
def movie_file() -> UploadFile:
    with open("tests/data/movie.mp4", "rb") as f:
        return UploadFile(
            file=io.BytesIO(f.read()),
            filename="movie.mp4",
            size=1055736,
            headers={"Content-Type": "video/mp4"},
        )


@pytest.fixture()
def subtitle_item() -> SubtitleItem:
    return SubtitleItem(
        start_time=datetime.timedelta(seconds=30),
        end_time=datetime.timedelta(seconds=40),
        text="fruits: apples, bananas and oranges",
        normalized_text="fruits apples bananas and oranges",
    )


@pytest.fixture()
def scene_file_buffered_bytes() -> io.BytesIO:
    with open("tests/data/scene.mp4", "rb") as f:
        return io.BytesIO(f.read())


"""
###############################################################################
[END] Scenes-upload-service fixtures
###############################################################################
"""

"""
###############################################################################
[START] Presigned-url-service fixtures
###############################################################################
"""


@pytest.fixture()
def presigned_url_service(mock_s3_service: mock.AsyncMock) -> PresignedURLService:
    return PresignedURLService(s3_service=mock_s3_service)


@pytest.fixture()
def mock_presigned_url_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture()
def mock_presigned_url_value() -> str:
    return "https://flickphrase.s3.aws/key"


"""
###############################################################################
[END] Presigned-url-service fixtures
###############################################################################
"""
