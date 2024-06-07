import uuid

import pytest

from app.api.movies.models import MovieModel
from app.api.phrases.models import PhraseIssueModel, PhraseModel
from app.api.phrases.repository import PhrasesRepository
from app.api.phrases.schemas import (
    PhraseCreateSchema,
    PhraseIssueCreateSchema,
    PhraseTransferSchema,
    PhraseUpdateSchema,
)
from app.api.phrases.utils import normalize_phrase_text
from app.core.config import settings
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

    @pytest.mark.parametrize(
        ("has_issues", "expected_result_len"),
        [
            (False, 0),
            (True, 1),
        ],
    )
    async def test_get_for_export_has_issues(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        phrase_issue_fixture: PhraseIssueModel,
        has_issues: bool,
        expected_result_len: int,
        random_movie_id: uuid.UUID,
    ):
        result = await phrases_repository.get_for_export(random_movie_id, has_issues)

        assert len(result) == expected_result_len

    @pytest.mark.parametrize(
        ("has_issues", "expected_result_len"),
        [
            (False, 1),
            (True, 0),
        ],
    )
    async def test_get_for_export_has_no_issues(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        has_issues: bool,
        expected_result_len: int,
        random_movie_id: uuid.UUID,
    ):
        result = await phrases_repository.get_for_export(random_movie_id, has_issues)

        assert len(result) == expected_result_len

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

    async def test_pagination_get_by_search_phrase(
        self,
        phrases_repository: PhrasesRepository,
        movie_fixture: MovieModel,
        phrase_create_schema_data: PhraseCreateSchema,
    ):
        valid_search_text = normalize_phrase_text("fruits")
        created_phrases = []
        number_of_phrases = 7

        for _ in range(number_of_phrases):
            phrase = await phrases_repository.create(phrase_create_schema_data)
            created_phrases.append(phrase)

        result_page_1 = await phrases_repository.get_by_search_text(
            valid_search_text,
            page=1,
        )
        assert len(result_page_1.items) == 3
        assert [x.id for x in result_page_1.items] == [x.id for x in created_phrases[:3]]
        assert result_page_1.total == number_of_phrases
        assert result_page_1.size == settings.phrases_page_size
        assert result_page_1.page == 1
        assert result_page_1.pages == 3

        result_page_2 = await phrases_repository.get_by_search_text(
            valid_search_text,
            page=2,
        )
        assert len(result_page_2.items) == 3
        assert [x.id for x in result_page_2.items] == [x.id for x in created_phrases[3:6]]
        assert result_page_2.total == number_of_phrases
        assert result_page_2.size == settings.phrases_page_size
        assert result_page_2.page == 2
        assert result_page_2.pages == 3

        result_page_3 = await phrases_repository.get_by_search_text(
            valid_search_text,
            page=3,
        )
        assert len(result_page_3.items) == 1
        assert [x.id for x in result_page_3.items] == [x.id for x in created_phrases[6:7]]
        assert result_page_3.total == number_of_phrases
        assert result_page_3.size == settings.phrases_page_size
        assert result_page_3.page == 3
        assert result_page_3.pages == 3

    @pytest.mark.parametrize(
        ("search_text", "expected_count"),
        [
            ("fruits: apples, bananas and oranges", 1),
            ("fruits", 1),
            ("invalid string", 0),
        ],
    )
    async def test_get_by_search_phrases(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        search_text: str,
        expected_count: int,
    ):
        result = await phrases_repository.get_by_search_text(
            search_text=normalize_phrase_text(search_text),
            page=1,
        )

        assert len(result.items) == expected_count

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

    async def test_create_phrase_issue_ok(
        self,
        phrases_repository: PhrasesRepository,
        phrase_fixture: PhraseModel,
        phrase_issue_create_schema_data: PhraseIssueCreateSchema,
    ):
        await phrases_repository.create_issue(phrase_issue_create_schema_data)

        all_issues = await phrases_repository.get_all_issues()

        assert len(all_issues) == 1
        assert all_issues[0].phrase_id == phrase_issue_create_schema_data.phrase_id
        assert all_issues[0].issuer_ip == phrase_issue_create_schema_data.issuer_ip

        # Check if the same issue was not created
        await phrases_repository.create_issue(phrase_issue_create_schema_data)

        assert len(all_issues) == 1
        assert all_issues[0].phrase_id == phrase_issue_create_schema_data.phrase_id
        assert all_issues[0].issuer_ip == phrase_issue_create_schema_data.issuer_ip

    async def test_get_all_issues(
        self,
        phrases_repository: PhrasesRepository,
        phrase_issue_fixture: PhraseIssueModel,
        phrase_issue_model_data: PhraseIssueModel,
    ):
        all_issues = await phrases_repository.get_all_issues()

        assert [phrase_issue_model_data] == all_issues

    async def test_get_issues_by_phrase_id(
        self,
        phrases_repository: PhrasesRepository,
        phrase_issue_fixture: PhraseIssueModel,
        phrase_issue_model_data: PhraseIssueModel,
        random_phrase_id: uuid.UUID,
    ):
        phrase_issues = await phrases_repository.get_issues_by_phrase_id(random_phrase_id)

        assert phrase_issues == [phrase_issue_model_data]

    async def test_delete_issue(
        self,
        phrases_repository: PhrasesRepository,
        phrase_issue_fixture: PhraseIssueModel,
        random_phrase_issue_id: uuid.UUID,
    ):
        existing_issues = await phrases_repository.get_all_issues()
        assert len(existing_issues) == 1

        await phrases_repository.delete_issue(random_phrase_issue_id)
        existing_issues = await phrases_repository.get_all_issues()
        assert len(existing_issues) == 0

    async def test_issue_exists(
        self,
        phrases_repository: PhrasesRepository,
        phrase_issue_fixture: PhraseIssueModel,
        random_phrase_issue_id: uuid.UUID,
    ):
        exists = await phrases_repository.issue_exists(random_phrase_issue_id)
        assert exists is True

        invalid_uuid = uuid.uuid4()
        exists = await phrases_repository.issue_exists(invalid_uuid)
        assert exists is False

    async def test_delete_issues_by_phrase_id(
        self,
        phrases_repository: PhrasesRepository,
        phrase_issue_fixture: PhraseIssueModel,
        random_phrase_id: uuid.UUID,
    ):
        existing_issues = await phrases_repository.get_issues_by_phrase_id(random_phrase_id)
        assert len(existing_issues) == 1

        await phrases_repository.delete_issues_by_phrase_id(random_phrase_id)
        existing_issues = await phrases_repository.get_issues_by_phrase_id(random_phrase_id)
        assert len(existing_issues) == 0
