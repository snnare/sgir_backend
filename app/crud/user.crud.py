from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    db_user: User = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        nombres=user.nombres,
        apellidos=user.apellidos,
        id_rol=user.id_rol,
        id_estado_usuario=user.id_estado_usuario
    )

    db.add(instance=db_user)
    db.commit()
    db.refresh(instance=db_user)
    return db_user


