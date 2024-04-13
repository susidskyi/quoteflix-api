import uuid

import pytest

from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieUpdateSchema
from app.core.constants import MovieStatus
from app.core.exceptions import RepositoryNotFoundError


@pytest.mark.asyncio()
class TestMoviesRepository:
    async def test_get_all_movies(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
    ):
        result = await movies_repository.get_all()

        assert len(result) == 1
        assert movie_fixture in result

    async def test_get_movie_by_id(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
    ):
        result = await movies_repository.get_by_id(movie_fixture.id)

        assert result == movie_fixture

    async def test_get_movie_by_id_not_found(
        self,
        movies_repository: MoviesRepository,
        random_movie_id: uuid.UUID,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.get_by_id(random_movie_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]

    async def test_update_movie(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
        movie_update_schema_data: MovieUpdateSchema,
    ):
        result = await movies_repository.update(
            movie_fixture.id,
            movie_update_schema_data,
        )

        assert result.id == movie_fixture.id
        assert result.title == movie_fixture.title

    async def test_update_movie_not_found(
        self,
        movies_repository: MoviesRepository,
        movie_update_schema_data: MovieUpdateSchema,
        random_movie_id: uuid.UUID,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.update(random_movie_id, movie_update_schema_data)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]

    async def test_exists(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
    ):
        result = await movies_repository.exists(movie_fixture.id)

        assert result is True

    async def test_does_not_exist(
        self,
        movies_repository: MoviesRepository,
        random_movie_id: uuid.UUID,
    ):
        result = await movies_repository.exists(random_movie_id)

        assert result is False

    async def test_delete(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
    ):
        movie_id = movie_fixture.id

        result = await movies_repository.exists(movie_id)
        assert result is True

        await movies_repository.delete(movie_id)
        result = await movies_repository.exists(movie_id)
        assert result is False

    async def test_delete_not_found(
        self,
        movies_repository: MoviesRepository,
        random_movie_id: uuid.UUID,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.delete(random_movie_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]

    async def test_update_status(
        self,
        movies_repository: MoviesRepository,
        movie_fixture: MovieModel,
        random_movie_id: uuid.UUID,
    ):
        assert movie_fixture.status == MovieStatus.PENDING

        await movies_repository.update_status(random_movie_id, MovieStatus.ERROR)

        result = await movies_repository.get_by_id(random_movie_id)

        assert result.status == MovieStatus.ERROR
