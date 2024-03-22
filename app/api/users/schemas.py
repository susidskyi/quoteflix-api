import uuid

from fastapi_users import schemas


class UserSchema(schemas.BaseUser[uuid.UUID]):
    first_name: str
    last_name: str


class UserCreateSchema(schemas.BaseUserCreate):
    first_name: str
    last_name: str


class UserUpdateSchema(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
