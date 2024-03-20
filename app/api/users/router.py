from fastapi import APIRouter, Depends
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.api.dependencies import get_db_session
from app.api.users.schemas import UserRead

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Sequence[UserRead])
async def user_details(
    db: AsyncSession = Depends(get_db_session),
) -> Sequence[UserRead]:
    users = await db.execute(text("SELECT * FROM users"))

    return [UserRead(**user.dict()) for user in users]
