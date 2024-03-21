import uuid

from fastapi_users import FastAPIUsers
from fastapi import APIRouter
from app.api.users.models import UserModel
from app.api.users.schemas import UserSchema, UserCreateSchema, UserUpdateSchema
from app.api.users.manager import get_user_manager
from app.api.users.backend import auth_backend

router = APIRouter()

fastapi_users = FastAPIUsers[UserModel, uuid.UUID](
    get_user_manager,
    [auth_backend],
)


router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)
router.include_router(
    fastapi_users.get_register_router(UserSchema, UserCreateSchema),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserSchema), prefix="/auth", tags=["auth"]
)
router.include_router(
    fastapi_users.get_users_router(UserSchema, UserUpdateSchema),
    prefix="/users",
    tags=["users"],
)
