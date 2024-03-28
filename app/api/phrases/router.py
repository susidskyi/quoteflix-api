import uuid
from typing import Sequence

from fastapi import Depends
from fastapi.routing import APIRouter

from app.api.phrases.dependencies import get_phrases_service, phrase_exists
from app.api.phrases.schemas import PhraseCreateSchema, PhraseSchema, PhraseUpdateSchema
from app.api.phrases.service import PhrasesService
from app.api.users.permissions import current_superuser

router = APIRouter(prefix="/phrases", tags=["phrases"])


@router.get(
    "/",
    name="phrases:get-all-phrases",
    dependencies=[Depends(current_superuser)],
    response_model=Sequence[PhraseSchema],
)
async def get_all_phrases(
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> Sequence[PhraseSchema]:
    phrases = await phrases_service.get_all()

    return [phrase for phrase in phrases]


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
):
    phrase = await phrases_service.get_by_id(phrase_id)

    return phrase


@router.post(
    "/",
    name="phrases:create-phrase",
    response_model=PhraseSchema,
    status_code=201,
    dependencies=[Depends(current_superuser)],
)
async def create_phrase(
    payload: PhraseCreateSchema,
    phrases_service: PhrasesService = Depends(get_phrases_service),
):
    phrase = await phrases_service.create(payload)

    return phrase


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
):
    phrase = await phrases_service.update(phrase_id, payload)

    return phrase


@router.delete(
    "/{phrase_id}",
    name="phrases:delete-phrase",
    status_code=204,
    dependencies=[Depends(current_superuser), Depends(phrase_exists)],
)
async def delete_phrase(
    phrase_id: uuid.UUID,
    phrases_service: PhrasesService = Depends(get_phrases_service),
) -> None:
    await phrases_service.delete(phrase_id)
