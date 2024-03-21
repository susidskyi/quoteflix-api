import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.movies.models import MovieModel


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    async def create(self, data: MovieModel.Create) -> MovieModel:
        movie = MovieModel(**data.model_dump())
        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)
        return movie

    async def list(self) -> Sequence[MovieModel]:
        return await self.session.scalars(select(MovieModel))

    async def update(self, movie_id: uuid.UUID, data: MovieModel.Update) -> MovieModel:
        stmt = select(MovieModel).where(MovieModel.id == movie_id)
        movie = await self.session.scalar(stmt)

        if movie is None:
            return None

        print(movie.model_dump(exclude_unset=True))

        raise Exception
