# The builder image, used to build the virtual environment
FROM python:3.12 as builder

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry==${POETRY_VERSION}

WORKDIR /code

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}


# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12 as runtime

ENV VIRTUAL_ENV=/code/.venv \
    PATH="/code/.venv/bin:$PATH" \
    PYTHONPATH=/code

WORKDIR /code

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
