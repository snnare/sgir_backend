from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import AlertaCreate, AlertaResponse
from app.services import monitoring_persistence_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=AlertaResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alerta: AlertaCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_alert = monitoring_persistence_crud.create_alert(db, alerta)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Alerta",
        entidad_id=new_alert.id_alerta,
        descripcion=f"Alerta generada para servidor ID: {alerta.id_servidor}: {alerta.descripcion}",
        tipo_evento_id=5 # Ejecución/Alerta
    )
    return new_alert

@router.get("/servidor/{servidor_id}", response_model=List[AlertaResponse])
def read_alerts_by_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.get_alerts_by_server(db, servidor_id)
