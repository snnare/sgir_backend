from sqlalchemy.orm import Session
from app.models.user_models import UserStatus
from app.schemas.estado_general_schemas import StatusCreate

def create_status(db: Session, status: StatusCreate):
    db_status = UserStatus(**status.model_dump())
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def get_statuses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserStatus).offset(skip).limit(limit).all()

def get_status_by_id(db: Session, status_id: int):
    return db.query(UserStatus).filter(UserStatus.id_estado == status_id).first()

def delete_status(db: Session, status_id: int):
    db_status = db.query(UserStatus).filter(UserStatus.id_estado == status_id).first()
    if db_status:
        db.delete(db_status)
        db.commit()
        return True
    return False
