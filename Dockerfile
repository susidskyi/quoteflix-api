FROM python:3.12-slim-bookworm as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Poetry
RUN apt update && apt install curl ffmpeg --no-install-recommends -y && curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/apt /var/lib/dpkg && \
    rm -rf /var/lib/apt/lists/*

COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY ./scripts/prestart.sh /prestart.sh

FROM builder as runtime

WORKDIR /app/

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG ENVIRONMENT='production'
RUN bash -c " \
    if [ $ENVIRONMENT == 'production' ] || [ $ENVIRONMENT == 'dev' ]; then \
        poetry install --only main; \
    elif [ ${ENVIRONMENT} == 'test' ]; then \
        poetry install --only main, test; \
    else \
        poetry install; \
    fi \
"

COPY ./app /app/app

ENV PYTHONPATH=/app

COPY ./scripts/ /app/

COPY ./alembic.ini /app/
