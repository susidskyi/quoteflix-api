import uuid
from typing import Sequence

from fastapi import Depends, status
from fastapi.routing import APIRouter

from app.api.movies.dependencies import get_movie_service, movie_exists
from app.api.movies.schemas import (
    MovieCreateSchema,
    MovieSchema,
    MovieUpdateSchema,
)
from app.api.movies.service import MoviesService
from app.api.users.permissions import current_superuser

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", name="movies:get-all-movies", response_model=Sequence[MovieSchema])
async def get_all(
    movie_service: MoviesService = Depends(get_movie_service),
) -> Sequence[MovieSchema]:
    movies = await movie_service.get_all()

    return [movie for movie in movies]


@router.post(
    "/",
    name="movies:create-movie",
    response_model=MovieSchema,
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    payload: MovieCreateSchema = Depends(MovieCreateSchema.depends),
    movie_service: MoviesService = Depends(get_movie_service),
) -> MovieSchema:
    movie = await movie_service.create(payload)

    return movie


@router.put(
    "/{movie_id}",
    name="movies:update-movie",
    response_model=MovieSchema,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def update(
    movie_id: uuid.UUID,
    payload: MovieUpdateSchema = Depends(MovieUpdateSchema.depends),
    movie_service: MoviesService = Depends(get_movie_service),
):
    movie = await movie_service.update(movie_id, payload)

    return movie


@router.get(
    "/{movie_id}",
    name="movies:get-movie-by-id",
    response_model=MovieSchema,
    dependencies=[Depends(movie_exists)],
)
async def get_movie_by_id(
    movie_id: uuid.UUID, movie_service: MoviesService = Depends(get_movie_service)
) -> MovieSchema:
    movie = await movie_service.get_by_id(movie_id)

    return movie


@router.delete(
    "/{movie_id}",
    name="movies:delete-movie",
    status_code=204,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def delete_movie(
    movie_id: uuid.UUID, movie_service: MoviesService = Depends(get_movie_service)
):
    await movie_service.delete(movie_id)

    return {"success": True}
