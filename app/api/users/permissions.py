from app.api.users.router import fastapi_users

curret_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(
    active=True,
    verified=True,
    superuser=True,
)
