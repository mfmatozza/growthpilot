from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        raise HTTPException(status_code=500, detail="ADMIN_EMAIL/ADMIN_PASSWORD are not configured on the server")
    if payload.email != settings.admin_email or payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return LoginResponse(token=settings.secret_key)
