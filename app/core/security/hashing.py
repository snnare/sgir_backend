import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano con su hash de Bcrypt."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Genera un hash de Bcrypt a partir de una contraseña."""
    salt: bytes = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
