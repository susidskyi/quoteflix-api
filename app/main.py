import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.movies.router import router as movies_router
from app.api.phrases.router import router as phrases_router
from app.api.users.router import router as users_router
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
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


docs_url = "/docs" if settings.environment != "production" else None
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]


app = FastAPI(lifespan=lifespan, docs_url=docs_url)

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
