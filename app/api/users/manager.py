import uuid
from typing import AsyncIterator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase

from app.api.users.dependencies import get_user_db
from app.api.users.models import UserModel
from app.core.config import settings


class UserManager(UUIDIDMixin, BaseUserManager[UserModel, uuid.UUID]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret

    async def on_after_register(
        self,
        user: UserModel,
        request: Request | None = None,
    ) -> None: ...

    async def on_after_forgot_password(
        self,
        user: UserModel,
        token: str,
        request: Request | None = None,
    ) -> None: ...

    async def on_after_request_verify(
        self,
        user: UserModel,
        token: str,
        request: Request | None = None,
    ) -> None: ...


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[UserModel, uuid.UUID] = Depends(get_user_db),
) -> AsyncIterator[UserManager]:
    yield UserManager(user_db)
