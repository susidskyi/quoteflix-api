from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.core.models import BaseModel
from fastapi_users.db import SQLAlchemyBaseUserTableUUID


class User(SQLAlchemyBaseUserTableUUID, BaseModel):
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
