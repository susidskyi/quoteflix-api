import uuid

import pytest

from app.api.phrases.models import PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import PhraseCreateSchema, PhraseUpdateSchema
from app.core.exceptions import RepositoryNotFoundError


@pytest.mark.asyncio
class TestPhrasesRepository:
    async def test_get_all(
        self, phrases_repository: PhrasesRepository, phrase_fixture: PhraseModel
    ):
        result = await phrases_repository.get_all()

        assert len(result) == 1
        assert phrase_fixture in result

    async def test_get_by_id(
        self, phrases_repository: PhrasesRepository, phrase_fixture: PhraseModel
    ):
        result = await phrases_repository.get_by_id(phrase_fixture.id)

        assert result == phrase_fixture

    async def test_get_by_id_not_found(
        self, phrases_repository: PhrasesRepository, random_phrase_id: uuid.UUID
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await phrases_repository.get_by_id(random_phrase_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_phrase_id) in excinfo.value.args[0]

    async def test_exists(
        self, phrase_fixture: PhraseModel, phrases_repository: PhrasesRepository
    ):
        result = await phrases_repository.exists(phrase_fixture.id)

        assert result is True

    async def test_does_not_exist(
        self, random_phrase_id: uuid.UUID, phrases_repository: PhrasesRepository
    ):
        result = await phrases_repository.exists(random_phrase_id)

        assert result is False

    async def test_delete(
        self, phrase_fixture: PhraseModel, phrases_repository: PhrasesRepository
    ):
        await phrases_repository.delete(phrase_fixture.id)

        result = await phrases_repository.exists(phrase_fixture.id)

        assert result is False

    async def test_delete_not_found(
        self, phrases_repository: PhrasesRepository, random_phrase_id: uuid.UUID
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await phrases_repository.delete(random_phrase_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_phrase_id) in excinfo.value.args[0]

    async def test_update(
        self,
        phrase_fixture: PhraseModel,
        phrases_repository: PhrasesRepository,
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        result = await phrases_repository.update(
            phrase_fixture.id, phrase_update_schema_data
        )

        assert result.id == phrase_fixture.id
        assert result.file_s3_key == phrase_update_schema_data.file_s3_key

    async def test_update_not_found(
        self,
        phrases_repository: PhrasesRepository,
        random_phrase_id: uuid.UUID,
        phrase_update_schema_data: PhraseUpdateSchema,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await phrases_repository.update(random_phrase_id, phrase_update_schema_data)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_phrase_id) in excinfo.value.args[0]

    async def test_create(
        self,
        phrases_repository: PhrasesRepository,
        phrase_create_schema_data: PhraseCreateSchema,
    ):
        result = await phrases_repository.create(phrase_create_schema_data)

        assert await phrases_repository.exists(result.id) is True
