from fastapi.routing import APIRouter
import uuid
from fastapi import Depends, Request, UploadFile, Form, File
from typing import Sequence, Annotated
from app.api.movies.schemas import MovieSchema
from app.api.movies.models import MovieModel
from app.api.movies.constants import MovieStatus, Languages
from app.api.movies.service import MovieService

from app.api.movies.dependencies import get_movie_service

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", name="movies:get-all-movies", response_model=Sequence[MovieSchema])
async def list(
    request: Request, movie_service: MovieService = Depends(get_movie_service)
) -> Sequence[MovieSchema]:
    movies = await movie_service.list()

    return [movie for movie in movies]


@router.post("/", name="movies:create-movie", response_model=MovieSchema)
async def create(
    request: Request,
    title: str = Form(),
    year: int = Form(),
    language: Languages = Form(),
    is_active: bool = Form(default=False),
    status: MovieStatus = Form(default=MovieStatus.PENDING),
    subtitles_file: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
    movie_service: MovieService = Depends(get_movie_service),
) -> MovieSchema:
    """
    TODO: Investigate if payload validation can be done with pydantic
    """
    movie = MovieModel.Create(
        title=title,
        year=year,
        language=language,
        is_active=is_active,
        status=status,
        subtitles_file=subtitles_file,
        file=file,
    )
    movie = await movie_service.create(movie)

    return movie


"""
@router.patch("/{movie_id}", name="movies:update-movie", response_model=MovieSchema)
async def patch(
    request: Request,
    movie_id: uuid.UUID,
    title: str | None = Form(default=None),
    year: int | None = Form(default=None),
    language: Languages | None = Form(default=None),
    is_active: bool | None = Form(default=None),
    status: MovieStatus | None = Form(default=None),
    subtitles_file: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
    movie_service: MovieService = Depends(get_movie_service),
) -> MovieSchema:
    movie = MovieModel.Update(
        title=title,
        year=year,
        language=language,
        is_active=is_active,
        status=status,
        subtitles_file=subtitles_file,
        file=file,
    )

    movie = await movie_service.update(movie_id, movie)

    return movie
"""
