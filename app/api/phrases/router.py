import uuid
from typing import Sequence

from fastapi import Depends, Query, status
from fastapi.routing import APIRouter
from fastapi_cache.decorator import cache
from typing_extensions import Annotated

from app.api.movies.dependencies import movie_exists
from app.api.phrases.dependencies import (
    get_phrases_service,
    get_scenes_upload_service,
    phrase_exists,
)
from app.api.phrases.models import PhraseModel
from app.api.phrases.scenes_upload_service import ScenesUploadService
from app.api.phrases.schemas import (
    PhraseBySearchTextSchema,
    PhraseCreateFromMovieFilesSchema,
    PhraseCreateSchema,
    PhraseSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.api.phrases.service import PhrasesService
from app.api.users.permissions import current_superuser
from app.core.cache_key_builder import key_builder_phrase_search_by_text

router = APIRouter(prefix="/phrases", tags=["phrases"])


@router.get(
    "/",
    name="phrases:get-all-phrases",
    dependencies=[Depends(current_superuser)],
    response_model=Sequence[PhraseSchema],
)
async def get_all_phrases(
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> Sequence[PhraseModel]:
    return await phrases_service.get_all()


@router.get(
    "/get-by-search-text",
    name="phrases:get-phrases-by-search-text",
    response_model=Sequence[PhraseBySearchTextSchema],
    status_code=status.HTTP_200_OK,
)
@cache(expire=1800, key_builder=key_builder_phrase_search_by_text)
async def get_phrases_by_search_text(
    search_text: Annotated[str, Query(min_length=1)],
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> Sequence[PhraseBySearchTextSchema]:
    """
    If dependencies are changed, make sure `key_builder_phrase_search_by_text`
    workds correctly. It had to be created because of issue: https://github.com/long2ice/fastapi-cache/issues/279
    """
    return await phrases_service.get_by_search_text(search_text)


@router.get(
    "/get-by-movie-id/{movie_id}",
    name="phrases:get-phrases-by-movie-id",
    response_model=Sequence[PhraseSchema],
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def get_phrases_by_movie_id(
    movie_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> Sequence[PhraseModel]:
    return await phrases_service.get_by_movie_id(movie_id)


@router.delete(
    "/delete-by-movie-id/{movie_id}",
    name="phrases:delete-phrases-by-movie-id",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def delete_phrases_by_movie_id(
    movie_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    await phrases_service.delete_by_movie_id(movie_id)


@router.get(
    "/{phrase_id}",
    name="phrases:get-phrase-by-id",
    response_model=PhraseSchema,
    dependencies=[
        Depends(phrase_exists),
    ],
)
async def get_phrase_by_id(
    phrase_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> PhraseModel:
    return await phrases_service.get_by_id(phrase_id)


@router.post(
    "/",
    name="phrases:create-phrase",
    response_model=PhraseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
)
async def create_phrase(
    payload: PhraseCreateSchema,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> PhraseModel:
    return await phrases_service.create(payload)


@router.put(
    "/{phrase_id}",
    name="phrases:update-phrase",
    response_model=PhraseSchema,
    dependencies=[Depends(current_superuser), Depends(phrase_exists)],
)
async def update_phrase(
    phrase_id: uuid.UUID,
    payload: PhraseUpdateSchema,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> PhraseModel:
    return await phrases_service.update(phrase_id, payload)


@router.delete(
    "/{phrase_id}",
    name="phrases:delete-phrase",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser), Depends(phrase_exists)],
)
async def delete_phrase(
    phrase_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    await phrases_service.delete(phrase_id)


@router.post(
    "/create-from-movie-files/{movie_id}",
    name="phrases:create-phrases-from-movie-files",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(movie_exists), Depends(current_superuser)],
)
async def create_phrases_from_movie_files(
    movie_id: uuid.UUID,
    movie_files: PhraseCreateFromMovieFilesSchema = Depends(
        PhraseCreateFromMovieFilesSchema.depends,
    ),
    scenes_upload_service: ScenesUploadService = Depends(get_scenes_upload_service),
) -> None:
    """
    Actually need to await the upload and process files
    Because FastAPI has oppened issues to process large files (UploadFile) in Background Tasks
    https://github.com/tiangolo/fastapi/issues/10857
    When it's resolved, this will be rewritten to `background_tasks.add_task`
    """
    await scenes_upload_service.upload_and_process_files(
        movie_id=movie_id,
        movie_file=movie_files.movie_file,
        subtitle_file=movie_files.subtitles_file,
    )


@router.get(
    "/export-to-json/{movie_id}",
    name="phrases:export-phrases-to-json",
    response_model=Sequence[PhraseTransferSchema],
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def export_phrases_to_json(
    movie_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> Sequence[PhraseTransferSchema]:
    return await phrases_service.export_to_json(movie_id)


@router.post(
    "/import-from-json/{movie_id}",
    name="phrases:import-phrases-from-json",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(current_superuser), Depends(movie_exists)],
)
async def import_phrases_from_json(
    movie_id: uuid.UUID,
    payload: Sequence[PhraseTransferSchema],
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    await phrases_service.import_from_json(movie_id, payload)
