from sqlalchemy.orm import Session
from app.models.user_models import User
from app.schemas.user_schemas import UserCreate
from app.core.security_core import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id_usuario == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


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

def update_user(db: Session, user_id: int, user_update: UserCreate) -> User | None:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_by_email(db: Session, email: str, user_update: UserCreate) -> User | None:
    db_user = get_user_by_email(db, email)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


def delete_user_by_email(db: Session, email: str) -> bool:
    db_user = get_user_by_email(db, email)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True
