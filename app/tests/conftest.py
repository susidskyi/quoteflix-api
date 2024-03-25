import uuid
from typing import AsyncGenerator, AsyncIterator, Callable
from unittest import mock

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.movies.constants import Languages, MovieStatus
from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieCreateSchema
from app.api.movies.service import MoviesService
from app.api.users.models import UserModel
from app.core.config import settings
from app.core.models import BaseModel
from app.main import app as main_app


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


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return main_app


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


@pytest.fixture()
def current_superuser_fixture(user: UserModel):
    def _current_superuser() -> UserModel:
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return user

    return _current_superuser


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver.tst"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def create_movie(db: AsyncSession) -> Callable[[MovieCreateSchema], MovieModel]:
    async def _create_movie(data: MovieCreateSchema) -> MovieModel:
        movie = MovieModel(**data.model_dump())

        db.add(movie)
        await db.commit()
        await db.refresh(movie)

        return movie

    return _create_movie


@pytest.fixture
def movie_active_without_files_data() -> MovieCreateSchema:
    movie = MovieCreateSchema(
        title="Test",
        year=2000,
        status=MovieStatus.PENDING,
        language=Languages.EN,
    )

    return movie


@pytest_asyncio.fixture
async def movie_active_without_files_fixture(
    create_movie: Callable[[MovieCreateSchema], MovieModel],
    movie_active_without_files_data: MovieCreateSchema,
) -> MovieModel:
    movie = await create_movie(movie_active_without_files_data)

    return movie


@pytest.fixture
def random_movie_id() -> uuid.UUID:
    return uuid.uuid4()
