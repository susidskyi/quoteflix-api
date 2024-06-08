import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_pagination import add_pagination
from redis import asyncio as aioredis
from sqladmin import Admin

from app.api.analytics.router import router as analytics_router
from app.api.movies import admin as movies_admin
from app.api.movies.router import router as movies_router
from app.api.phrases import admin as phrases_admin
from app.api.phrases.router import router as phrases_router
from app.api.users.router import router as users_router
from app.core.admin_auth import AdminAuth
from app.core.config import settings
from app.core.database import sessionmanager

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.debug_logs else logging.INFO,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """
    Function that handles startup and shutdown events.
    """
    redis = aioredis.from_url(str(settings.redis_api_cache_url))
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


docs_url = "/docs" if settings.environment != "prod" else None
origins = ["http://localhost", "http://localhost:8080", "http://localhost:3000", "https://phraseqwe.space"]


app = FastAPI(lifespan=lifespan, docs_url=docs_url)

authentication_backend = AdminAuth(secret_key=settings.secret)

# Admin
admin = Admin(
    app,
    engine=sessionmanager._engine,
    base_url=settings.admin_panel_path,
    authentication_backend=authentication_backend,
)
admin.add_view(phrases_admin.PhraseAdmin)
admin.add_view(phrases_admin.PhraseIssueAdmin)
admin.add_view(movies_admin.MovieAdmin)

# Paginator
add_pagination(app)

# Logfire configuration
logfire.configure(token=settings.logfire_token, send_to_logfire=settings.environment in ["dev", "prod"])
logfire.instrument_fastapi(app)

# CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(users_router, prefix="/api")
app.include_router(movies_router, prefix="/api")
app.include_router(phrases_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
