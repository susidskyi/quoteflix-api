from fastapi_users.authentication import (
    AuthenticationBackend as BaseAuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from app.core.config import settings


class AuthenticationBackend(BaseAuthenticationBackend):
    pass


bearer_transport = BearerTransport(tokenUrl="auth/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
