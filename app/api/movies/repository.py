import uuid
from typing import Sequence

from sqlalchemy import delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.movies.models import MovieModel
from app.api.movies.schemas import MovieCreateSchema, MovieUpdateSchema
from app.core.constants import MovieStatus
from app.core.exceptions import RepositoryNotFoundError


class MoviesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_by_id(self, movie_id: uuid.UUID) -> MovieModel:
        async with self.session as session:
            query = select(MovieModel).where(MovieModel.id == movie_id)
            movie = await session.scalar(query)

            if not movie:
                raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

            return movie

    async def create(self, data: MovieCreateSchema) -> MovieModel:
        async with self.session as session:
            movie = MovieModel(**data.model_dump())

            session.add(movie)
            await session.commit()
            await session.refresh(movie)

            return movie

    async def get_all(self) -> Sequence[MovieModel]:
        async with self.session as session:
            movies = await session.scalars(select(MovieModel))

            return movies.all()

    async def update(self, movie_id: uuid.UUID, data: MovieUpdateSchema) -> MovieModel:
        async with self.session as session:
            query = select(MovieModel).where(MovieModel.id == movie_id)
            movie = await session.scalar(query)

            if not movie:
                raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

            for field, value in data.model_dump().items():
                setattr(movie, field, value)

            await session.commit()
            await session.refresh(movie)

            return movie

    async def delete(self, movie_id: uuid.UUID) -> None:
        if not await self.exists(movie_id):
            raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

        async with self.session as session:
            query = delete(MovieModel).where(MovieModel.id == movie_id)

            await session.execute(query)
            await session.commit()

    async def exists(self, movie_id: uuid.UUID) -> bool:
        async with self.session as session:
            query = select(exists().where(MovieModel.id == movie_id))

            result = await session.scalar(query)

            return bool(result)

    async def update_status(self, movie_id: uuid.UUID, status: MovieStatus) -> None:
        async with self.session as session:
            if not await self.exists(movie_id):
                raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

            query = update(MovieModel).where(MovieModel.id == movie_id).values(status=status)
            await session.execute(query)

            await session.commit()
