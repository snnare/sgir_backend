from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import RespaldoCreate, RespaldoResponse
from app.services import backup_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=RespaldoResponse, status_code=status.HTTP_201_CREATED)
def registrar_ejecucion_respaldo(respaldo: RespaldoCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_respaldo = backup_crud.create_registro_respaldo(db, respaldo)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Respaldo",
        entidad_id=new_respaldo.id_respaldo,
        descripcion=f"Ejecución de respaldo registrada para BD ID: {respaldo.id_base_datos}. Estado: {respaldo.id_estado_ejecucion}",
        tipo_evento_id=5 # Ejecución
    )
    return new_respaldo

@router.get("/historial", response_model=List[RespaldoResponse])
def read_historial_respaldos(id_base_datos: Optional[int] = None, db: Session = Depends(get_pg_db)):
    return backup_crud.get_historial_respaldos(db, id_base_datos)
