from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.monitoring_persistence_schemas import MonitoreoCreate, MonitoreoResponse
from app.services import monitoring_persistence_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=MonitoreoResponse, status_code=status.HTTP_201_CREATED)
def create_monitoreo_session(session: MonitoreoCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_session = monitoring_persistence_crud.create_monitoreo_session(db, session)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Monitoreo",
        entidad_id=new_session.id_monitoreo,
        descripcion=f"Sesión de monitoreo iniciada para servidor ID: {session.id_servidor}",
        tipo_evento_id=5 # Ejecución
    )
    return new_session

@router.get("/{monitoreo_id}", response_model=MonitoreoResponse)
def read_monitoreo_session(monitoreo_id: int, db: Session = Depends(get_pg_db)):
    session = monitoring_persistence_crud.get_monitoreo_session(db, monitoreo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de monitoreo no encontrada")
    return session

@router.put("/{monitoreo_id}/close", response_model=MonitoreoResponse)
def close_monitoreo_session(monitoreo_id: int, db: Session = Depends(get_pg_db)):
    session = monitoring_persistence_crud.close_monitoreo_session(db, monitoreo_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de monitoreo no encontrada")
    return session
