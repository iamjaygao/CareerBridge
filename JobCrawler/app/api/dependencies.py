from typing import Optional

from fastapi import Header, HTTPException

from app.core.config import settings


def verify_api_key(authorization: Optional[str] = Header(default=None)) -> None:
    if not settings.API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    token = authorization.split(" ", 1)[1]
    if token != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
