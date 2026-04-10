from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import base64
from jose import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config_core import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    salt: bytes = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def _get_fernet() -> Fernet:
    """ Genera una instancia de Fernet basada en el SECRET KEY"""
    kdf: PBKDF2HMAC = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"sgir_fixed_salt",
        iterations=1000000,
    )
    key: bytes = base64.urlsafe_b64decode(
        kdf.derive(settings.SECRET_KEY.encode())
    )
    return Fernet(key)


def encrypt_password(password: str) -> str:
    """Encripta la password, puede ser recuperable por el sistema"""
    f: Fernet = _get_fernet()
    return f.encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    """Desencripta la password para el uso en conexiones"""
    f: Fernet = _get_fernet()
    return f.decrypt(token.encode()).decode()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = dict[str, Any] = data.copy()
    if expires_delta:
        expire: datetime = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(
            timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encode_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encode_jwt
