from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config_core import settings
from app.db.postgres.postgres_connection import get_db
from app.services import user_crud
from app.schemas import TokenData
from app.models.user_models import User
from app.core.exceptions import AuthenticationException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = AuthenticationException(
        detail="No se pudo validar las credenciales"
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = user_crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
