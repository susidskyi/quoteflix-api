import uuid
from typing import Sequence

from fastapi import BackgroundTasks, Depends, status
from fastapi.routing import APIRouter

from app.api.movies.dependencies import get_movies_service, movie_exists
from app.api.movies.models import MovieModel
from app.api.movies.schemas import (
    MovieCreateSchema,
    MovieSchema,
    MovieUpdateSchema,
    MovieUpdateStatusSchema,
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
    movies_service: MoviesService = Depends(get_movies_service),
) -> Sequence[MovieModel]:
    return await movies_service.get_all()


@router.post(
    "/",
    name="movies:create-movie",
    response_model=MovieSchema,
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    payload: MovieCreateSchema,
    movies_service: MoviesService = Depends(get_movies_service),
) -> MovieModel:
    return await movies_service.create(payload)


@router.put(
    "/{movie_id}",
    name="movies:update-movie",
    response_model=MovieSchema,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def update(
    movie_id: uuid.UUID,
    payload: MovieUpdateSchema,
    movies_service: MoviesService = Depends(get_movies_service),
) -> MovieModel:
    return await movies_service.update(movie_id, payload)


@router.get(
    "/{movie_id}",
    name="movies:get-movie-by-id",
    response_model=MovieSchema,
    dependencies=[Depends(movie_exists)],
)
async def get_movie_by_id(
    movie_id: uuid.UUID,
    movies_service: MoviesService = Depends(get_movies_service),
) -> MovieModel:
    return await movies_service.get_by_id(movie_id)


@router.delete(
    "/{movie_id}",
    name="movies:delete-movie",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def delete_movie(
    movie_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    movies_service: MoviesService = Depends(get_movies_service),
) -> None:
    await movies_service.delete(movie_id, background_tasks)


@router.patch(
    "/{movie_id}/update-status",
    name="movies:update-movie-status",
    dependencies=[Depends(movie_exists), Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_status(
    movie_id: uuid.UUID,
    new_status_schema: MovieUpdateStatusSchema,
    movies_service: MoviesService = Depends(get_movies_service),
) -> None:
    await movies_service.update_status(movie_id, new_status_schema.status)
