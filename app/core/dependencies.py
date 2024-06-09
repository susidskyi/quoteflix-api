from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import sessionmanager


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with sessionmanager.session() as session:
        yield session
