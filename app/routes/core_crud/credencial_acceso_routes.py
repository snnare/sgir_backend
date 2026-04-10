from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import CredencialCreate, CredencialResponse, CredencialUpdate
from app.crud import infrastructure_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=CredencialResponse, status_code=status.HTTP_201_CREATED)
def create_credential(credencial: CredencialCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_cred = infrastructure_crud.create_credencial(db, credencial)
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=new_cred.id_credencial,
        descripcion=f"Credencial creada para usuario: {new_cred.usuario} en servidor ID: {new_cred.id_servidor}",
        tipo_evento_id=2 # Creación
    )
    return new_cred

@router.get("/servidor/{servidor_id}", response_model=List[CredencialResponse])
def read_credentials_by_server(servidor_id: int, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_credenciales_by_servidor(db, servidor_id)

@router.put("/{credencial_id}", response_model=CredencialResponse)
def update_credential(credencial_id: int, credencial_update: CredencialUpdate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    db_cred = infrastructure_crud.update_credencial(db, credencial_id, credencial_update)
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=credencial_id,
        descripcion=f"Credencial actualizada para usuario: {db_cred.usuario}",
        tipo_evento_id=3 # Modificación
    )
    return db_cred

@router.delete("/{credencial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(credencial_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not infrastructure_crud.delete_credencial(db, credencial_id):
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    
    # Auditoría
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="CredencialAcceso",
        entidad_id=credencial_id,
        descripcion=f"Credencial eliminada ID: {credencial_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
