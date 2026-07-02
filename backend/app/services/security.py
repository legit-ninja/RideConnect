from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, email: str, is_admin: bool) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str | bool]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise JWTError("Missing subject")
        return {
            "sub": sub,
            "email": str(payload.get("email", "")),
            "is_admin": bool(payload.get("is_admin", False)),
        }
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
