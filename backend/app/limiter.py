"""Shared rate-limiter instance.

Defined here (not in main.py) so routers can import it without circular imports.
The limiter is registered on app.state and the SlowAPIMiddleware in main.py.
"""

from fastapi import Request
from slowapi import Limiter

from app.config import settings


def _get_user_or_ip(request: Request) -> str:
    """Rate-limit key: user_id from JWT, or client IP for unauthenticated requests.

    Must be synchronous — slowapi calls this in a sync context.
    JWT is decoded without a DB call (python-jose is synchronous).
    """
    auth: str | None = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth[len("Bearer "):]
        try:
            from jose import jwt

            payload = jwt.decode(
                token,
                settings.jwt_secret.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
            sub = payload.get("sub")
            if sub:
                return str(sub)
        except Exception:
            pass
    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=_get_user_or_ip,
    storage_uri=settings.redis_url,
    default_limits=["100/minute"],
)
