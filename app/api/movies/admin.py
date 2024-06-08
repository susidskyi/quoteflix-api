from sqladmin import ModelView

from app.api.movies.models import MovieModel


class MovieAdmin(ModelView, model=MovieModel):
    category = "Movies"

    column_list = (
        "id",
        "title",
        "year",
        "status",
        "is_active",
    )
    column_searchable_list = (
        "id",
        "title",
        "year",
    )
    column_labels = {
        "title": "Title",
        "year": "Year",
        "status": "Status",
        "is_active": "Active",
    }

    column_sortable_list = (
        "title",
        "year",
        "status",
        "is_active",
    )
