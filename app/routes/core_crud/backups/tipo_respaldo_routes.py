from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.backup_schemas import TipoRespaldoCreate, TipoRespaldoResponse
from app.services import backup_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=TipoRespaldoResponse, status_code=status.HTTP_201_CREATED)
def create_tipo_respaldo(tipo: TipoRespaldoCreate, db: Session = Depends(get_pg_db)):
    return backup_crud.create_tipo_respaldo(db, tipo)

@router.get("/", response_model=List[TipoRespaldoResponse])
def read_tipos_respaldo(db: Session = Depends(get_pg_db)):
    return backup_crud.get_tipos_respaldo(db)

@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_respaldo(tipo_id: int, db: Session = Depends(get_pg_db)):
    if not backup_crud.delete_tipo_respaldo(db, tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de respaldo no encontrado")
    return None
