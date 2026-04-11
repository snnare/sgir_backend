from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt
from app.core.config_core import settings

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Genera un token JWT firmado."""
    to_encode: dict[str, Any] = data.copy()
    if expires_delta:
        expire: datetime = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encode_jwt: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encode_jwt
