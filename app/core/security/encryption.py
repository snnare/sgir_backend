import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config_core import settings

def _get_fernet() -> Fernet:
    """Genera una instancia de Fernet basada en la SECRET_KEY."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"sgir_fixed_salt",
        iterations=1000000,
    )
    key_bytes = kdf.derive(settings.SECRET_KEY.encode())
    key_base64 = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key_base64)

def encrypt_password(password: str) -> str:
    """Encripta la contraseña para almacenamiento reversible."""
    f = _get_fernet()
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    """Desencripta la contraseña para el uso en conexiones remotas."""
    f = _get_fernet()
    return f.decrypt(token.encode()).decode()
