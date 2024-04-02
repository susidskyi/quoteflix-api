import datetime
import io
import uuid
from typing import AsyncGenerator, AsyncIterator, Callable
from unittest import mock

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
    PhraseCreateSchema,
    PhraseSchema,
    PhraseUpdateSchema,
    SubtitleItem,
)
from app.api.phrases.service import PhrasesService
from app.api.users.models import UserModel
from app.core.config import settings
from app.core.constants import Languages, MovieStatus
from app.core.models import BaseModel
from app.core.s3_service import S3Service
from app.main import app as main_app

"""
###############################################################################
[START] Core fixtures 
###############################################################################
"""


@pytest.fixture
def engine() -> AsyncEngine:
    engine = create_async_engine(str(settings.test_database_url))

    return engine


@pytest.fixture
def session_local(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    session_local = async_sessionmaker(engine)

    return session_local


@pytest_asyncio.fixture
async def db(
    engine: AsyncEngine, session_local: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncSession]:
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)

    db = session_local()

    try:
        yield db
    finally:
        await db.close()


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver.tst"
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return main_app


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def anonymous_user():
    return None


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def movies_repository(db: AsyncSession) -> MoviesRepository:
    return MoviesRepository(db)


@pytest.fixture
def mock_movies_repository() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture
def movies_service(movies_repository: MoviesRepository) -> MoviesService:
    return MoviesService(movies_repository)


@pytest.fixture
def mock_movies_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture
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


@pytest.fixture
def movie_create_schema_data() -> MovieCreateSchema:
    movie = MovieCreateSchema(
        title="Test",
        year=2000,
        status=MovieStatus.PENDING,
        language=Languages.EN,
    )

    return movie


@pytest.fixture
def movie_update_schema_data(
    movie_create_schema_data: MovieCreateSchema,
) -> MovieUpdateSchema:
    movie = MovieUpdateSchema(**movie_create_schema_data.model_dump())

    return movie


@pytest.fixture
def movie_model_data(
    movie_create_schema_data: MovieCreateSchema,
    random_movie_id: uuid.UUID,
) -> MovieModel:
    movie = MovieModel(
        **movie_create_schema_data.model_dump(),
        id=random_movie_id,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )

    return movie


@pytest_asyncio.fixture
async def movie_fixture(
    create_movie: Callable[[MovieModel], MovieModel],
    movie_model_data: MovieModel,
) -> MovieModel:
    movie = await create_movie(movie_model_data)

    return movie


@pytest.fixture
def movie_schema_data(
    movie_model_data: MovieModel,
) -> MovieSchema:
    movie = MovieSchema(**movie_model_data.__dict__)

    return movie


@pytest.fixture
def check_movie_exists() -> Callable[[bool], None]:
    def _raise_exception(exists: bool):
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


@pytest.fixture
def phrases_repository(db: AsyncSession) -> PhrasesRepository:
    return PhrasesRepository(db)


@pytest.fixture
def mock_phrases_repository() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture
def phrases_service(mock_phrases_repository: PhrasesRepository) -> PhrasesService:
    return PhrasesService(mock_phrases_repository)


@pytest.fixture
def mock_phrases_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture
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


@pytest.fixture
def phrase_create_schema_data(random_movie_id: uuid.UUID) -> PhraseCreateSchema:
    return PhraseCreateSchema(
        movie_id=random_movie_id,
        full_text="fruits: apples, bananas and oranges",
        normalized_text="fruits apples bananas and oranges",
        start_in_movie="00:00:30.000",
        end_in_movie="00:00:40.00000",
    )


@pytest.fixture
def scene_file_path() -> str:
    return "test/movies/test.mp4"


@pytest.fixture
def phrase_update_schema_data(
    phrase_create_schema_data: PhraseCreateSchema, scene_file_path: str
) -> PhraseUpdateSchema:
    return PhraseUpdateSchema(
        **phrase_create_schema_data.model_dump(),
        scene_s3_key=scene_file_path,
    )


@pytest.fixture
def phrase_model_data(
    phrase_update_schema_data: PhraseUpdateSchema,
    random_phrase_id: uuid.UUID,
):
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
    phrase = await create_phrase(phrase_model_data)

    return phrase


@pytest.fixture
def phrase_schema_data(
    phrase_fixture: PhraseModel,
) -> PhraseSchema:
    phrase = PhraseSchema(**phrase_fixture.__dict__)

    return phrase


@pytest.fixture
def check_phrase_exists() -> Callable[[bool], None]:
    def _raise_exception(exists: bool):
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


@pytest.fixture
def s3_service() -> S3Service:
    return S3Service()


@pytest.fixture
def mock_s3_service() -> mock.AsyncMock:
    return mock.AsyncMock()


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


@pytest.fixture
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


@pytest.fixture
def mock_scenes_upload_service() -> mock.AsyncMock:
    return mock.AsyncMock()


@pytest.fixture
def subtitle_file() -> UploadFile:
    with open("app/tests/data/subtitles.srt", "rb") as f:
        _file = UploadFile(
            file=io.BytesIO(f.read()),
            filename="subtitles.srt",
            size=69,
            headers={"Content-Type": "text/plain"},
        )

    return _file


@pytest.fixture
def movie_file() -> UploadFile:
    with open("app/tests/data/movie.mp4", "rb") as f:
        _file = UploadFile(
            file=io.BytesIO(f.read()),
            filename="movie.mp4",
            size=1055736,
            headers={"Content-Type": "video/mp4"},
        )

    return _file


@pytest.fixture
def subtitle_item() -> SubtitleItem:
    return SubtitleItem(
        start_time=datetime.timedelta(seconds=30),
        end_time=datetime.timedelta(seconds=40),
        text="fruits: apples, bananas and oranges",
        normalized_text="fruits apples bananas and oranges",
    )


@pytest.fixture
def scene_file_buffered_bytes() -> io.BytesIO:
    with open("app/tests/data/scene.mp4", "rb") as f:
        return io.BytesIO(f.read())


"""
###############################################################################
[END] Scenes-upload-service fixtures
###############################################################################
"""
