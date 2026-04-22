from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import StatusCreate, StatusResponse
from app.services import status_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=StatusResponse, status_code=status.HTTP_201_CREATED)
def create_status(status: StatusCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_status = status_crud.create_status(db, status)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Estado_General",
        entidad_id=new_status.id_estado,
        descripcion=f"Nuevo estado registrado: {new_status.nombre_estado}",
        tipo_evento_id=2 # Creación
    )
    return new_status

@router.get("/", response_model=List[StatusResponse])
def read_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return status_crud.get_statuses(db, skip=skip, limit=limit)

@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_status(status_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not status_crud.delete_status(db, status_id):
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Estado_General",
        entidad_id=status_id,
        descripcion=f"Estado eliminado ID: {status_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
