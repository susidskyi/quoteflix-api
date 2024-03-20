import logging
import sys
from contextlib import asynccontextmanager
from app.api.users.router import router as users_router
from app.core.config import settings
from app.core.database import sessionmanager
from fastapi import FastAPI


logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG if settings.debug_logs else logging.INFO
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


docs_url = "/docs" if settings.stage != "production" else None
app = FastAPI(lifespan=lifespan, docs_url=docs_url)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Routers
app.include_router(users_router)
