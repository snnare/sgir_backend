from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import ServidorCreate, ServidorResponse, ServidorUpdate
from app.crud import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ServidorResponse, status_code=status.HTTP_201_CREATED)
def create_server(servidor: ServidorCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_server = infrastructure_crud.create_servidor(db, servidor)
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Servidor",
        entidad_id=new_server.id_servidor,
        descripcion=f"Servidor creado: {new_server.nombre_servidor} ({new_server.direccion_ip})",
        tipo_evento_id=2 # Creación
    )
    return new_server

@router.get("/", response_model=List[ServidorResponse])
def read_servers(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_servidores(db, skip, limit)

@router.get("/{servidor_id}", response_model=ServidorResponse)
def read_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    db_server = infrastructure_crud.get_servidor(db, servidor_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    return db_server

@router.put("/{servidor_id}", response_model=ServidorResponse)
def update_server(servidor_id: int, servidor_update: ServidorUpdate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    db_server = infrastructure_crud.update_servidor(db, servidor_id, servidor_update)
    if not db_server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Servidor",
        entidad_id=servidor_id,
        descripcion=f"Servidor actualizado: {db_server.nombre_servidor}",
        tipo_evento_id=3 # Modificación
    )
    return db_server

@router.delete("/{servidor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(servidor_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not infrastructure_crud.delete_servidor(db, servidor_id):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Servidor",
        entidad_id=servidor_id,
        descripcion=f"Servidor eliminado ID: {servidor_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
