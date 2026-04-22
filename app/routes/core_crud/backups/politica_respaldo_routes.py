from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import PoliticaRespaldoCreate, PoliticaRespaldoResponse, PoliticaRespaldoUpdate
from app.services import backup_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=PoliticaRespaldoResponse, status_code=status.HTTP_201_CREATED)
def create_politica(politica: PoliticaRespaldoCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_pol = backup_crud.create_politica_respaldo(db, politica)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="PoliticaRespaldo",
        entidad_id=new_pol.id_politica,
        descripcion=f"Política de respaldo creada: {new_pol.nombre_politica}",
        tipo_evento_id=2 # Creación
    )
    return new_pol

@router.get("/", response_model=List[PoliticaRespaldoResponse])
def read_politicas(db: Session = Depends(get_pg_db)):
    return backup_crud.get_politicas_respaldo(db)

@router.put("/{politica_id}", response_model=PoliticaRespaldoResponse)
def update_politica(politica_id: int, politica_update: PoliticaRespaldoUpdate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    db_pol = backup_crud.update_politica_respaldo(db, politica_id, politica_update)
    if not db_pol:
        raise HTTPException(status_code=404, detail="Política no encontrada")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="PoliticaRespaldo",
        entidad_id=politica_id,
        descripcion=f"Política de respaldo actualizada: {db_pol.nombre_politica}",
        tipo_evento_id=3 # Modificación
    )
    return db_pol

@router.delete("/{politica_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_politica(politica_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not backup_crud.delete_politica_respaldo(db, politica_id):
        raise HTTPException(status_code=404, detail="Política no encontrada")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="PoliticaRespaldo",
        entidad_id=politica_id,
        descripcion=f"Política de respaldo eliminada ID: {politica_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
