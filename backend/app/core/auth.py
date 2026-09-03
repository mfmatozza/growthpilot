from fastapi import Header, HTTPException

from app.core.config import get_settings


def require_auth(authorization: str | None = Header(default=None)) -> None:
    """Dependency applied to every router except health and auth/login
    (see app/main.py). The token is just SECRET_KEY itself — there's one
    admin account, so a session store/JWT would be complexity with no
    payoff. See docs/DECISIONS.md #16."""
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        raise HTTPException(status_code=500, detail="ADMIN_EMAIL/ADMIN_PASSWORD are not configured on the server")
    if authorization != f"Bearer {settings.secret_key}":
        raise HTTPException(status_code=401, detail="Not authenticated")
