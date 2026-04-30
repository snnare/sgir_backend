from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import ServidorParticionCreate, ServidorParticionResponse
from app.services import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ServidorParticionResponse, status_code=status.HTTP_201_CREATED)
def create_particion(particion: ServidorParticionCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    # Validar que el servidor exista
    if not infrastructure_crud.get_servidor(db, particion.id_servidor):
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
        
    new_particion = infrastructure_crud.create_particion(db, particion)
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="ServidorParticion",
        entidad_id=new_particion.id_particion,
        descripcion=f"Partición {new_particion.etiqueta} ({new_particion.path}) agregada al servidor ID: {new_particion.id_servidor}",
        tipo_evento_id=2 # Creación
    )
    return new_particion

@router.get("/servidor/{servidor_id}", response_model=List[ServidorParticionResponse])
def read_particiones_by_servidor(servidor_id: int, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_particiones_by_servidor(db, servidor_id)

@router.delete("/{id_particion}", status_code=status.HTTP_204_NO_CONTENT)
def delete_particion(id_particion: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not infrastructure_crud.delete_particion(db, id_particion):
        raise HTTPException(status_code=404, detail="Partición no encontrada")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="ServidorParticion",
        entidad_id=id_particion,
        descripcion=f"Partición eliminada ID: {id_particion}",
        tipo_evento_id=4 # Eliminación
    )
    return None
