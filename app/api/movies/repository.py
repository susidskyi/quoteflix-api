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
        query = select(MovieModel).where(MovieModel.id == movie_id)
        movie = await self.session.scalar(query)

        if not movie:
            raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

        return movie

    async def create(self, data: MovieCreateSchema) -> MovieModel:
        movie = MovieModel(**data.model_dump())

        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)

        return movie

    async def get_all(self) -> Sequence[MovieModel]:
        movies = await self.session.scalars(select(MovieModel))

        return movies.all()

    async def update(self, movie_id: uuid.UUID, data: MovieUpdateSchema) -> MovieModel:
        query = select(MovieModel).where(MovieModel.id == movie_id)
        movie = await self.session.scalar(query)

        if not movie:
            raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

        for field, value in data.model_dump().items():
            setattr(movie, field, value)

        await self.session.commit()
        await self.session.refresh(movie)

        return movie

    async def delete(self, movie_id: uuid.UUID) -> None:
        if not await self.exists(movie_id):
            raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

        query = delete(MovieModel).where(MovieModel.id == movie_id)

        await self.session.execute(query)
        await self.session.commit()

    async def exists(self, movie_id: uuid.UUID) -> bool:
        query = select(exists().where(MovieModel.id == movie_id))

        return await self.session.scalar(query)

    async def update_status(self, movie_id: uuid.UUID, status: MovieStatus) -> None:
        if not await self.exists(movie_id):
            raise RepositoryNotFoundError(f"Movie not found: id={movie_id}")

        query = (
            update(MovieModel).where(MovieModel.id == movie_id).values(status=status)
        )
        await self.session.execute(query)

        await self.session.commit()
