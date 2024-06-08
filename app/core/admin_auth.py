from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.jwt import decode_jwt, generate_jwt
from sqladmin.authentication import AuthenticationBackend

from app.api.dependencies import get_db_session
from app.api.users.dependencies import get_user_db
from app.api.users.manager import get_user_manager


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = str(form["username"]), str(form["password"])

        credentials = OAuth2PasswordRequestForm(username=username, password=password)
        user_manager = [item async for item in get_user_manager()][0]
        user_manager.user_db = [item async for item in get_user_db()][0]
        user_manager.user_db.session = [item async for item in get_db_session()][0]
        user = await user_manager.authenticate(credentials)

        await user_manager.user_db.session.close()

        if user is None or not user.is_superuser:
            return False

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "aud": user_manager.verification_token_audience,
        }
        token = generate_jwt(
            token_data,
            user_manager.verification_token_secret,
            user_manager.verification_token_lifetime_seconds,
        )
        # Validate username/password credentials
        # And update session
        request.session.update({"Authorization": "Bearer " + token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token: str = request.session.get("Authorization", "")

        user_manager = [item async for item in get_user_manager()][0]
        user_manager.user_db = [item async for item in get_user_db()][0]
        user_manager.user_db.session = [item async for item in get_db_session()][0]

        try:
            token = token.split("Bearer")[1].strip()

            data = decode_jwt(
                token,
                user_manager.verification_token_secret,
                [user_manager.verification_token_audience],
            )

            user_id = data["sub"]
            email = data["email"]

            user = await user_manager.get_by_email(email)

            parsed_id = user_manager.parse_id(user_id)

            if parsed_id != user.id:
                return False

            if not user.is_superuser:
                return False
        except Exception:
            await user_manager.user_db.session.close()
            return False

        await user_manager.user_db.session.close()

        if not token:
            return False

        return True
