import uuid
from typing import Sequence

from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.movies.models import MovieModel


class MoviesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def get_by_id(self, movie_id: uuid.UUID) -> MovieModel:
        query = select(MovieModel).where(MovieModel.id == movie_id)
        return await self.session.scalar(query)

    async def create(self, data: MovieModel.Create) -> MovieModel:
        movie = MovieModel(**data.model_dump())
        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)

        return movie

    async def list(self) -> Sequence[MovieModel]:
        return await self.session.scalars(select(MovieModel))

    async def update(self, movie_id: uuid.UUID, data: MovieModel.Update) -> MovieModel:
        query = select(MovieModel).where(MovieModel.id == movie_id)
        movie = await self.session.scalar(query)

        for field, value in data.model_dump().items():
            setattr(movie, field, value)

        await self.session.commit()
        await self.session.refresh(movie)

        return movie

    async def delete(self, movie_id: uuid.UUID) -> None:
        query = delete(MovieModel).where(MovieModel.id == movie_id)
        await self.session.execute(query)
        await self.session.commit()

    async def exists(self, movie_id: uuid.UUID) -> bool:
        query = select(exists().where(MovieModel.id == movie_id))
        return await self.session.scalar(query)
