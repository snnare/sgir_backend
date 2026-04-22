from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import BaseDatosCreate, BaseDatos as BaseDatosResponse
from app.services import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=BaseDatosResponse, status_code=status.HTTP_201_CREATED)
def create_base_datos(base_datos: BaseDatosCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_bd = infrastructure_crud.create_base_datos(db, base_datos)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="BaseDeDatos",
        entidad_id=new_bd.id_base_datos,
        descripcion=f"Base de datos registrada: {new_bd.nombre_base}",
        tipo_evento_id=2 # Creación
    )
    return new_bd
