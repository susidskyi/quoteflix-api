import uuid

import pytest

from app.api.movies.models import MovieModel
from app.api.phrases.models import PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import PhraseCreateSchema, PhraseTransferSchema, PhraseUpdateSchema
from app.api.phrases.utils import normalize_phrase_text
from app.core.exceptions import RepositoryNotFoundError


@pytest.mark.asyncio()
class TestPhrasesRepository:
    async def test_get_all(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
    ):
        result = await phrases_repository.get_all()

        assert len(result) == 1
        assert phrase_fixture in result

    async def test_get_by_id(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
    ):
        result = await phrases_repository.get_by_id(phrase_fixture.id)

        assert result == phrase_fixture

    async def test_get_by_id_not_found(
        self,
        phrases_repository: PhrasesRepository,
        random_phrase_id: uuid.UUID,
    ):
        with pytest.raises(RepositoryNotFoundError) as excinfo:
            await phrases_repository.get_by_id(random_phrase_id)

        assert excinfo.type is RepositoryNotFoundError
        assert str(random_phrase_id) in excinfo.value.args[0]

    async def test_exists(
        self,
        phrase_fixture: PhraseModel,
        phrases_repository: PhrasesRepository,
    ):
        result = await phrases_repository.exists(phrase_fixture.id)

        assert result is True

    async def test_does_not_exist(
        self,
        random_phrase_id: uuid.UUID,
        phrases_repository: PhrasesRepository,
    ):
        result = await phrases_repository.exists(random_phrase_id)

        assert result is False

    async def test_delete(
        self,
        phrase_fixture: PhraseModel,
        phrases_repository: PhrasesRepository,
        scene_s3_key: str,
    ):
        exists = await phrases_repository.exists(phrase_fixture.id)
        assert exists is True

        result = await phrases_repository.delete(phrase_fixture.id)

        assert result == scene_s3_key
        exists = await phrases_repository.exists(phrase_fixture.id)
        assert exists is False

    async def test_delete_not_found(
        self,
        phrases_repository: PhrasesRepository,
        random_phrase_id: uuid.UUID,
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
            phrase_fixture.id,
            phrase_update_schema_data,
        )

        assert result.id == phrase_fixture.id
        assert result.scene_s3_key == phrase_update_schema_data.scene_s3_key

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
        movie_fixture: MovieModel,
    ):
        result = await phrases_repository.create(phrase_create_schema_data)

        assert await phrases_repository.exists(result.id) is True

    async def test_get_by_movie_id(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
    ):
        result = await phrases_repository.get_by_movie_id(phrase_fixture.movie_id)

        assert len(result) == 1
        assert phrase_fixture in result

    async def test_bulk_create(
        self,
        phrases_repository: PhrasesRepository,
        phrase_create_schema_data: PhraseCreateSchema,
        movie_fixture: MovieModel,
    ):
        result = await phrases_repository.bulk_create(
            [phrase_create_schema_data, phrase_create_schema_data],
        )

        all_phrases_in_db = await phrases_repository.get_all()

        assert len(all_phrases_in_db) == 2
        assert len(result) == 2

    @pytest.mark.parametrize(
        ("search_text", "expected_count"),
        [
            ("fruits: apples, bananas and oranges", 1),
            ("fru'its", 1),
            ("invalid string", 0),
        ],
    )
    async def test_get_by_search_text(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        search_text: str,
        expected_count: int,
    ):
        normalized_text = normalize_phrase_text(search_text)
        result = await phrases_repository.get_by_search_text(normalized_text)

        assert len(result) == expected_count

    async def test_delete_by_movie_id(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        random_movie_id: uuid.UUID,
    ):
        existing_phrases = await phrases_repository.get_by_movie_id(random_movie_id)
        assert len(existing_phrases) == 1

        await phrases_repository.delete_by_movie_id(phrase_fixture.movie_id)

        existing_phrases = await phrases_repository.get_by_movie_id(
            phrase_fixture.movie_id,
        )
        assert len(existing_phrases) == 0

    async def test_import_from_json(
        self,
        random_movie_id: uuid.UUID,
        phrases_repository: PhrasesRepository,
        movie_fixture: MovieModel,
        phrase_transfer_schema_data: PhraseTransferSchema,
    ):
        await phrases_repository.import_from_json(random_movie_id, [phrase_transfer_schema_data])

        result = await phrases_repository.get_by_movie_id(random_movie_id)

        assert len(result) == 1
        assert result[0].movie_id == random_movie_id
        assert result[0].scene_s3_key == phrase_transfer_schema_data.scene_s3_key
        assert result[0].end_in_movie == phrase_transfer_schema_data.end_in_movie
        assert result[0].start_in_movie == phrase_transfer_schema_data.start_in_movie
        assert result[0].normalized_text == phrase_transfer_schema_data.normalized_text
