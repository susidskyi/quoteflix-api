import uuid

import pytest

from app.api.movies.models import MovieModel
from app.api.movies.repository import MoviesRepository
from app.api.movies.schemas import MovieCreateSchema
from app.core.exceptions import RepositoryNotFoundError


@pytest.mark.asyncio
class TestMoviesRepository:
    async def test_get_all_movies(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_fixture: MovieModel,
    ):
        movies = await movies_repository.get_all()

        assert len(movies) == 1
        assert movie_active_without_files_fixture in movies

    async def test_get_movie_by_id(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_fixture: MovieModel,
    ):
        movie = await movies_repository.get_by_id(movie_active_without_files_fixture.id)

        assert movie == movie_active_without_files_fixture

    async def test_get_movie_by_id_not_found(
        self, movies_repository: MoviesRepository, random_movie_id: uuid.UUID
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.get_by_id(random_movie_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]

    async def test_update_movie(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_fixture: MovieModel,
        movie_active_without_files_data: MovieCreateSchema,
    ):
        new_title = "New title"
        new_movie_data = movie_active_without_files_data.model_copy()
        new_movie_data.title = new_title

        movie = await movies_repository.update(
            movie_active_without_files_fixture.id, new_movie_data
        )

        assert movie.id == movie_active_without_files_fixture.id
        assert movie.title == new_title

    async def test_update_movie_not_found(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_data: MovieCreateSchema,
        random_movie_id: uuid.UUID,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.update(
                random_movie_id, movie_active_without_files_data
            )

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]

    async def test_exists(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_fixture: MovieModel,
    ):
        exists = await movies_repository.exists(movie_active_without_files_fixture.id)

        assert exists is True

    async def test_does_not_exist(
        self, movies_repository: MoviesRepository, random_movie_id: uuid.UUID
    ):
        exists = await movies_repository.exists(random_movie_id)

        assert exists is False

    async def test_delete(
        self,
        movies_repository: MoviesRepository,
        movie_active_without_files_fixture: MovieModel,
    ):
        movie_id = movie_active_without_files_fixture.id

        exists = await movies_repository.exists(movie_id)
        assert exists is True

        await movies_repository.delete(movie_id)
        exists = await movies_repository.exists(movie_id)
        assert exists is False

    async def test_delete_not_found(
        self, movies_repository: MoviesRepository, random_movie_id: uuid.UUID
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await movies_repository.delete(random_movie_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_movie_id) in excinfo.value.args[0]
