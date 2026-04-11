from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.audit_schemas import BitacoraResponse
from app.services import audit_crud

from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/", response_model=List[BitacoraResponse])
def read_bitacoras(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    """Obtiene la lista de eventos en la bitácora."""
    return audit_crud.get_bitacoras(db, skip=skip, limit=limit)

@router.get("/{bitacora_id}", response_model=BitacoraResponse)
def read_bitacora(bitacora_id: int, db: Session = Depends(get_pg_db)):
    """Obtiene un evento específico de la bitácora por ID."""
    db_bitacora = audit_crud.get_bitacora_by_id(db, bitacora_id=bitacora_id)
    if db_bitacora is None:
        raise HTTPException(status_code=404, detail="Evento de bitácora no encontrado")
    return db_bitacora
