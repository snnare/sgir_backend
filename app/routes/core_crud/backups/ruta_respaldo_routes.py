from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import RutaRespaldoCreate, RutaRespaldoResponse, RutaRespaldoUpdate
from app.services import backup_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=RutaRespaldoResponse, status_code=status.HTTP_201_CREATED)
def create_ruta(ruta: RutaRespaldoCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_ruta = backup_crud.create_ruta_respaldo(db, ruta)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="RutaRespaldo",
        entidad_id=new_ruta.id_ruta,
        descripcion=f"Ruta de respaldo creada: {new_ruta.path}",
        tipo_evento_id=2 # Creación
    )
    return new_ruta

@router.get("/", response_model=List[RutaRespaldoResponse])
def read_rutas(db: Session = Depends(get_pg_db)):
    return backup_crud.get_rutas_respaldo(db)

@router.put("/{ruta_id}", response_model=RutaRespaldoResponse)
def update_ruta(ruta_id: int, ruta_update: RutaRespaldoUpdate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    db_ruta = backup_crud.update_ruta_respaldo(db, ruta_id, ruta_update)
    if not db_ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="RutaRespaldo",
        entidad_id=ruta_id,
        descripcion=f"Ruta de respaldo actualizada: {db_ruta.path}",
        tipo_evento_id=3 # Modificación
    )
    return db_ruta

@router.delete("/{ruta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ruta(ruta_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not backup_crud.delete_ruta_respaldo(db, ruta_id):
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="RutaRespaldo",
        entidad_id=ruta_id,
        descripcion=f"Ruta de respaldo eliminada ID: {ruta_id}",
        tipo_evento_id=4 # Eliminación
    )
    return None
