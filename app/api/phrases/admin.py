from sqladmin import ModelView

from app.api.phrases.models import PhraseIssueModel, PhraseModel
from app.api.phrases.utils import format_duration


class PhraseAdmin(ModelView, model=PhraseModel):
    category = "Phrases"

    column_list = (
        "id",
        "movie.title",
        "full_text",
        "start_in_movie",
        "end_in_movie",
        "is_active",
    )
    column_labels = {
        "movie.title": "Movie",
        "start_in_movie": "Start",
        "end_in_movie": "End",
        "full_text": "Text",
        "is_active": "Active",
    }
    column_searchable_list = (
        "id",
        "movie.title",
        "full_text",
    )
    column_sortable_list = (
        "movie.title",
        "start_in_movie",
        "is_active",
    )
    column_formatters = {
        "start_in_movie": lambda m, _: format_duration(m.start_in_movie),  # type: ignore
        "end_in_movie": lambda m, _: format_duration(m.start_in_movie),  # type: ignore
    }


class PhraseIssueAdmin(ModelView, model=PhraseIssueModel):
    category = "Phrases"

    column_list = (
        "id",
        "phrase.movie.title",
        "phrase.full_text",
        "phrase.start_in_movie",
        "issuer_ip",
        "is_active",
    )
    column_labels = {
        "movie.title": "Movie",
        "phrase.start_in_movie": "Start",
        "phrase.full_text": "Text",
        "issuer_ip": "IP",
    }
    column_searchable_list = (
        "id",
        "issuer_ip",
        "phrase.movie.title",
    )
    column_sortable_list = (
        "phrase.movie.title",
        "issuer_ip",
        "is_active",
    )
    column_formatters = {
        "phrase.start_in_movie": lambda m, _: format_duration(m.phrase.start_in_movie),  # type: ignore
    }
