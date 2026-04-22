from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.audit_schemas import TipoEventoCreate, TipoEventoResponse
from app.services import audit_crud

from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=TipoEventoResponse, status_code=status.HTTP_201_CREATED)
def create_tipo_evento(tipo_evento: TipoEventoCreate, db: Session = Depends(get_pg_db)):
    return audit_crud.create_tipo_evento(db=db, tipo_evento=tipo_evento)

@router.get("/", response_model=List[TipoEventoResponse])
def read_tipo_eventos(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return audit_crud.get_tipo_eventos(db, skip=skip, limit=limit)

@router.get("/{tipo_id}", response_model=TipoEventoResponse)
def read_tipo_evento(tipo_id: int, db: Session = Depends(get_pg_db)):
    db_tipo = audit_crud.get_tipo_evento_by_id(db, id_tipo_evento=tipo_id)
    if db_tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    return db_tipo

@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_evento(tipo_id: int, db: Session = Depends(get_pg_db)):
    success = audit_crud.delete_tipo_evento(db, id_tipo_evento=tipo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")
    return None
