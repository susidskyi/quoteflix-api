from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_superuser: bool
