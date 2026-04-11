from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import InstanciaCreate, Instancia as InstanciaResponse
from app.services import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=InstanciaResponse, status_code=status.HTTP_201_CREATED)
def create_instancia(instancia: InstanciaCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_inst = infrastructure_crud.create_instancia(db, instancia)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="InstanciaDBMS",
        entidad_id=new_inst.id_instancia,
        descripcion=f"Instancia creada: {new_inst.nombre_instancia} en puerto {new_inst.puerto}",
        tipo_evento_id=2 # Creación
    )
    return new_inst

@router.get("/servidor/{servidor_id}", response_model=List[InstanciaResponse])
def read_instancias_by_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_instancias_by_servidor(db, servidor_id)
