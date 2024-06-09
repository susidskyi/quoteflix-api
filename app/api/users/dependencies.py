import uuid
from typing import AsyncIterator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.models import UserModel
from app.core.dependencies import get_db_session


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncIterator[SQLAlchemyUserDatabase[UserModel, uuid.UUID]]:
    yield SQLAlchemyUserDatabase(session, UserModel)
